"""DecisionService 单元测试。"""

import random
from pathlib import Path

import pytest

from component.decision.company.classic import ClassicCompanyDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from core.config import ConfigManager
from core.entity import Entity
from entity.company.company import Company
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsBatch, GoodsType
from system.decision_service import DecisionService

_TEST_CONFIG_DIR = str(Path(__file__).parent / "config_integration")


@pytest.fixture(autouse=True)
def _reset_config():
    ConfigManager._instance = None
    ConfigManager().load(_TEST_CONFIG_DIR)
    yield
    ConfigManager._instance = None


def _make_company(
    *,
    business_acumen: float = 0.5,
    risk_appetite: float = 0.5,
    profit_focus: float = 0.5,
    marketing_awareness: float = 0.5,
    tech_focus: float = 0.5,
    price_sensitivity: float = 0.5,
    cash: int = 100_000,
) -> Company:
    company = Company(name="test_company")
    company.init_component(ClassicCompanyDecisionComponent)
    dc = company.get_component(ClassicCompanyDecisionComponent)
    dc.business_acumen = business_acumen
    dc.risk_appetite = risk_appetite
    dc.profit_focus = profit_focus
    dc.marketing_awareness = marketing_awareness
    dc.tech_focus = tech_focus
    dc.price_sensitivity = price_sensitivity
    ledger = company.get_component(LedgerComponent)
    ledger.cash = cash
    company.initial_wage = 10
    return company


def _service() -> DecisionService:
    ds = DecisionService()
    ds.set_market_data(sell_orders=[], trades=[], economy_index=1.0)
    return ds


def _set_context(svc: DecisionService, company: Company) -> None:
    """Helper: build and set context on the decision component (as plan_phase would)."""
    dc = svc._get_decision_component(company)
    ctx = svc._build_context(company)
    dc.set_context(ctx)


# ── 固定测试用的商品/工厂 ──

def _make_factory_setup():
    gt = GoodsType(name="硅", base_price=100)
    recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt, output_quantity=1, tech_quality_weight=1.0)
    ft = FactoryType(recipe=recipe, labor_demand=50, build_cost=50000, maintenance_cost=3000, build_time=2)
    return gt, recipe, ft


class TestInvestmentPlan:
    """plan_phase 生成完整计划表。"""

    def test_plan_phase_populates_investment_plan(self) -> None:
        random.seed(42)
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=0.9, business_acumen=0.9, marketing_awareness=0.5, tech_focus=0.5, cash=200_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        mc = company.get_component(MetricComponent)
        mc.last_revenue = 100_000

        _service().plan_phase([company])

        dc = company.get_component(ClassicCompanyDecisionComponent)
        plan = dc.investment_plan
        assert "expansion" in plan
        assert "brand" in plan
        assert "tech" in plan
        assert all(isinstance(v, int) for v in plan.values())


class TestActPhase:
    """act_phase 投资执行。"""

    def test_full_budget_executes_all(self) -> None:
        """预算充足时全额执行。"""
        gt, recipe, ft = _make_factory_setup()
        company = _make_company(cash=200_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        dc = company.get_component(ClassicCompanyDecisionComponent)

        svc = _service()
        _set_context(svc, company)
        dc.investment_plan = {"expansion": ft.build_cost, "brand": 5000, "tech": 3000}

        svc.maintenance_phase([company])
        svc.act_phase([company])

        ledger = company.get_component(LedgerComponent)
        # 花了 50000 + 5000 + 3000 = 58000
        assert ledger.cash == 200_000 - 58000 - 3000  # 58000 investment + 3000 maintenance
        assert len(pc.factories[ft]) == 2  # 新建了一个工厂
        assert pc.brand_values.get(gt, 0) == 5000
        assert pc.tech_values.get(recipe, 0) == 3000

    def test_proportional_allocation(self) -> None:
        """预算不足时按比例分配。"""
        gt, recipe, ft = _make_factory_setup()
        company = _make_company(risk_appetite=1.0, cash=15_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        dc = company.get_component(ClassicCompanyDecisionComponent)

        svc = _service()
        _set_context(svc, company)
        # 计划总额 = 50000 + 5000 + 5000 = 60000
        dc.investment_plan = {"expansion": 50000, "brand": 5000, "tech": 5000}

        # reserved = 3000*(1+0*2)=3000, budget = 15000-3000 = 12000
        svc.maintenance_phase([company])
        svc.act_phase([company])

        ledger = company.get_component(LedgerComponent)
        # expansion 分配 = int(12000 * 50000/60000) = 10000 < 50000 build_cost → 回流
        # brand 分配 = int(12000 * 5000/60000) = 1000
        # tech 分配 = int(12000 * 5000/60000) = 1000
        assert len(pc.factories[ft]) == 1  # 没建成新工厂
        assert pc.brand_values.get(gt, 0) == 1000
        assert pc.tech_values.get(recipe, 0) == 1000
        assert ledger.cash == 15_000 - 2000 - 3000  # 2000 investment + 3000 maintenance

    def test_expansion_insufficient_rolls_back(self) -> None:
        """扩产分配金额不够建厂时回流。"""
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=1.0, cash=50_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        dc = company.get_component(ClassicCompanyDecisionComponent)

        svc = _service()
        _set_context(svc, company)
        dc.investment_plan = {"expansion": 50000, "brand": 0, "tech": 0}

        # reserved = 3000, budget = 47000 < 50000 → expansion 分配 47000 < build_cost → 回流
        svc.maintenance_phase([company])
        svc.act_phase([company])

        ledger = company.get_component(LedgerComponent)
        assert len(pc.factories[ft]) == 1  # 没建
        assert ledger.cash == 50_000 - 3000  # 3000 maintenance

    def test_empty_plan_no_change(self) -> None:
        """空计划不花钱。"""
        company = _make_company(cash=100_000)
        dc = company.get_component(ClassicCompanyDecisionComponent)

        svc = _service()
        _set_context(svc, company)
        dc.investment_plan = {"expansion": 0, "brand": 0, "tech": 0}

        svc.act_phase([company])
        assert company.get_component(LedgerComponent).cash == 100_000


class TestMakePurchaseSortKey:
    """make_purchase_sort_key via DecisionService delegation."""

    def test_make_sort_key_returns_callable(self) -> None:
        svc = _service()
        company = _make_company(marketing_awareness=0.6)
        # plan_phase sets context, which is required by make_purchase_sort_key
        svc.plan_phase([company])
        sort_fn = svc.make_purchase_sort_key(company)
        gt = GoodsType(name="硅", base_price=100)
        batch = GoodsBatch(goods_type=gt, quantity=100, quality=0.7, brand_value=5)
        from system.market_service import SellOrder
        order = SellOrder(seller=Entity(), batch=batch, price=80)
        assert isinstance(sort_fn(order), float)


class TestLoanNeed:
    """plan_phase 后贷款需求计算。"""

    def test_loan_need_when_budget_insufficient(self) -> None:
        """计划总额 > 可用预算时，生成贷款申请。"""
        random.seed(42)
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=1.0, cash=10_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        mc = company.get_component(MetricComponent)
        mc.last_revenue = 100_000

        svc = _service()
        svc.plan_phase([company])
        apps = svc.calc_loan_needs([company])
        assert len(apps) == 1
        assert apps[0].applicant is company
        assert apps[0].amount > 0

    def test_no_loan_need_when_budget_sufficient(self) -> None:
        """可用预算 >= 计划总额时，不生成贷款申请。"""
        random.seed(42)
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=1.0, cash=500_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        mc = company.get_component(MetricComponent)
        mc.last_revenue = 100_000

        svc = _service()
        # First run plan_phase to get investment plans
        svc.plan_phase([company])
        apps = svc.calc_loan_needs([company])
        assert len(apps) == 0

    def test_loan_need_equals_shortfall(self) -> None:
        """贷款需求 = 保留金额 + 计划总额 - 现金。"""
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=1.0, cash=20_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        dc = company.get_component(ClassicCompanyDecisionComponent)

        svc = _service()
        _set_context(svc, company)
        # Manually set plan to test exact calculation
        dc.investment_plan = {"expansion": 50_000, "brand": 5_000, "tech": 5_000}

        # reserved = 3000 * (1 + 0*2) = 3000
        # loan_need = 3000 + 60000 - 20000 = 43000
        apps = svc.calc_loan_needs([company])
        assert len(apps) == 1
        assert apps[0].amount == 43_000


class TestLastAvgBuyPrices:
    """ClassicCompanyDecisionComponent 购买均价追踪。"""

    def test_metric_component_has_last_avg_buy_prices(self) -> None:
        company = _make_company()
        mc = company.get_component(MetricComponent)
        assert mc.last_avg_buy_prices == {}


class TestDecideWage:
    """DecisionService plan_phase 后企业有 wage 属性。"""

    def test_plan_phase_sets_wage(self) -> None:
        """plan_phase 后企业应有 wage 属性。"""
        random.seed(42)
        gt, recipe, ft = _make_factory_setup()
        company = _make_company()
        pc = company.init_component(ProductorComponent)
        pc.factories[ft].append(Factory(factory_type=ft, build_remaining=0))

        # 设置 initial_wage
        company.initial_wage = 15

        svc = _service()
        svc.plan_phase([company])

        assert hasattr(company, "wage")
        assert company.wage == 15
