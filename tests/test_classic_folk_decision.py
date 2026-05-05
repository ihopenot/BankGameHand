"""ClassicFolkDecisionComponent 支出决策测试。"""

import pytest

from component.decision.folk.classic import ClassicFolkDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.storage_component import StorageComponent
from core.entity import Entity
from entity.goods import GoodsType


# 创建测试用 GoodsType（不依赖配置加载）
GT_FOOD = GoodsType(name="食品", base_price=50)
GT_CLOTH = GoodsType(name="服装", base_price=200)
GT_PHONE = GoodsType(name="手机", base_price=3000)


@pytest.fixture(autouse=True)
def _clear_components():
    ClassicFolkDecisionComponent.components.clear()
    yield
    ClassicFolkDecisionComponent.components.clear()


def _make_folk_entity(population=6000, w_quality=0.4, w_brand=0.05, w_price=0.55):
    """创建一个带 ClassicFolkDecisionComponent 的模拟 Folk 实体。"""
    entity = Entity("test")
    entity.population = population
    entity.w_quality = w_quality
    entity.w_brand = w_brand
    entity.w_price = w_price
    entity.demand_multiplier = 1.0
    entity.last_spending = 0
    entity.base_demands = {
        GT_FOOD: {"per_capita": 10, "sensitivity": 0.1},
        GT_CLOTH: {"per_capita": 1, "sensitivity": 0.5},
        GT_PHONE: {"per_capita": 0, "sensitivity": 0.8},
    }
    comp = entity.init_component(ClassicFolkDecisionComponent)
    entity.init_component(LedgerComponent)
    entity.init_component(StorageComponent)
    entity.init_component(MetricComponent)
    return entity, comp


class TestClassicFolkDecisionDecideSpending:
    """ClassicFolkDecisionComponent.decide_spending() 测试。"""

    def test_returns_budget_and_demand_per_goods_type(self) -> None:
        """decide_spending() 返回每个商品类型的 budget 和 demand。"""
        entity, comp = _make_folk_entity()
        context = {
            "economy_cycle_index": 1.0,
            "reference_prices": {
                "食品": 50,
                "服装": 200,
                "手机": 3000,
            },
        }
        comp.set_context(context)
        result = comp.decide_spending()

        assert isinstance(result, dict)
        for gt_name in ["食品", "服装"]:
            assert gt_name in result
            assert "budget" in result[gt_name]
            assert "demand" in result[gt_name]
            assert isinstance(result[gt_name]["budget"], int)
            assert isinstance(result[gt_name]["demand"], int)

    def test_demand_formula(self) -> None:
        """demand = population * per_capita * demand_multiplier（默认1.0）。"""
        entity, comp = _make_folk_entity(population=6000)
        context = {
            "economy_cycle_index": 1.0,
            "reference_prices": {"食品": 50, "服装": 200, "手机": 3000},
        }
        comp.set_context(context)
        result = comp.decide_spending()

        # 食品: population=6000, per_capita=10, demand_multiplier=1.0
        # demand = 6000 * 10 * 1.0 = 60000
        assert result["食品"]["demand"] == 60000

        # 服装: per_capita=1, demand_multiplier=1.0
        # demand = 6000 * 1 * 1.0 = 6000
        assert result["服装"]["demand"] == 6000

    def test_zero_per_capita_means_zero_budget_and_demand(self) -> None:
        """per_capita=0 时 budget=0, demand=0。"""
        entity, comp = _make_folk_entity()
        context = {
            "economy_cycle_index": 1.0,
            "reference_prices": {"食品": 50, "服装": 200, "手机": 3000},
        }
        comp.set_context(context)
        result = comp.decide_spending()

        # 手机 per_capita=0
        assert result["手机"]["demand"] == 0
        assert result["手机"]["budget"] == 0

    def test_budget_formula_with_exact_values(self) -> None:
        """budget = demand * reference_price * spending_tendency，用精确值验证。"""
        # w_quality=0.4 + w_brand=0.05 + w_price=0.55 = spending_tendency 1.0
        entity, comp = _make_folk_entity(population=6000)
        context = {
            "economy_cycle_index": 1.0,
            "reference_prices": {"食品": 50, "服装": 200, "手机": 3000},
        }
        comp.set_context(context)
        result = comp.decide_spending()

        # 食品: demand=60000, reference_price=50, spending_tendency=1.0
        # budget = int(60000 * 50 * 1.0) = 3000000
        assert result["食品"]["budget"] == 3000000

        # 服装: demand=6000, reference_price=200, spending_tendency=1.0
        # budget = int(6000 * 200 * 1.0) = 1200000
        assert result["服装"]["budget"] == 1200000

    def test_budget_with_non_unit_spending_tendency(self) -> None:
        """非单位 spending_tendency 正确乘入 budget。"""
        # w_quality=0.2 + w_brand=0.1 + w_price=0.3 = spending_tendency 0.6
        entity, comp = _make_folk_entity(
            population=6000, w_quality=0.2, w_brand=0.1, w_price=0.3
        )
        context = {
            "economy_cycle_index": 1.0,
            "reference_prices": {"食品": 50, "服装": 200, "手机": 3000},
        }
        comp.set_context(context)
        result = comp.decide_spending()

        # 食品: demand=60000, reference_price=50, spending_tendency=0.6
        # budget = int(60000 * 50 * 0.6) = 1800000
        assert result["食品"]["budget"] == 1800000

    def test_folk_w_attributes_used(self) -> None:
        """Folk 的 w_* 属性影响 spending_tendency。"""
        _, comp_low_brand = _make_folk_entity(w_brand=0.05, w_price=0.55)
        _, comp_high_brand = _make_folk_entity(w_brand=0.75, w_price=0.1)

        context = {
            "economy_cycle_index": 1.0,
            "reference_prices": {"食品": 50, "服装": 200, "手机": 3000},
        }
        comp_low_brand.set_context(context)
        comp_high_brand.set_context(context)

        result_low = comp_low_brand.decide_spending()
        result_high = comp_high_brand.decide_spending()

        assert result_low["食品"]["budget"] != result_high["食品"]["budget"]
