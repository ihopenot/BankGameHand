"""居民动态需求机制测试。"""

import math
from pathlib import Path
from unittest.mock import patch

import pytest

from core.config import ConfigManager
from entity.folk import DemandFeedbackParams
from entity.goods import GoodsType, load_goods_types

_DEFAULT_DEMAND_FEEDBACK = DemandFeedbackParams(
    savings_target_ratio=5.0,
    max_adjustment=0.15,
    sensitivity=1.0,
    min_multiplier=0.3,
    max_multiplier=2.0,
)


@pytest.fixture(autouse=True)
def _load_config():
    """确保配置和 GoodsType 已加载。"""
    ConfigManager._instance = None
    ConfigManager().load(str(Path(__file__).parent / "config_integration"))
    GoodsType.types.clear()
    load_goods_types()
    yield
    ConfigManager._instance = None


class TestFolkDemandAttributes:
    """Folk 实体应有 last_spending 和 demand_multiplier 属性。"""

    def test_folk_has_last_spending(self) -> None:
        from entity.folk import Folk
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
            demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
        )
        assert folk.last_spending == 0

    def test_folk_has_demand_multiplier(self) -> None:
        from entity.folk import Folk
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
            demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
        )
        assert folk.demand_multiplier == 1.0


class TestDemandMultiplierUpdate:
    """demand_multiplier 更新逻辑测试。"""

    def _make_folk(self, cash: int, last_spending: int, demand_multiplier: float = 1.0):
        from entity.folk import Folk
        from component.ledger_component import LedgerComponent
        gt = list(GoodsType.types.values())[0]
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={gt: {"per_capita": 1.0, "sensitivity": 0.5}},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
            demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
        )
        folk.last_spending = last_spending
        folk.demand_multiplier = demand_multiplier
        ledger = folk.get_component(LedgerComponent)
        ledger.cash = cash
        return folk

    def test_neutral_when_last_spending_zero(self) -> None:
        """last_spending=0 时不触发调整，demand_multiplier 保持不变。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=5000, last_spending=0)
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier == 1.0

    def test_increase_when_cash_abundant(self) -> None:
        """现金充裕(R > T)时 demand_multiplier 增加。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=10000, last_spending=1000)  # R=10, T=5 → deviation>0
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier > 1.0

    def test_decrease_when_cash_tight(self) -> None:
        """现金紧张(R < T)时 demand_multiplier 减少。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=2000, last_spending=1000)  # R=2, T=5 → deviation<0
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier < 1.0

    def test_clamp_max(self) -> None:
        """demand_multiplier 不超过 max_multiplier。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=100000, last_spending=100, demand_multiplier=1.9)
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier <= 2.0

    def test_clamp_min(self) -> None:
        """demand_multiplier 不低于 min_multiplier。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=100, last_spending=10000, demand_multiplier=0.35)
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier >= 0.3

    def test_equilibrium_no_change(self) -> None:
        """R == T 时 deviation=0，demand_multiplier 不变。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=5000, last_spending=1000)  # R=5, T=5 → deviation=0
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier == pytest.approx(1.0, abs=1e-10)


class TestEconomyCycleDecoupled:
    """经济周期不再直接影响居民需求。"""

    def _make_folk(self):
        from entity.folk import Folk
        from component.ledger_component import LedgerComponent
        gt = list(GoodsType.types.values())[0]
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={gt: {"per_capita": 1.0, "sensitivity": 0.8}},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
            demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
        )
        ledger = folk.get_component(LedgerComponent)
        ledger.cash = 100000
        return folk

    def test_demand_same_regardless_of_economy_index(self) -> None:
        """不同经济周期值应产生相同需求（因为 demand_multiplier 不受 economy_index 影响）。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent

        folk1 = self._make_folk()
        dc1 = folk1.get_component(ClassicFolkDecisionComponent)
        dc1.set_context({"economy_cycle_index": 0.5, "reference_prices": {}})
        plan1 = dc1.decide_spending()

        folk2 = self._make_folk()
        dc2 = folk2.get_component(ClassicFolkDecisionComponent)
        dc2.set_context({"economy_cycle_index": -0.5, "reference_prices": {}})
        plan2 = dc2.decide_spending()

        gt_name = list(GoodsType.types.values())[0].name
        assert plan1[gt_name]["demand"] == plan2[gt_name]["demand"]
