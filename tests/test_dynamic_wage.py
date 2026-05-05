"""企业动态工资决策测试。"""

import math
from pathlib import Path

import pytest

from component.decision.company.classic import ClassicCompanyDecisionComponent
from core.config import ConfigManager
from core.entity import Entity
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsType, load_goods_types


@pytest.fixture(autouse=True)
def _clear_components():
    ClassicCompanyDecisionComponent.components.clear()
    yield
    ClassicCompanyDecisionComponent.components.clear()


@pytest.fixture(autouse=True)
def _load_config():
    """确保配置和 GoodsType 已加载。"""
    ConfigManager._instance = None
    ConfigManager().load(str(Path(__file__).parent / "config_integration"))
    GoodsType.types.clear()
    load_goods_types()
    yield
    ConfigManager._instance = None


def _make_factory_type(
    maintenance_cost: int = 100,
    labor_demand: int = 10,
    output_quantity: int = 100,
    input_quantity: int = 50,
) -> FactoryType:
    """创建测试用 FactoryType（原料层，无输入原料）。"""
    gt_out = list(GoodsType.types.values())[0]
    recipe = Recipe(
        input_goods_type=None,  # 原料层，无输入
        input_quantity=0,
        output_goods_type=gt_out,
        output_quantity=output_quantity,
        tech_quality_weight=0.5,
    )
    return FactoryType(
        recipe=recipe,
        labor_demand=labor_demand,
        build_cost=1000,
        maintenance_cost=maintenance_cost,
        build_time=0,
    )


def _make_context(
    cash: int = 100000,
    initial_wage: int = 400,
    current_prices: dict | None = None,
    avg_buy_prices: dict | None = None,
    factories: dict | None = None,
    last_operating_expense: int = 0,
    profit_focus: float = 0.5,
    risk_appetite: float = 0.5,
) -> dict:
    """构建测试 context。"""
    gt_out = list(GoodsType.types.values())[0]
    ft = _make_factory_type()

    if current_prices is None:
        current_prices = {gt_out: 1000}
    if factories is None:
        factories = {ft: [Factory(ft, build_remaining=0)]}
    if avg_buy_prices is None:
        avg_buy_prices = {}

    return {
        "company": {
            "name": "TestCorp",
            "ceo_traits": {
                "business_acumen": 0.5,
                "risk_appetite": risk_appetite,
                "profit_focus": profit_focus,
                "marketing_awareness": 0.5,
                "tech_focus": 0.5,
                "price_sensitivity": 0.5,
            },
            "initial_wage": initial_wage,
            "current_wage": initial_wage,
            "last_operating_expense": last_operating_expense,
        },
        "ledger": {
            "cash": cash,
            "revenue": 0,
            "expense": 0,
            "receivables": 0,
            "payables": 0,
        },
        "productor": {
            "factories": factories,
            "tech_levels": {},
            "brand_values": {},
            "current_prices": current_prices,
        },
        "metric": {
            "my_sell_orders": {},
            "my_sold_quantities": {},
            "last_revenue": 5000,
            "my_avg_buy_prices": avg_buy_prices,
        },
        "market": {
            "economy_index": 0.0,
            "sell_orders": [],
            "trades": [],
        },
    }


class TestDynamicWage:
    """动态工资决策测试。"""

    def test_wage_returns_positive_int(self) -> None:
        """decide_wage 应返回正整数。"""
        entity = Entity("test")
        comp = entity.init_component(ClassicCompanyDecisionComponent)
        ctx = _make_context(cash=100000, initial_wage=400, last_operating_expense=10000)
        comp.set_context(ctx)
        wage = comp.decide_wage()
        assert isinstance(wage, int)
        assert wage > 0

    def test_low_cash_reduces_wage(self) -> None:
        """现金紧张时目标工资应低于充裕时。"""
        entity1 = Entity("test1")
        comp1 = entity1.init_component(ClassicCompanyDecisionComponent)
        ctx1 = _make_context(cash=5000, initial_wage=400, last_operating_expense=10000)
        comp1.set_context(ctx1)
        wage_low_cash = comp1.decide_wage()

        entity2 = Entity("test2")
        comp2 = entity2.init_component(ClassicCompanyDecisionComponent)
        ctx2 = _make_context(cash=500000, initial_wage=400, last_operating_expense=10000)
        comp2.set_context(ctx2)
        wage_high_cash = comp2.decide_wage()

        assert wage_low_cash < wage_high_cash

    def test_high_profit_focus_lowers_wage(self) -> None:
        """profit_focus 高的 CEO 设定更低的工资（保利润）。"""
        entity1 = Entity("test1")
        comp1 = entity1.init_component(ClassicCompanyDecisionComponent)
        ctx1 = _make_context(cash=100000, initial_wage=400, last_operating_expense=10000, profit_focus=0.9)
        comp1.set_context(ctx1)
        wage_high_pf = comp1.decide_wage()

        entity2 = Entity("test2")
        comp2 = entity2.init_component(ClassicCompanyDecisionComponent)
        ctx2 = _make_context(cash=100000, initial_wage=400, last_operating_expense=10000, profit_focus=0.1)
        comp2.set_context(ctx2)
        wage_low_pf = comp2.decide_wage()

        assert wage_high_pf < wage_low_pf

    def test_zero_operating_expense_neutral(self) -> None:
        """上回合运营支出为0时应返回正常工资（中性状态）。"""
        entity = Entity("test")
        comp = entity.init_component(ClassicCompanyDecisionComponent)
        ctx = _make_context(cash=100000, initial_wage=400, last_operating_expense=0)
        comp.set_context(ctx)
        wage = comp.decide_wage()
        assert isinstance(wage, int)
        assert wage > 0

    def test_incremental_approach(self) -> None:
        """工资应增量逼近目标，不会一步到位。"""
        entity = Entity("test")
        comp = entity.init_component(ClassicCompanyDecisionComponent)
        # 设置一个 target 远高于 current 的情况
        ctx = _make_context(cash=1000000, initial_wage=100, last_operating_expense=5000)
        comp.set_context(ctx)
        wage = comp.decide_wage()
        # 工资应增加但不会一步跳到目标
        # target_wage ≈ 9240, adjusted_target ≈ 13860 (cash_factor=1.5)
        # step_rate=0.2: new ≈ 100 + 0.2*(13860-100) = 2852
        assert wage > 100
        # 不应到达 adjusted_target（13860）的 50% 以上，因为 step=0.2
        assert wage < 9000

    def test_no_factories_returns_current(self) -> None:
        """无工厂时返回 current_wage。"""
        entity = Entity("test")
        comp = entity.init_component(ClassicCompanyDecisionComponent)
        ctx = _make_context(cash=100000, initial_wage=400, factories={})
        comp.set_context(ctx)
        wage = comp.decide_wage()
        assert wage == 400
