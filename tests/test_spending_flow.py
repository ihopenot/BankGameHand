"""Spending flow 测试：企业支出分流到居民。"""

import pytest

from component.ledger_component import LedgerComponent
from core.config import ConfigManager
from entity.folk import Folk


@pytest.fixture(autouse=True)
def _load_config():
    ConfigManager._instance = None
    ConfigManager().load()
    yield
    ConfigManager._instance = None


def _make_folk_entities():
    """创建 Folk 实体列表（匹配 folk.yaml 中的 3 个组）。"""
    folks = [
        Folk(
            name="folk_0",
            population=6000,
            w_quality=0.4,
            w_brand=0.05,
            w_price=0.55,
            spending_flow={"tech": 0.6, "brand": 0.4, "maintenance": 0.5},
            base_demands={},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        ),
        Folk(
            name="folk_1",
            population=3000,
            w_quality=0.35,
            w_brand=0.35,
            w_price=0.3,
            spending_flow={"tech": 0.3, "brand": 0.4, "maintenance": 0.35},
            base_demands={},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        ),
        Folk(
            name="folk_2",
            population=1000,
            w_quality=0.15,
            w_brand=0.75,
            w_price=0.1,
            spending_flow={"tech": 0.1, "brand": 0.2, "maintenance": 0.15},
            base_demands={},
            labor_participation_rate=0.6, labor_points_per_capita=1.0,
        ),
    ]
    return folks


class TestSpendingFlowDistribution:
    """支出分流分配逻辑测试。"""

    def test_tech_spending_distributed_by_ratio(self) -> None:
        """企业 tech 支出按 folk.spending_flow 比例分配到各 Folk 组。"""
        from system.decision_service import DecisionService

        folks = _make_folk_entities()
        ds = DecisionService()

        # tech_budget=10000, 全部流向居民
        # 低收入: 10000 * 0.6 = 6000
        # 中等收入: 10000 * 0.3 = 3000
        # 高收入: 10000 * 0.1 = 1000
        ds.distribute_spending_to_folks("tech", 10000, folks)

        assert folks[0].get_component(LedgerComponent).cash == 6000
        assert folks[1].get_component(LedgerComponent).cash == 3000
        assert folks[2].get_component(LedgerComponent).cash == 1000

    def test_brand_spending_distributed_by_ratio(self) -> None:
        """企业 brand 支出按 folk.spending_flow 比例分配到各 Folk 组。"""
        from system.decision_service import DecisionService

        folks = _make_folk_entities()
        ds = DecisionService()

        # brand_budget=10000, 全部流向居民
        # 低收入: 10000 * 0.4 = 4000
        # 中等收入: 10000 * 0.4 = 4000
        # 高收入: 10000 * 0.2 = 2000
        ds.distribute_spending_to_folks("brand", 10000, folks)

        assert folks[0].get_component(LedgerComponent).cash == 4000
        assert folks[1].get_component(LedgerComponent).cash == 4000
        assert folks[2].get_component(LedgerComponent).cash == 2000

    def test_maintenance_cost_deducted_and_distributed(self) -> None:
        """维护费用全部分配到 Folk 组。"""
        from system.decision_service import DecisionService

        folks = _make_folk_entities()
        ds = DecisionService()

        # maintenance_amount=500, 全部流向居民
        # 低收入: 500 * 0.5 = 250
        # 中等收入: 500 * 0.35 = 175
        # 高收入: 500 * 0.15 = 75
        ds.distribute_spending_to_folks("maintenance", 500, folks)

        assert folks[0].get_component(LedgerComponent).cash == 250
        assert folks[1].get_component(LedgerComponent).cash == 175
        assert folks[2].get_component(LedgerComponent).cash == 75

    def test_zero_amount_means_no_flow(self) -> None:
        """金额为 0 时不分流。"""
        from system.decision_service import DecisionService

        folks = _make_folk_entities()
        ds = DecisionService()

        ds.distribute_spending_to_folks("tech", 0, folks)

        assert folks[0].get_component(LedgerComponent).cash == 0
        assert folks[1].get_component(LedgerComponent).cash == 0
        assert folks[2].get_component(LedgerComponent).cash == 0
