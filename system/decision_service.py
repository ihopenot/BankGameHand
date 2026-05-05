from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from component.decision.company.ai import AICompanyDecisionComponent
from component.decision.company.base import BaseCompanyDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from core.config import ConfigManager
from core.types import LoanApplication
from entity.factory import Factory, FactoryType

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
                "initial_wage": company.initial_wage,
                "current_wage": company.wage,
                "last_operating_expense": getattr(company, 'last_operating_expense', 0),
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
        """决策阶段：组装 context → AI 公司并行 query → 回填结果 → prepare 下一轮。"""
        # 1. 构建所有 context
        contexts: List[Tuple[Company, BaseCompanyDecisionComponent, dict]] = []
        ai_queries: List[Tuple[str, str]] = []  # (company_name, prompt)
        ai_indices: List[int] = []  # ai_queries 中对应的公司在 contexts 中的下标

        for company in companies:
            dc = self._get_decision_component(company)
            ctx = self._build_context(company)
            BaseCompanyDecisionComponent.set_context(dc, ctx)  # 只设 context 不触发 AI

            if isinstance(dc, AICompanyDecisionComponent):
                prompt = dc._build_prompt(ctx)
                ai_queries.append((company.name, prompt))
                ai_indices.append(len(contexts))
            contexts.append((company, dc, ctx))

        # 2. 并行 query 所有 AI 公司
        if ai_queries:
            decisions_list = AICompanyDecisionComponent.query_all_parallel(ai_queries)
            for qi, ci in enumerate(ai_indices):
                _, dc, _ = contexts[ci]
                dc._ai_decisions = decisions_list[qi]

        # 3. 逐个公司应用决策结果
        for company, dc, ctx in contexts:
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

            # 决策：工资定价
            company.wage = dc.decide_wage()

            # 记录本回合运营支出供下轮工资决策参考
            company.last_operating_expense = dc._calc_operating_expense()

        # plan_phase 完成后立即 prepare 下一轮 session
        self.prepare_next_round(companies)

    @staticmethod
    def _set_context_on_component(dc: BaseCompanyDecisionComponent, ctx: dict) -> None:
        """设置 context 到决策组件，不触发 AI 调用。"""
        from component.decision.company.base import BaseCompanyDecisionComponent
        # 只调用父类 set_context（Classic），不触发 AICompanyDecisionComponent 的 _query_ai
        BaseCompanyDecisionComponent.set_context(dc, ctx)

    def prepare_next_round(self, companies: List[Company]) -> None:
        """为所有 AI 公司 prepare 下一轮的 AgentSession。"""
        ai_company_names = []
        for company in companies:
            dc = self._get_decision_component(company)
            if isinstance(dc, AICompanyDecisionComponent):
                ai_company_names.append(company.name)
        if ai_company_names:
            AICompanyDecisionComponent.prepare_next_sessions(ai_company_names)

    def maintenance_phase(self, companies: List[Company], folks: List | None = None) -> None:
        """维护阶段：逐个工厂扣维护费，现金不足标记未维护，并记录工厂统计。"""
        for company in companies:
            pc = company.get_component(ProductorComponent)
            mc = company.get_component(MetricComponent)

            maintenance_cost = self._pay_maintenance(company)
            if maintenance_cost > 0:
                if folks:
                    self.distribute_spending_to_folks("maintenance", maintenance_cost, folks)

            # 记录工厂统计
            for ft, factory_list in pc.factories.items():
                for f in factory_list:
                    if not f.is_built:
                        mc.factories_building += 1
                    elif f.maintained:
                        mc.factories_active += 1
                    else:
                        mc.factories_idle += 1

    def act_phase(self, companies: List[Company], folks: List | None = None) -> None:
        """执行阶段：委托预算分配 + 执行投资 + 支出分流到居民。"""
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
                if folks:
                    self.distribute_spending_to_folks("brand", brand_budget, folks)
                actual_spent += brand_budget
                mc.cumulative_brand_spend += brand_budget

            # 科技投入
            tech_budget = allocation.get("tech", 0)
            if tech_budget > 0:
                self._apply_tech(company, tech_budget)
                if folks:
                    self.distribute_spending_to_folks("tech", tech_budget, folks)
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

    def distribute_spending_to_folks(self, spending_type: str, amount: int, folks: list) -> None:
        """将企业支出按 Folk.spending_flow 比例分流到各 Folk 组的 LedgerComponent.cash。"""
        if amount <= 0:
            return
        for folk in folks:
            ratio = folk.spending_flow[spending_type]
            if ratio > 0:
                share = int(amount * ratio)
                if share > 0:
                    ledger = folk.get_component(LedgerComponent)
                    ledger.cash += share

    def _pay_maintenance(self, company: Company) -> int:
        """逐个工厂支付维护费，现金不足时标记工厂未维护。返回实际支付总额。"""
        pc = company.get_component(ProductorComponent)
        if pc is None:
            return 0
        ledger = company.get_component(LedgerComponent)
        total_paid = 0
        for ft, factory_list in pc.factories.items():
            for f in factory_list:
                if not f.is_built:
                    continue
                if ledger.cash >= ft.maintenance_cost:
                    ledger.cash -= ft.maintenance_cost
                    total_paid += ft.maintenance_cost
                    f.maintained = True
                else:
                    f.maintained = False
        return total_paid

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
