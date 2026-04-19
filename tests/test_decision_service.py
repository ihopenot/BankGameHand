"""DecisionService 单元测试。"""

import random
from pathlib import Path

import pytest

from component.decision_component import DecisionComponent
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
    cash: int = 100_000,
) -> Company:
    company = Company()
    dc = company.get_component(DecisionComponent)
    dc.business_acumen = business_acumen
    dc.risk_appetite = risk_appetite
    dc.profit_focus = profit_focus
    dc.marketing_awareness = marketing_awareness
    dc.tech_focus = tech_focus
    ledger = company.get_component(LedgerComponent)
    ledger.cash = cash
    return company


def _service() -> DecisionService:
    return DecisionService()


# ── 固定测试用的商品/工厂 ──

def _make_factory_setup():
    gt = GoodsType(name="硅", base_price=100)
    recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt, output_quantity=1, tech_quality_weight=1.0)
    ft = FactoryType(recipe=recipe, base_production=100, build_cost=50000, maintenance_cost=3000, build_time=2)
    return gt, recipe, ft


class TestPricingDecision:

    def test_sold_out_raises_price(self) -> None:
        random.seed(42)
        gt = GoodsType(name="芯片", base_price=5000)
        company = _make_company(business_acumen=1.0)
        pc = company.get_component(ProductorComponent)
        pc.prices[gt] = 5000
        mc = company.get_component(MetricComponent)
        mc.last_sell_orders[gt] = 100
        mc.last_sold_quantities[gt] = 100
        _service().decide_pricing(company)
        assert pc.prices[gt] > 5000

    def test_surplus_cuts_price(self) -> None:
        random.seed(42)
        gt = GoodsType(name="芯片", base_price=5000)
        company = _make_company(business_acumen=1.0)
        pc = company.get_component(ProductorComponent)
        pc.prices[gt] = 5000
        mc = company.get_component(MetricComponent)
        mc.last_sell_orders[gt] = 100
        mc.last_sold_quantities[gt] = 30
        _service().decide_pricing(company)
        assert pc.prices[gt] < 5000

    def test_high_profit_focus_less_cut_on_surplus(self) -> None:
        gt = GoodsType(name="芯片", base_price=5000)
        random.seed(42)
        c_high = _make_company(profit_focus=0.9, business_acumen=1.0)
        pc_high = c_high.get_component(ProductorComponent)
        pc_high.prices[gt] = 5000
        mc_high = c_high.get_component(MetricComponent)
        mc_high.last_sell_orders[gt] = 100
        mc_high.last_sold_quantities[gt] = 30

        random.seed(42)
        c_low = _make_company(profit_focus=0.1, business_acumen=1.0)
        pc_low = c_low.get_component(ProductorComponent)
        pc_low.prices[gt] = 5000
        mc_low = c_low.get_component(MetricComponent)
        mc_low.last_sell_orders[gt] = 100
        mc_low.last_sold_quantities[gt] = 30

        svc = _service()
        svc.decide_pricing(c_high)
        svc.decide_pricing(c_low)
        assert pc_high.prices[gt] > pc_low.prices[gt]

    def test_no_previous_sales_no_change(self) -> None:
        gt = GoodsType(name="芯片", base_price=5000)
        company = _make_company(business_acumen=1.0)
        pc = company.get_component(ProductorComponent)
        pc.prices[gt] = 5000
        _service().decide_pricing(company)
        assert pc.prices[gt] == 5000

    def test_price_stays_positive(self) -> None:
        random.seed(42)
        gt = GoodsType(name="芯片", base_price=100)
        company = _make_company(profit_focus=0.0, business_acumen=1.0)
        pc = company.get_component(ProductorComponent)
        pc.prices[gt] = 10
        mc = company.get_component(MetricComponent)
        mc.last_sell_orders[gt] = 100
        mc.last_sold_quantities[gt] = 10
        _service().decide_pricing(company)
        assert pc.prices[gt] > 0


class TestPlanBrand:
    """品牌计划只返回金额，不修改组件。"""

    def test_plan_brand_formula(self) -> None:
        _, _, ft = _make_factory_setup()
        company = _make_company(marketing_awareness=0.8)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        mc = company.get_component(MetricComponent)
        mc.last_revenue = 200_000

        amount = _service()._plan_brand(company)
        expected = int(200_000 * 0.05 * (1 + 0.8 * 1.0))
        assert amount == expected

    def test_plan_brand_does_not_modify_component(self) -> None:
        _, _, ft = _make_factory_setup()
        company = _make_company(marketing_awareness=0.8)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        mc = company.get_component(MetricComponent)
        mc.last_revenue = 200_000
        old_brand = dict(pc.brand_values)

        _service()._plan_brand(company)
        assert pc.brand_values == old_brand  # 不应被修改

    def test_zero_revenue(self) -> None:
        company = _make_company(marketing_awareness=1.0)
        company.get_component(MetricComponent).last_revenue = 0
        assert _service()._plan_brand(company) == 0


class TestPlanTech:
    """科技计划只返回金额，不修改组件。"""

    def test_plan_tech_formula(self) -> None:
        _, _, ft = _make_factory_setup()
        company = _make_company(tech_focus=0.6)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        mc = company.get_component(MetricComponent)
        mc.last_revenue = 300_000

        amount = _service()._plan_tech(company)
        expected = int(300_000 * 0.05 * (1 + 0.6 * 1.0))
        assert amount == expected

    def test_plan_tech_does_not_modify_component(self) -> None:
        gt, recipe, ft = _make_factory_setup()
        company = _make_company(tech_focus=0.6)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        mc = company.get_component(MetricComponent)
        mc.last_revenue = 300_000
        old_tech = dict(pc.tech_values)

        _service()._plan_tech(company)
        assert pc.tech_values == old_tech

    def test_zero_revenue(self) -> None:
        company = _make_company(tech_focus=1.0)
        company.get_component(MetricComponent).last_revenue = 0
        assert _service()._plan_tech(company) == 0


class TestPlanExpansion:
    """扩产计划只返回金额，不实际建厂。"""

    def test_high_willingness_returns_build_cost(self) -> None:
        random.seed(42)
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=0.9, business_acumen=0.9, cash=200_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))

        amount = _service()._plan_expansion(company)
        assert amount == ft.build_cost

    def test_low_willingness_returns_zero(self) -> None:
        random.seed(42)
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=0.1, business_acumen=0.9, cash=200_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))

        amount = _service()._plan_expansion(company)
        assert amount == 0

    def test_does_not_build_factory(self) -> None:
        random.seed(42)
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=0.9, business_acumen=0.9, cash=200_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        factory_count_before = len(pc.factories[ft])

        _service()._plan_expansion(company)
        assert len(pc.factories[ft]) == factory_count_before  # 不实际建厂


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

        dc = company.get_component(DecisionComponent)
        plan = dc.investment_plan
        assert "expansion" in plan
        assert "brand" in plan
        assert "tech" in plan
        assert all(isinstance(v, int) for v in plan.values())


class TestReservedCash:
    """保留金计算。"""

    def test_aggressive_reserves_less(self) -> None:
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=1.0)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))

        svc = _service()
        # maintenance_cost=3000, risk=1.0 → reserved = 3000 * (1 + 0 * 2) = 3000
        assert svc._calc_reserved_cash(company) == 3000

    def test_conservative_reserves_more(self) -> None:
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=0.0)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))

        svc = _service()
        # maintenance_cost=3000, risk=0.0 → reserved = 3000 * (1 + 1 * 2) = 9000
        assert svc._calc_reserved_cash(company) == 9000

    def test_unbuilt_factory_excluded(self) -> None:
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=1.0)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))  # 已建成
        pc.factories[ft].append(Factory(ft, build_remaining=3))  # 未建成

        svc = _service()
        # 只有 1 个已建成工厂，maintenance=3000
        assert svc._calc_reserved_cash(company) == 3000


class TestActPhase:
    """act_phase 投资执行。"""

    def test_full_budget_executes_all(self) -> None:
        """预算充足时全额执行。"""
        gt, recipe, ft = _make_factory_setup()
        company = _make_company(cash=200_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        dc = company.get_component(DecisionComponent)
        dc.investment_plan = {"expansion": ft.build_cost, "brand": 5000, "tech": 3000}

        svc = _service()
        svc.act_phase([company])

        ledger = company.get_component(LedgerComponent)
        # 花了 50000 + 5000 + 3000 = 58000
        assert ledger.cash == 200_000 - 58000
        assert len(pc.factories[ft]) == 2  # 新建了一个工厂
        assert pc.brand_values.get(gt, 0) == 5000
        assert pc.tech_values.get(recipe, 0) == 3000

    def test_proportional_allocation(self) -> None:
        """预算不足时按比例分配。"""
        gt, recipe, ft = _make_factory_setup()
        company = _make_company(risk_appetite=1.0, cash=15_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        dc = company.get_component(DecisionComponent)
        # 计划总额 = 50000 + 5000 + 5000 = 60000
        dc.investment_plan = {"expansion": 50000, "brand": 5000, "tech": 5000}

        svc = _service()
        # reserved = 3000*(1+0*2)=3000, budget = 15000-3000 = 12000
        svc.act_phase([company])

        ledger = company.get_component(LedgerComponent)
        # expansion 分配 = int(12000 * 50000/60000) = 10000 < 50000 build_cost → 回流
        # brand 分配 = int(12000 * 5000/60000) = 1000
        # tech 分配 = int(12000 * 5000/60000) = 1000
        assert len(pc.factories[ft]) == 1  # 没建成新工厂
        assert pc.brand_values.get(gt, 0) == 1000
        assert pc.tech_values.get(recipe, 0) == 1000
        assert ledger.cash == 15_000 - 2000  # 只花了 brand + tech

    def test_expansion_insufficient_rolls_back(self) -> None:
        """扩产分配金额不够建厂时回流。"""
        _, _, ft = _make_factory_setup()
        company = _make_company(risk_appetite=1.0, cash=50_000)
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))
        dc = company.get_component(DecisionComponent)
        dc.investment_plan = {"expansion": 50000, "brand": 0, "tech": 0}

        svc = _service()
        # reserved = 3000, budget = 47000 < 50000 → expansion 分配 47000 < build_cost → 回流
        svc.act_phase([company])

        ledger = company.get_component(LedgerComponent)
        assert len(pc.factories[ft]) == 1  # 没建
        assert ledger.cash == 50_000  # 钱没花

    def test_empty_plan_no_change(self) -> None:
        """空计划不花钱。"""
        company = _make_company(cash=100_000)
        dc = company.get_component(DecisionComponent)
        dc.investment_plan = {"expansion": 0, "brand": 0, "tech": 0}

        _service().act_phase([company])
        assert company.get_component(LedgerComponent).cash == 100_000


class TestPurchasePreference:

    def test_score_formula(self) -> None:
        svc = _service()
        score = svc.calculate_supplier_score(marketing_awareness=0.5, price_sensitivity=0.0, quality=0.8, price=100, brand_value=10, avg_price=100)
        # w_brand=0.5*0.5=0.25, w_price=0.0*0.5=0.0, w_quality=0.75
        # price_attractiveness(100,100) = 0.0
        expected = 0.75 * 0.8 + 0.25 * 10 + 0.0 * 0.0
        assert abs(score - expected) < 1e-9

    def test_high_marketing_prefers_brand(self) -> None:
        svc = _service()
        score_cheap = svc.calculate_supplier_score(marketing_awareness=0.9, price_sensitivity=0.0, quality=0.5, price=50, brand_value=2, avg_price=100)
        score_brand = svc.calculate_supplier_score(marketing_awareness=0.9, price_sensitivity=0.0, quality=0.5, price=100, brand_value=20, avg_price=100)
        assert score_brand > score_cheap

    def test_low_marketing_prefers_value(self) -> None:
        svc = _service()
        score_cheap = svc.calculate_supplier_score(marketing_awareness=0.1, price_sensitivity=0.0, quality=0.9, price=50, brand_value=1, avg_price=100)
        score_brand = svc.calculate_supplier_score(marketing_awareness=0.1, price_sensitivity=0.0, quality=0.3, price=200, brand_value=1, avg_price=100)
        assert score_cheap > score_brand

    def test_make_sort_key_returns_callable(self) -> None:
        svc = _service()
        company = _make_company(marketing_awareness=0.6)
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
        dc = company.get_component(DecisionComponent)
        # Manually set plan to test exact calculation
        dc.investment_plan = {"expansion": 50_000, "brand": 5_000, "tech": 5_000}

        svc = _service()
        # reserved = 3000 * (1 + 0*2) = 3000
        # loan_need = 3000 + 60000 - 20000 = 43000
        apps = svc.calc_loan_needs([company])
        assert len(apps) == 1
        assert apps[0].amount == 43_000


class TestLastAvgBuyPrices:
    """DecisionComponent 购买均价追踪。"""

    def test_metric_component_has_last_avg_buy_prices(self) -> None:
        company = _make_company()
        mc = company.get_component(MetricComponent)
        assert mc.last_avg_buy_prices == {}
