"""MetricComponent 单元测试。"""

from __future__ import annotations

import pytest

from component.metric_component import MetricComponent, RoundSnapshot
from core.entity import Entity
from entity.folk import DemandFeedbackParams
from entity.goods import GoodsType

_DEFAULT_DEMAND_FEEDBACK = DemandFeedbackParams(
    savings_target_ratio=5.0,
    max_adjustment=0.15,
    sensitivity=1.0,
    min_multiplier=0.3,
    max_multiplier=2.0,
)


class TestMetricComponentInit:
    """MetricComponent 初始化测试。"""

    def test_inherits_base_component(self) -> None:
        from component.base_component import BaseComponent

        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert isinstance(mc, BaseComponent)

    def test_last_sell_orders_init_empty(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert mc.last_sell_orders == {}

    def test_last_sold_quantities_init_empty(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert mc.last_sold_quantities == {}

    def test_last_revenue_init_zero(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert mc.last_revenue == 0

    def test_last_avg_buy_prices_init_empty(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert mc.last_avg_buy_prices == {}

    def test_cumulative_revenue_init_zero(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert mc.cumulative_revenue == 0

    def test_cumulative_brand_spend_init_zero(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert mc.cumulative_brand_spend == 0

    def test_cumulative_tech_spend_init_zero(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert mc.cumulative_tech_spend == 0

    def test_cumulative_expansion_spend_init_zero(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert mc.cumulative_expansion_spend == 0

    def test_round_history_init_empty(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        assert mc.round_history == []


class TestRoundSnapshot:
    """RoundSnapshot 数据结构测试。"""

    def test_is_dataclass(self) -> None:
        import dataclasses
        assert dataclasses.is_dataclass(RoundSnapshot)

    def test_required_round_number(self) -> None:
        snap = RoundSnapshot(round_number=1)
        assert snap.round_number == 1

    def test_defaults(self) -> None:
        snap = RoundSnapshot(round_number=1)
        assert snap.cash == 0
        assert snap.revenue == 0
        assert snap.sell_orders == {}
        assert snap.sold_quantities == {}
        assert snap.prices == {}
        assert snap.brand_values == {}
        assert snap.tech_values == {}
        assert snap.investment_plan == {}
        assert snap.actual_investment == {}

    def test_custom_values(self) -> None:
        snap = RoundSnapshot(round_number=3, cash=1000, revenue=500)
        assert snap.round_number == 3
        assert snap.cash == 1000
        assert snap.revenue == 500

    def test_add_snapshot(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        snap = RoundSnapshot(round_number=1, cash=100)
        mc.add_snapshot(snap)
        assert len(mc.round_history) == 1
        assert mc.round_history[0].round_number == 1
        assert mc.round_history[0].cash == 100

    def test_add_multiple_snapshots(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        mc.add_snapshot(RoundSnapshot(round_number=1))
        mc.add_snapshot(RoundSnapshot(round_number=2))
        mc.add_snapshot(RoundSnapshot(round_number=3))
        assert len(mc.round_history) == 3
        assert [s.round_number for s in mc.round_history] == [1, 2, 3]


class TestEntityMounting:
    """实体挂载 MetricComponent 测试。"""

    def test_company_has_metric_component(self) -> None:
        from entity.company.company import Company
        company = Company(name="test_company")
        mc = company.get_component(MetricComponent)
        assert mc is not None
        assert isinstance(mc, MetricComponent)

    def test_folk_has_metric_component(self) -> None:
        from entity.folk import Folk
        folk = Folk(
            name="test_folk",
            population=100,
            w_quality=0.5,
            w_brand=0.3,
            w_price=0.2,
            spending_flow={"tech": 0.5, "brand": 0.3, "maintenance": 0.2},
            base_demands={},
            labor_participation_rate=0.6,
            labor_points_per_capita=1.0,
            demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
        )
        mc = folk.get_component(MetricComponent)
        assert mc is not None
        assert isinstance(mc, MetricComponent)

    def test_bank_has_metric_component(self) -> None:
        from entity.bank import Bank
        bank = Bank("test_bank")
        mc = bank.get_component(MetricComponent)
        assert mc is not None
        assert isinstance(mc, MetricComponent)


class TestResetRound:
    """MetricComponent.reset_round 测试。"""

    def test_reset_round_clears_sell_orders(self) -> None:
        gt = GoodsType(name="test", base_price=100)
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        mc.last_sell_orders[gt] = 50
        mc.reset_round()
        assert mc.last_sell_orders == {}

    def test_reset_round_clears_sold_quantities(self) -> None:
        gt = GoodsType(name="test", base_price=100)
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        mc.last_sold_quantities[gt] = 30
        mc.reset_round()
        assert mc.last_sold_quantities == {}

    def test_reset_round_clears_revenue(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        mc.last_revenue = 5000
        mc.reset_round()
        assert mc.last_revenue == 0

    def test_reset_round_preserves_history(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        mc.add_snapshot(RoundSnapshot(round_number=1))
        mc.last_revenue = 5000
        mc.reset_round()
        assert len(mc.round_history) == 1

    def test_reset_round_preserves_cumulative(self) -> None:
        entity = Entity("test")
        entity.init_component(MetricComponent)
        mc = entity.get_component(MetricComponent)
        mc.cumulative_revenue = 10000
        mc.reset_round()
        assert mc.cumulative_revenue == 10000
