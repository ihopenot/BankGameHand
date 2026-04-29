from __future__ import annotations

from typing import Dict, List

from component.base_company_decision import get_decision_component_class
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.config import ConfigManager
from core.types import Loan, LoanType, RepaymentType
from entity.company.company import Company
from entity.factory import Factory, FactoryType
from entity.goods import GoodsType
from system.market_service import BuyIntent, MarketService, SellOrder, TradeRecord


class CompanyService:


    def __init__(self) -> None:
        self.companies: Dict[str, Company] = {}

        config = ConfigManager()
        bankruptcy_cfg = config.section("game").bankruptcy
        self._liquidation_factory_rate: float = bankruptcy_cfg.liquidation_factory_rate
        self._min_producers: int = bankruptcy_cfg.min_producers_per_goods
        self._new_company_cash: int = bankruptcy_cfg.new_company_initial_cash
        self._replenish_decision_component: str = bankruptcy_cfg.replenish_decision_component
        self._replenish_initial_wage: int = bankruptcy_cfg.replenish_initial_wage

    def create_company(
        self,
        name: str,
        factory_type: FactoryType,
        initial_cash: int,
        decision_component: str,
        initial_wage: int,
    ) -> Company:
        """创建一家拥有指定工厂类型和初始资金的公司。"""
        company = Company(name=name)
        company.initial_wage = initial_wage
        company.wage = initial_wage
        ledger = company.get_component(LedgerComponent)
        ledger.cash = initial_cash
        pc = company.get_component(ProductorComponent)
        factory = Factory(factory_type, build_remaining=0)
        pc.factories[factory_type].append(factory)
        pc.init_prices()
        decision_cls = get_decision_component_class(decision_component)
        company.init_component(decision_cls)
        self.companies[name] = company
        return company

    def sell_phase(self, market: MarketService) -> None:
        """遍历所有公司，将库存中的每个 GoodsBatch 作为 SellOrder 挂到市场。"""
        for company in self.companies.values():
            storage = company.get_component(StorageComponent)
            pc = company.get_component(ProductorComponent)
            mc = company.get_component(MetricComponent)
            if storage is None or pc is None:
                continue
            for goods_type, batches in storage.inventory.items():
                price = pc.prices.get(goods_type, goods_type.base_price)
                for batch in batches:
                    if batch.quantity <= 0:
                        continue
                    order = SellOrder(seller=company, batch=batch, price=price)
                    market.add_sell_order(order)
                    if mc is not None:
                        mc.last_sell_orders[goods_type] = (
                            mc.last_sell_orders.get(goods_type, 0) + batch.quantity
                        )

    def buy_phase(self, market: MarketService, decision_service=None) -> List[BuyIntent]:
        """遍历所有公司，计算原料需求并生成 BuyIntent 列表。"""
        intents: List[BuyIntent] = []
        for company in self.companies.values():
            pc = company.get_component(ProductorComponent)
            storage = company.get_component(StorageComponent)
            if pc is None or storage is None:
                continue

            # 决策四：采购偏好排序
            if decision_service is not None:
                sort_fn = decision_service.make_purchase_sort_key(company)
            else:
                sort_fn = lambda o: o.batch.quality

            # 汇总各原料的总需求
            demand_map: Dict[GoodsType, int] = {}
            for ft, factories in pc.factories.items():
                recipe = ft.recipe
                if recipe.input_goods_type is None:
                    continue
                built_count = sum(1 for f in factories if f.is_built)
                if built_count == 0:
                    continue
                raw_demand = recipe.input_quantity * built_count
                gt = recipe.input_goods_type
                demand_map[gt] = demand_map.get(gt, 0) + raw_demand

            # 扣减现有库存
            for gt, raw_demand in demand_map.items():
                stock = sum(b.quantity for b in storage.get_batches(gt))
                net_demand = max(0, raw_demand - stock)
                if net_demand <= 0:
                    continue

                intent = BuyIntent(
                    buyer=company,
                    goods_type=gt,
                    quantity=net_demand,
                    sort_key=sort_fn,
                )
                intents.append(intent)

        return intents

    def settle_trades(self, trades: List[TradeRecord]) -> None:
        """处理成交记录：商品转移 + 现金支付/赊账 + 更新购买均价。"""
        for trade in trades:
            seller = trade.seller
            buyer = trade.buyer

            # 1. 商品转移：卖方扣减 → 买方入库
            seller_storage = seller.get_component(StorageComponent)
            buyer_storage = buyer.get_component(StorageComponent)
            transferred = seller_storage.require_goods(trade.goods_type, trade.quantity, base=0)
            if transferred.quantity > 0:
                buyer_storage.add_batch(transferred)
            else:
                continue

            # 2. 支付结算（按实际交付量计费）
            total_cost = transferred.quantity * trade.price
            buyer_ledger = buyer.get_component(LedgerComponent)
            seller_ledger = seller.get_component(LedgerComponent)

            if buyer_ledger.cash >= total_cost:
                # 全额现金支付
                buyer_ledger.cash -= total_cost
                seller_ledger.cash += total_cost
            else:
                # 部分现金 + 赊账
                cash_paid = buyer_ledger.cash
                buyer_ledger.cash = 0
                seller_ledger.cash += cash_paid
                shortfall = total_cost - cash_paid
                # 创建 TRADE_PAYABLE Loan
                loan = Loan(
                    creditor=seller,
                    debtor=buyer,
                    principal=shortfall,
                    rate=0,
                    term=1,
                    loan_type=LoanType.TRADE_PAYABLE,
                    repayment_type=RepaymentType.BULLET,
                )
                seller_ledger.receivables.append(loan)
                buyer_ledger.payables.append(loan)

            # 3. 更新卖方指标
            seller_mc = seller.get_component(MetricComponent)
            if seller_mc is not None:
                seller_mc.last_sold_quantities[trade.goods_type] = (
                    seller_mc.last_sold_quantities.get(trade.goods_type, 0) + transferred.quantity
                )
                seller_mc.last_revenue += total_cost

        self._update_avg_buy_prices(trades)

    @staticmethod
    def _update_avg_buy_prices(trades: List[TradeRecord]) -> None:
        """按成交量加权更新每个买方的 MetricComponent.last_avg_buy_prices。"""
        from collections import defaultdict
        buyer_totals: dict = defaultdict(list)
        for trade in trades:
            mc = trade.buyer.get_component(MetricComponent)
            if mc is not None:
                buyer_totals[(trade.buyer, trade.goods_type)].append(trade)

        for (buyer, goods_type), buyer_trades in buyer_totals.items():
            total_qty = sum(t.quantity for t in buyer_trades)
            if total_qty > 0:
                mc = buyer.get_component(MetricComponent)
                weighted_price = sum(t.price * t.quantity for t in buyer_trades)
                mc.last_avg_buy_prices[goods_type] = weighted_price / total_qty

    # ── 破产清算 ──

    def process_bankruptcies(self) -> None:
        """遍历所有破产标记的 LedgerComponent，依次执行清算。"""
        bankrupt_components: List[LedgerComponent] = [
            lc for lc in LedgerComponent.components if lc.is_bankrupt
        ]

        for ledger in bankrupt_components:
            self._liquidate(ledger)

        # 移除已销毁的公司
        destroyed = [
            name for name, c in self.companies.items()
            if c.get_component(LedgerComponent) is None
        ]
        for name in destroyed:
            del self.companies[name]

    def _liquidate(self, ledger: LedgerComponent) -> None:
        """对单家破产公司执行清算。"""
        entity = ledger.outer

        # 1. 计算清算所得 = 工厂造价 × 50% + 现有现金
        proceeds = ledger.cash
        pc: ProductorComponent | None = entity.get_component(ProductorComponent)
        if pc is not None:
            for ft, factories in pc.factories.items():
                for factory in factories:
                    proceeds += ft.build_cost // 2

        # 2. 库存直接清空（不计入清算所得）
        storage: StorageComponent | None = entity.get_component(StorageComponent)
        if storage is not None:
            storage.inventory.clear()

        # 3. 按优先级偿还债务
        remaining_proceeds = proceeds
        payables_by_priority = sorted(
            list(ledger.payables),
            key=lambda loan: loan.loan_type.priority,
        )

        for loan in payables_by_priority:
            if remaining_proceeds <= 0:
                break
            creditor_ledger: LedgerComponent = loan.creditor.get_component(LedgerComponent)
            repay_amount = min(loan.remaining, remaining_proceeds)
            creditor_ledger.cash += repay_amount
            remaining_proceeds -= repay_amount

        # 4. 核销破产公司的债务（payables）
        for loan in list(ledger.payables):
            creditor_ledger: LedgerComponent = loan.creditor.get_component(LedgerComponent)
            creditor_ledger.write_off(loan)

        # 5. 核销破产公司的应收款（receivables）— 债务人不再需要偿还
        for loan in list(ledger.receivables):
            debtor_ledger: LedgerComponent = loan.debtor.get_component(LedgerComponent)
            debtor_ledger.write_off(loan)

        # 6. 销毁公司实体
        entity.destroy()

    # ── 市场补充 ──

    def replenish_market(self) -> None:
        """检查每种商品的存活生产者数量，低于阈值时创建新公司。"""
        # 统计每种 GoodsType 的存活生产者数量和对应 FactoryType
        producer_count: Dict[GoodsType, int] = {}
        goods_to_factory_type: Dict[GoodsType, FactoryType] = {}

        for pc in ProductorComponent.components:
            for ft, factories in pc.factories.items():
                gt = ft.recipe.output_goods_type
                built = sum(1 for f in factories if f.is_built)
                if built > 0:
                    producer_count[gt] = producer_count.get(gt, 0) + 1
                    goods_to_factory_type[gt] = ft

        # 补充所有已知的 FactoryType（可能已无存活生产者）
        for ft in FactoryType.factory_types.values():
            gt = ft.recipe.output_goods_type
            if gt not in producer_count:
                producer_count[gt] = 0
            if gt not in goods_to_factory_type:
                goods_to_factory_type[gt] = ft

        # 为不足阈值的商品创建新公司
        company_idx = len(self.companies)
        for gt, count in producer_count.items():
            while count < self._min_producers:
                ft = goods_to_factory_type[gt]
                name = f"gov_company_{company_idx}"
                self.create_company(
                    name=name,
                    factory_type=ft,
                    initial_cash=self._new_company_cash,
                    decision_component=self._replenish_decision_component,
                    initial_wage=self._replenish_initial_wage,
                )
                company_idx += 1
                count += 1
