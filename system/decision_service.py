from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING, Callable, List, Optional

from core.types import LoanApplication

from component.decision_component import DecisionComponent
from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from core.config import ConfigManager
from entity.factory import Factory, FactoryType
from entity.goods import GoodsType

if TYPE_CHECKING:
    from entity.company.company import Company
    from system.market_service import SellOrder


class DecisionService:
    """企业决策服务：编排 CEO 特质驱动的决策。"""

    def __init__(self) -> None:
        self.config = ConfigManager().section("decision")

    # ── 编排接口（供 Game 调用） ──

    def plan_phase(self, companies: List[Company]) -> None:
        """决策阶段：调整定价，生成投资计划表（不实际花钱）。"""
        for company in companies:
            dc = company.get_component(DecisionComponent)
            self.decide_pricing(company)
            dc.investment_plan = {
                "expansion": self._plan_expansion(company),
                "brand": self._plan_brand(company),
                "tech": self._plan_tech(company),
            }

    def act_phase(self, companies: List[Company]) -> None:
        """执行阶段：按计划表分配投资资金，未花完的回流。"""
        for company in companies:
            dc = company.get_component(DecisionComponent)
            pc = company.get_component(ProductorComponent)
            ledger = company.get_component(LedgerComponent)
            plan = dc.investment_plan
            plan_total = sum(plan.values())
            if plan_total == 0:
                continue

            reserved = self._calc_reserved_cash(company)
            budget = max(0, ledger.cash - reserved)

            if budget >= plan_total:
                alloc = dict(plan)
            else:
                alloc = {k: int(budget * v / plan_total) for k, v in plan.items()}

            actual_spent = 0

            # 扩产：必须够建一个厂才花钱，否则回流
            expansion_budget = alloc.get("expansion", 0)
            ft = self._pick_factory_type(company)
            if ft is not None and expansion_budget >= ft.build_cost:
                factory = Factory(ft, build_remaining=ft.build_time)
                pc.factories[ft].append(factory)
                actual_spent += ft.build_cost

            # 品牌投入
            brand_budget = alloc.get("brand", 0)
            if brand_budget > 0:
                self._apply_brand(company, brand_budget)
                actual_spent += brand_budget

            # 科技投入
            tech_budget = alloc.get("tech", 0)
            if tech_budget > 0:
                self._apply_tech(company, tech_budget)
                actual_spent += tech_budget

            ledger.cash -= actual_spent
            pc.update_max_tech()

    # ── 决策一：产品定价 ──

    def decide_pricing(self, company: Company) -> None:
        """根据上轮销售情况调整标价。"""
        dc = company.get_component(DecisionComponent)
        pc = company.get_component(ProductorComponent)
        cfg = self.config.pricing

        for gt, old_price in list(pc.prices.items()):
            listed = dc.last_sell_orders.get(gt, 0)
            sold = dc.last_sold_quantities.get(gt, 0)

            if listed == 0:
                continue

            if sold >= listed:
                raise_rate = cfg.base_raise_rate * (1 + dc.risk_appetite * cfg.risk_raise_coeff)
                delta = old_price * raise_rate
            else:
                cut_rate = cfg.base_cut_rate * (1 + (1 - dc.profit_focus) * cfg.concession_coeff)
                delta = -old_price * cut_rate

            acumen = max(dc.business_acumen, 0.01)
            noise_scale = cfg.noise_coeff / acumen
            noise = random.gauss(0, noise_scale * old_price)

            new_price = old_price + delta + noise
            pc.prices[gt] = max(1, round(new_price))

    # ── 采购偏好 ──

    @staticmethod
    def _price_attractiveness(price: int, avg_price: float) -> float:
        """用 sigmoid 计算价格吸引力，范围 [-1, 1]。"""
        if avg_price <= 0:
            return 0.0
        k = 5.0
        x = k * (avg_price - price) / avg_price
        return 2.0 / (1.0 + math.exp(-x)) - 1.0

    def calculate_supplier_score(
        self,
        marketing_awareness: float,
        price_sensitivity: float,
        quality: float,
        price: int,
        brand_value: int,
        avg_price: float,
    ) -> float:
        """计算供应商评分（三维加权：品质+品牌+价格吸引力）。"""
        cfg = self.config.purchase
        w_brand = marketing_awareness * cfg.brand_weight_coeff
        w_price = price_sensitivity * cfg.brand_weight_coeff
        w_quality = max(0.0, 1.0 - w_brand - w_price)
        price_score = self._price_attractiveness(price, avg_price)
        return w_quality * quality + w_brand * brand_value + w_price * price_score

    def make_purchase_sort_key(self, company: Company) -> Callable[[SellOrder], float]:
        """生成带 CEO 特质的采购排序函数。"""
        dc = company.get_component(DecisionComponent)
        awareness = dc.marketing_awareness
        price_sens = dc.price_sensitivity
        avg_prices = dc.last_avg_buy_prices

        def sort_key(order: SellOrder) -> float:
            gt = order.batch.goods_type
            avg_price = avg_prices.get(gt, 0.0)
            if avg_price <= 0:
                avg_price = gt.base_price
            return self.calculate_supplier_score(
                marketing_awareness=awareness,
                price_sensitivity=price_sens,
                quality=order.batch.quality,
                price=order.price,
                brand_value=order.batch.brand_value,
                avg_price=avg_price,
            )

        return sort_key

    # ── 计划阶段内部方法 ──

    def _plan_expansion(self, company: Company) -> int:
        """计划扩产金额（= 选定工厂类型的 build_cost，或 0）。"""
        dc = company.get_component(DecisionComponent)
        pc = company.get_component(ProductorComponent)
        cfg = self.config.investment

        if not pc.factories:
            return 0

        # 感知市场前景
        # TODO: 接入真实供需比
        acumen = max(dc.business_acumen, 0.01)
        noise = random.gauss(0, cfg.perception_noise_coeff / acumen)
        perceived_ratio = 0.8 + noise  # 占位供需比

        market_outlook = max(0.0, 1.0 - perceived_ratio)

        ledger = company.get_component(LedgerComponent)
        min_cost = min(ft.build_cost for ft in pc.factories)
        cash_adequacy = min(ledger.cash / (min_cost * 2), 1.0)
        willingness = (dc.risk_appetite + market_outlook + cash_adequacy) / 3.0

        if willingness <= cfg.investment_threshold:
            return 0

        ft = self._pick_factory_type(company)
        return ft.build_cost if ft is not None else 0

    def _plan_brand(self, company: Company) -> int:
        """计划品牌支出金额。"""
        dc = company.get_component(DecisionComponent)
        cfg = self.config.brand
        return int(dc.last_revenue * cfg.base_ratio * (1 + dc.marketing_awareness * cfg.marketing_coeff))

    def _plan_tech(self, company: Company) -> int:
        """计划科技支出金额。"""
        dc = company.get_component(DecisionComponent)
        cfg = self.config.tech
        return int(dc.last_revenue * cfg.base_ratio * (1 + dc.tech_focus * cfg.tech_coeff))

    def _pick_factory_type(self, company: Company) -> Optional[FactoryType]:
        """选择最便宜的现有工厂类型用于扩产。"""
        pc = company.get_component(ProductorComponent)
        if not pc.factories:
            return None
        return min(pc.factories, key=lambda ft: ft.build_cost)

    # ── 贷款需求计算 ──

    def calc_loan_needs(self, companies: List[Company]) -> List[LoanApplication]:
        """根据投资计划和保留金计算每个企业的贷款需求。

        目标：现金 >= 保留金额 + 投资计划总额
        贷款需求 = max(0, 保留金额 + 投资计划总额 - 现金)
        """
        applications: List[LoanApplication] = []
        for company in companies:
            dc = company.get_component(DecisionComponent)
            ledger = company.get_component(LedgerComponent)
            plan_total = sum(dc.investment_plan.values())
            if plan_total == 0:
                continue
            reserved = self._calc_reserved_cash(company)
            loan_need = reserved + plan_total - ledger.cash
            if loan_need > 0:
                applications.append(LoanApplication(applicant=company, amount=loan_need))
        return applications

    # ── 执行阶段内部方法 ──

    def _calc_operating_expense(self, company: Company) -> int:
        """计算经营开销（当前仅维护费）。"""
        pc = company.get_component(ProductorComponent)
        return sum(
            ft.maintenance_cost
            for ft, factories in pc.factories.items()
            for f in factories
            if f.is_built
        )

    def _calc_reserved_cash(self, company: Company) -> int:
        """计算保留金 = 经营开销 × (1 + (1 - risk_appetite) × reserve_coeff)。"""
        dc = company.get_component(DecisionComponent)
        expense = self._calc_operating_expense(company)
        coeff = self.config.investment.reserve_coeff
        return int(expense * (1 + (1 - dc.risk_appetite) * coeff))

    def _apply_brand(self, company: Company, amount: int) -> None:
        """将品牌投入金额应用到产出商品的 brand_values。"""
        pc = company.get_component(ProductorComponent)
        output_types = [ft.recipe.output_goods_type for ft in pc.factories]
        if not output_types:
            return
        per_type = amount // len(output_types)
        for gt in output_types:
            pc.brand_values[gt] = pc.brand_values.get(gt, 0) + per_type

    def _apply_tech(self, company: Company, amount: int) -> None:
        """将科技投入金额应用到配方的 tech_values。"""
        pc = company.get_component(ProductorComponent)
        recipes = [ft.recipe for ft in pc.factories]
        if not recipes:
            return
        per_recipe = amount // len(recipes)
        for recipe in recipes:
            pc.tech_values[recipe] = pc.tech_values.get(recipe, 0) + per_recipe
