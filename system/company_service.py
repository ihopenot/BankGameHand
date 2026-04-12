from __future__ import annotations

from typing import Dict, List

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.types import Loan, LoanType, RepaymentType
from entity.company.company import Company
from entity.goods import GoodsType
from system.market_service import BuyIntent, MarketService, SellOrder, TradeRecord


class CompanyService:
    companies: Dict[str, Company]

    def sell_phase(self, market: MarketService) -> None:
        """遍历所有公司，将库存中的每个 GoodsBatch 作为 SellOrder 挂到市场。"""
        for company in self.companies.values():
            storage = company.get_component(StorageComponent)
            pc = company.get_component(ProductorComponent)
            if storage is None or pc is None:
                continue
            for goods_type, batches in storage.inventory.items():
                price = pc.prices.get(goods_type, goods_type.base_price)
                for batch in batches:
                    if batch.quantity <= 0:
                        continue
                    order = SellOrder(seller=company, batch=batch, price=price)
                    market.add_sell_order(order)

    def buy_phase(self, market: MarketService) -> List[BuyIntent]:
        """遍历所有公司，计算原料需求并生成 BuyIntent 列表。"""
        intents: List[BuyIntent] = []
        for company in self.companies.values():
            pc = company.get_component(ProductorComponent)
            storage = company.get_component(StorageComponent)
            if pc is None or storage is None:
                continue

            # 汇总各原料的总需求
            demand_map: Dict[GoodsType, int] = {}
            for ft, factories in pc.factories.items():
                recipe = ft.recipe
                if recipe.input_goods_type is None:
                    continue
                built_count = sum(1 for f in factories if f.is_built)
                if built_count == 0:
                    continue
                raw_demand = recipe.input_quantity * ft.base_production * built_count
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
                    sort_key=lambda o: o.batch.quality / o.price if o.price > 0 else float("inf"),
                )
                intents.append(intent)

        return intents

    def settle_trades(self, trades: List[TradeRecord]) -> None:
        """处理成交记录：商品转移 + 现金支付/赊账。"""
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
