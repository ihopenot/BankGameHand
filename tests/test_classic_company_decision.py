"""ClassicCompanyDecisionComponent 经典决策组件测试。"""

import math
import random
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock

import pytest

from component.decision.company.base import BaseCompanyDecisionComponent
from component.decision.company.classic import ClassicCompanyDecisionComponent
from core.config import ConfigManager
from core.entity import Entity
from entity.factory import Factory, FactoryType
from entity.goods import GoodsBatch, GoodsType, load_goods_types
from system.market_service import SellOrder


# ── Fixtures ──


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


@pytest.fixture()
def comp() -> ClassicCompanyDecisionComponent:
    """创建一个挂载在 Entity 上的 ClassicCompanyDecisionComponent。"""
    entity = Entity()
    return entity.init_component(ClassicCompanyDecisionComponent)


def _get_goods_type(name: str) -> GoodsType:
    """获取已注册的 GoodsType，不存在则报错。"""
    gt = GoodsType.types.get(name)
    if gt is None:
        raise ValueError(f"GoodsType '{name}' not registered — test data out of sync with config")
    return gt


def _make_context(
    cash: int = 10000,
    revenue: int = 5000,
    last_revenue: int = 5000,
    sell_orders: dict | None = None,
    sold_quantities: dict | None = None,
    current_prices: dict | None = None,
    brand_values: dict | None = None,
    factories: dict | None = None,
    avg_buy_prices: dict | None = None,
) -> dict:
    """构建一个用于测试的 context dict。

    factories: Dict[FactoryType, List[Factory]] 格式，与 ProductorComponent.factories 一致
    sell_orders / sold_quantities / current_prices: 以 GoodsType 对象为 key
    """
    return {
        "company": {
            "name": "TestCorp",
            "ceo_traits": {
                "business_acumen": 0.5,
                "risk_appetite": 0.5,
                "profit_focus": 0.5,
                "marketing_awareness": 0.5,
                "tech_focus": 0.5,
                "price_sensitivity": 0.5,
            },
        },
        "ledger": {
            "cash": cash,
            "revenue": revenue,
            "expense": 1000,
            "receivables": 0,
            "payables": 0,
        },
        "productor": {
            "factories": factories if factories is not None else {},
            "tech_levels": {},
            "brand_values": brand_values or {},
            "current_prices": current_prices or {},
        },
        "metric": {
            "my_sell_orders": sell_orders or {},
            "my_sold_quantities": sold_quantities or {},
            "last_revenue": last_revenue,
            "my_avg_buy_prices": avg_buy_prices or {},
        },
        "market": {
            "economy_index": 1.0,
            "sell_orders": [],
            "trades": [],
        },
    }


# ── 2.1: set_context + decide_pricing ──


class TestClassicSetContextAndPricing:
    """2.1: set_context 存储 context，decide_pricing 返回正确结果。"""

    def test_set_context_stores_context(self, comp) -> None:
        ctx = _make_context()
        comp.set_context(ctx)
        assert comp._context is ctx

    def test_decide_pricing_returns_dict(self, comp) -> None:
        """decide_pricing 应返回 dict[str, int]。"""
        gt = _get_goods_type("食品")

        ctx = _make_context(
            sell_orders={gt: 10},
            sold_quantities={gt: 10},
            current_prices={gt: 100},
        )
        comp.set_context(ctx)
        result = comp.decide_pricing()
        assert isinstance(result, dict)
        assert gt.name in result

    def test_decide_pricing_sold_out_raises_price(self, comp) -> None:
        """售罄时涨价。"""
        gt = _get_goods_type("食品")

        ctx = _make_context(
            sell_orders={gt: 10},
            sold_quantities={gt: 10},
            current_prices={gt: 100},
        )
        comp.set_context(ctx)
        random.seed(42)
        result = comp.decide_pricing()
        new_price = result.get(gt.name, 100)
        assert new_price >= 100

    def test_decide_pricing_unsold_lowers_price(self, comp) -> None:
        """未售完时降价。"""
        gt = _get_goods_type("食品")

        ctx = _make_context(
            sell_orders={gt: 10},
            sold_quantities={gt: 2},
            current_prices={gt: 100},
        )
        comp.set_context(ctx)
        random.seed(42)
        result = comp.decide_pricing()
        new_price = result.get(gt.name, 100)
        assert new_price <= 100

    def test_decide_pricing_min_price_is_1(self, comp) -> None:
        """定价最小值为 1。"""
        gt = _get_goods_type("食品")

        ctx = _make_context(
            sell_orders={gt: 10},
            sold_quantities={gt: 0},
            current_prices={gt: 1},
        )
        comp.set_context(ctx)
        result = comp.decide_pricing()
        new_price = result.get(gt.name, 1)
        assert new_price >= 1

    def test_decide_pricing_no_sell_orders_skipped(self, comp) -> None:
        """无 sell_orders 的商品不定价。"""
        gt = _get_goods_type("食品")

        ctx = _make_context(
            sell_orders={},
            sold_quantities={},
            current_prices={gt: 100},
        )
        comp.set_context(ctx)
        result = comp.decide_pricing()
        assert len(result) == 0

    def test_inherits_base(self) -> None:
        """ClassicCompanyDecisionComponent 应继承 BaseCompanyDecisionComponent。"""
        assert issubclass(ClassicCompanyDecisionComponent, BaseCompanyDecisionComponent)


# ── 2.2: decide_investment_plan ──


class TestClassicInvestmentPlan:
    """2.2: decide_investment_plan 返回正确结构和计算。"""

    def test_returns_dict_with_three_keys(self, comp) -> None:
        """返回应包含 expansion, brand, tech 三个键。"""
        ctx = _make_context(cash=100000, last_revenue=10000)
        comp.set_context(ctx)
        result = comp.decide_investment_plan()
        assert isinstance(result, dict)
        assert "expansion" in result
        assert "brand" in result
        assert "tech" in result

    def test_brand_plan_calculation(self, comp) -> None:
        """品牌计划 = 营收 × 基础比例 × (1 + 营销意识 × 营销系数)。"""
        ctx = _make_context(cash=100000, last_revenue=10000)
        comp.marketing_awareness = 0.5
        comp.set_context(ctx)
        result = comp.decide_investment_plan()
        cfg = ConfigManager().section("decision")
        expected_brand = int(10000 * cfg.brand.base_ratio * (1 + 0.5 * cfg.brand.marketing_coeff))
        assert result["brand"] == expected_brand

    def test_tech_plan_calculation(self, comp) -> None:
        """科技计划 = 营收 × 基础比例 × (1 + 科技重视度 × 科技系数)。"""
        ctx = _make_context(cash=100000, last_revenue=10000)
        comp.tech_focus = 0.5
        comp.set_context(ctx)
        result = comp.decide_investment_plan()
        cfg = ConfigManager().section("decision")
        expected_tech = int(10000 * cfg.tech.base_ratio * (1 + 0.5 * cfg.tech.tech_coeff))
        assert result["tech"] == expected_tech

    def test_expansion_zero_without_factories(self, comp) -> None:
        """无工厂时扩产为 0。"""
        ctx = _make_context(factories={})
        comp.set_context(ctx)
        result = comp.decide_investment_plan()
        assert result["expansion"] == 0

    def test_expansion_with_factory_type_and_cash(self, comp) -> None:
        """有工厂类型且有现金时，高风险偏好可触发扩产。"""
        # 获取一个已注册的 FactoryType
        from entity.factory import FactoryType as FT
        # 使用 mock FactoryType 避免依赖具体注册
        mock_ft = MagicMock(spec=FT)
        mock_ft.build_cost = 5000
        mock_ft.maintenance_cost = 500

        built_factory = MagicMock()
        built_factory.is_built = True

        ctx = _make_context(
            cash=100000,
            last_revenue=10000,
            factories={mock_ft: [built_factory]},
        )
        comp.risk_appetite = 1.0
        comp.business_acumen = 1.0
        comp.set_context(ctx)
        result = comp.decide_investment_plan()
        assert result["expansion"] == 5000

    def test_investment_plan_updates_component_field(self, comp) -> None:
        """decide_investment_plan 应更新 investment_plan 属性。"""
        ctx = _make_context(cash=100000, last_revenue=10000)
        comp.set_context(ctx)
        result = comp.decide_investment_plan()
        assert comp.investment_plan == result


# ── 2.3: decide_budget_allocation, make_purchase_sort_key, decide_loan_needs ──


class TestClassicBudgetAllocation:
    """2.3: decide_budget_allocation 返回实际分配金额。"""

    def test_full_allocation_when_cash_sufficient(self, comp) -> None:
        """现金充足时，全额分配。"""
        from entity.factory import FactoryType as FT
        mock_ft = MagicMock(spec=FT)
        mock_ft.build_cost = 5000
        mock_ft.maintenance_cost = 500
        built_factory = MagicMock()
        built_factory.is_built = True

        ctx = _make_context(
            cash=100000,
            last_revenue=10000,
            factories={mock_ft: [built_factory]},
        )
        comp.risk_appetite = 1.0
        comp.business_acumen = 1.0
        comp.set_context(ctx)
        plan = comp.decide_investment_plan()
        plan_total = sum(plan.values())
        assert plan_total > 0, "investment plan should be non-zero with factories and revenue"

        allocation = comp.decide_budget_allocation()
        assert sum(allocation.values()) == plan_total

    def test_partial_allocation_when_cash_insufficient(self, comp) -> None:
        """现金不足时，按比例分配。"""
        from entity.factory import FactoryType as FT
        mock_ft = MagicMock(spec=FT)
        mock_ft.build_cost = 5000
        mock_ft.maintenance_cost = 500
        built_factory = MagicMock()
        built_factory.is_built = True

        ctx = _make_context(
            cash=100,
            last_revenue=10000,
            factories={mock_ft: [built_factory]},
        )
        comp.risk_appetite = 1.0
        comp.business_acumen = 1.0
        comp.set_context(ctx)
        plan = comp.decide_investment_plan()
        assert sum(plan.values()) > 0, "investment plan should be non-zero with factories and revenue"

        allocation = comp.decide_budget_allocation()
        assert sum(allocation.values()) <= 100


class TestClassicPurchaseSortKey:
    """2.3: make_purchase_sort_key 返回 Callable。"""

    def test_returns_callable(self, comp) -> None:
        """make_purchase_sort_key 应返回 Callable。"""
        ctx = _make_context()
        comp.set_context(ctx)
        result = comp.make_purchase_sort_key()
        assert callable(result)

    def test_sort_key_returns_float(self, comp) -> None:
        """排序函数应返回 float。"""
        gt = _get_goods_type("食品")

        ctx = _make_context()
        comp.set_context(ctx)
        sort_key = comp.make_purchase_sort_key()

        batch = GoodsBatch(goods_type=gt, quantity=10, quality=0.5, brand_value=10)
        order = SellOrder(seller=Entity(), batch=batch, price=50)
        score = sort_key(order)
        assert isinstance(score, float)

    def test_higher_marketing_prefers_brand(self, comp) -> None:
        """高营销意识偏好品牌值高的供应商。"""
        gt = _get_goods_type("食品")

        comp.marketing_awareness = 0.9
        comp.price_sensitivity = 0.1
        ctx = _make_context()
        comp.set_context(ctx)
        sort_key = comp.make_purchase_sort_key()

        batch_low_brand = GoodsBatch(goods_type=gt, quantity=10, quality=0.5, brand_value=5)
        batch_high_brand = GoodsBatch(goods_type=gt, quantity=10, quality=0.5, brand_value=50)
        order_low = SellOrder(seller=Entity(), batch=batch_low_brand, price=50)
        order_high = SellOrder(seller=Entity(), batch=batch_high_brand, price=50)

        assert sort_key(order_high) > sort_key(order_low)


class TestClassicLoanNeeds:
    """2.3: decide_loan_needs 返回 (amount, max_rate)。"""

    def test_returns_tuple(self, comp) -> None:
        """decide_loan_needs 应返回 tuple[int, int]。"""
        ctx = _make_context(cash=100, last_revenue=10000)
        comp.set_context(ctx)
        result = comp.decide_loan_needs()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)

    def test_no_loan_when_cash_sufficient(self, comp) -> None:
        """现金充足时贷款需求为 0。"""
        ctx = _make_context(cash=1000000, last_revenue=10000)
        comp.set_context(ctx)
        plan = comp.decide_investment_plan()
        amount, _ = comp.decide_loan_needs()
        assert amount == 0

    def test_loan_needed_when_cash_insufficient(self, comp) -> None:
        """现金不足时有贷款需求。"""
        from entity.factory import FactoryType as FT
        mock_ft = MagicMock(spec=FT)
        mock_ft.build_cost = 5000
        mock_ft.maintenance_cost = 500
        built_factory = MagicMock()
        built_factory.is_built = True

        ctx = _make_context(
            cash=0,
            last_revenue=10000,
            factories={mock_ft: [built_factory]},
        )
        comp.risk_appetite = 1.0
        comp.business_acumen = 1.0
        comp.set_context(ctx)
        plan = comp.decide_investment_plan()
        assert sum(plan.values()) > 0, "investment plan should be non-zero with factories and revenue"

        amount, _ = comp.decide_loan_needs()
        assert amount > 0

    def test_loan_amount_non_negative(self, comp) -> None:
        """贷款金额不应为负。"""
        ctx = _make_context(cash=1000000, last_revenue=10000)
        comp.set_context(ctx)
        amount, _ = comp.decide_loan_needs()
        assert amount >= 0

    def test_max_rate_decreases_with_risk_appetite(self, comp) -> None:
        """风险偏好越高，max_rate 越低。"""
        ctx = _make_context(cash=0, last_revenue=10000)
        comp.risk_appetite = 0.2
        comp.set_context(ctx)
        comp.decide_investment_plan()
        _, rate_low_risk = comp.decide_loan_needs()

        comp.risk_appetite = 0.8
        comp.set_context(ctx)
        comp.decide_investment_plan()
        _, rate_high_risk = comp.decide_loan_needs()

        assert rate_high_risk < rate_low_risk


class TestClassicDecideWage:
    """3.2: decide_wage 返回 initial_wage 配置值。"""

    def test_decide_wage_returns_int(self, comp) -> None:
        """decide_wage 应返回 int。"""
        ctx = _make_context()
        ctx["company"]["initial_wage"] = 10
        comp.set_context(ctx)
        result = comp.decide_wage()
        assert isinstance(result, int)

    def test_decide_wage_returns_initial_wage(self, comp) -> None:
        """decide_wage 应返回 context 中的 initial_wage。"""
        ctx = _make_context()
        ctx["company"]["initial_wage"] = 15
        comp.set_context(ctx)
        result = comp.decide_wage()
        assert result == 15
