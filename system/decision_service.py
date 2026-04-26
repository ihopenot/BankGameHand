from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from component.base_company_decision import BaseCompanyDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from core.config import ConfigManager
from core.types import LoanApplication
from entity.factory import Factory, FactoryType
from entity.goods import GoodsType

if TYPE_CHECKING:
    from entity.company.company import Company
    from system.market_service import SellOrder


class DecisionService:
    """企业决策服务：编排层，委托决策到 BaseCompanyDecisionComponent。"""

    def __init__(self) -> None:
        self.config = ConfigManager().section("decision")
        self._market_data: Dict | None = None

    @staticmethod
    def _get_decision_component(company: Company) -> BaseCompanyDecisionComponent:
        """获取公司的决策组件，不存在则抛出 ValueError。"""
        for comp in company._components.values():
            if isinstance(comp, BaseCompanyDecisionComponent):
                return comp
        raise ValueError(f"Company {getattr(company, 'name', '?')} has no decision component")

    # ── 上下文组装 ──

    def set_market_data(self, sell_orders: list, trades: list, economy_index: float) -> None:
        """设置市场数据（由 Game 在调用前传入）。"""
        self._market_data = {
            "economy_index": economy_index,
            "sell_orders": sell_orders,
            "trades": trades,
        }

    def _build_context(self, company: Company) -> dict:
        """从各 Component 组装 context dict。"""
        dc = self._get_decision_component(company)
        ledger = company.get_component(LedgerComponent)
        pc = company.get_component(ProductorComponent)
        mc = company.get_component(MetricComponent)

        ceo_traits = {
            "business_acumen": dc.business_acumen,
            "risk_appetite": dc.risk_appetite,
            "profit_focus": dc.profit_focus,
            "marketing_awareness": dc.marketing_awareness,
            "tech_focus": dc.tech_focus,
            "price_sensitivity": dc.price_sensitivity,
        }

        return {
            "company": {
                "name": company.name,
                "ceo_traits": ceo_traits,
            },
            "ledger": {
                "cash": ledger.cash,
                "revenue": 0,
                "expense": 0,
                "receivables": ledger.total_receivables(),
                "payables": ledger.total_payables(),
            },
            "productor": {
                "factories": dict(pc.factories),
                "tech_levels": dict(pc.tech_values),
                "brand_values": dict(pc.brand_values),
                "current_prices": dict(pc.prices),
            },
            "metric": {
                "my_sell_orders": dict(mc.last_sell_orders),
                "my_sold_quantities": dict(mc.last_sold_quantities),
                "last_revenue": mc.last_revenue,
                "my_avg_buy_prices": dict(mc.last_avg_buy_prices),
            },
            "market": dict(self._market_data),
        }

    # ── 编排接口（供 Game 调用） ──

    def plan_phase(self, companies: List[Company]) -> None:
        """决策阶段：组装 context → 委托到组件。"""
        for company in companies:
            dc = self._get_decision_component(company)

            ctx = self._build_context(company)
            dc.set_context(ctx)

            # 决策一：定价
            new_prices = dc.decide_pricing()
            pc = company.get_component(ProductorComponent)
            for gt_name, price in new_prices.items():
                for gt in pc.prices:
                    if getattr(gt, "name", None) == gt_name or gt == gt_name:
                        pc.prices[gt] = price
                        break

            # 决策二：投资计划
            dc.decide_investment_plan()

    def act_phase(self, companies: List[Company]) -> None:
        """执行阶段：委托预算分配 + 执行投资。"""
        for company in companies:
            dc = self._get_decision_component(company)
            pc = company.get_component(ProductorComponent)
            ledger = company.get_component(LedgerComponent)
            mc = company.get_component(MetricComponent)

            allocation = dc.decide_budget_allocation()
            plan_total = sum(allocation.values())
            if plan_total == 0:
                continue

            actual_spent = 0

            # 扩产
            expansion_budget = allocation.get("expansion", 0)
            ft = self._pick_factory_type(company)
            if ft is not None and expansion_budget >= ft.build_cost:
                factory = Factory(ft, build_remaining=ft.build_time)
                pc.factories[ft].append(factory)
                actual_spent += ft.build_cost
                mc.cumulative_expansion_spend += ft.build_cost

            # 品牌投入
            brand_budget = allocation.get("brand", 0)
            if brand_budget > 0:
                self._apply_brand(company, brand_budget)
                actual_spent += brand_budget
                mc.cumulative_brand_spend += brand_budget

            # 科技投入
            tech_budget = allocation.get("tech", 0)
            if tech_budget > 0:
                self._apply_tech(company, tech_budget)
                actual_spent += tech_budget
                mc.cumulative_tech_spend += tech_budget

            ledger.cash -= actual_spent
            pc.update_max_tech()

    # ── 采购排序 ──

    def make_purchase_sort_key(self, company: Company) -> Callable[[SellOrder], float]:
        """生成带 CEO 特质的采购排序函数，委托到组件。"""
        dc = self._get_decision_component(company)
        return dc.make_purchase_sort_key()

    # ── 贷款需求 ──

    def calc_loan_needs(self, companies: List[Company]) -> List[LoanApplication]:
        """根据组件的 decide_loan_needs 计算贷款需求。"""
        applications: List[LoanApplication] = []
        for company in companies:
            dc = self._get_decision_component(company)
            amount, max_rate = dc.decide_loan_needs()
            if amount > 0:
                applications.append(LoanApplication(applicant=company, amount=amount))
        return applications

    # ── 内部方法 ──

    def _pick_factory_type(self, company: Company) -> Optional[FactoryType]:
        """选择最便宜的现有工厂类型用于扩产。"""
        pc = company.get_component(ProductorComponent)
        if pc is None or not pc.factories:
            return None
        return min(pc.factories, key=lambda ft: ft.build_cost)

    def _apply_brand(self, company: Company, amount: int) -> None:
        """将品牌投入金额应用到产出商品的 brand_values。"""
        pc = company.get_component(ProductorComponent)
        if pc is None:
            return
        output_types = [ft.recipe.output_goods_type for ft in pc.factories]
        if not output_types:
            return
        per_type = amount // len(output_types)
        for gt in output_types:
            pc.brand_values[gt] = pc.brand_values.get(gt, 0) + per_type

    def _apply_tech(self, company: Company, amount: int) -> None:
        """将科技投入金额应用到配方的 tech_values。"""
        pc = company.get_component(ProductorComponent)
        if pc is None:
            return
        recipes = [ft.recipe for ft in pc.factories]
        if not recipes:
            return
        per_recipe = amount // len(recipes)
        for recipe in recipes:
            pc.tech_values[recipe] = pc.tech_values.get(recipe, 0) + per_recipe
