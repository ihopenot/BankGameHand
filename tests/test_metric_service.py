"""MetricService 单元测试。"""

from __future__ import annotations

from component.decision.company.classic import ClassicCompanyDecisionComponent
from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from entity.bank import Bank
from entity.company.company import Company
from entity.factory import Factory, FactoryType, Recipe
from entity.folk import Folk
from entity.goods import GoodsType
from system.metric_service import MetricService


def _make_company(gt: GoodsType, cash: int = 10000) -> Company:
    recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt,
                    output_quantity=10, tech_quality_weight=1.0)
    ft = FactoryType(recipe=recipe, base_production=100, build_cost=1000,
                     maintenance_cost=50, build_time=1)
    company = Company(name="test_company")
    pc = company.get_component(ProductorComponent)
    pc.factories[ft] = [Factory(ft, build_remaining=0)]
    pc.init_prices()
    company.get_component(LedgerComponent).cash = cash
    return company


class TestSnapshotPhase:
    """MetricService.snapshot_phase 测试。"""

    def test_company_snapshot_created(self) -> None:
        gt = GoodsType(name="chip", base_price=500)
        company = _make_company(gt, cash=5000)
        mc = company.get_component(MetricComponent)
        mc.last_revenue = 1000
        mc.last_sell_orders[gt] = 50
        mc.last_sold_quantities[gt] = 30

        service = MetricService()
        service.snapshot_phase(round_number=1)

        assert len(mc.round_history) == 1
        snap = mc.round_history[0]
        assert snap.round_number == 1
        assert snap.cash == 5000
        assert snap.revenue == 1000
        assert snap.sell_orders[gt] == 50
        assert snap.sold_quantities[gt] == 30

    def test_company_snapshot_includes_prices(self) -> None:
        gt = GoodsType(name="chip", base_price=500)
        company = _make_company(gt)
        pc = company.get_component(ProductorComponent)
        pc.prices[gt] = 600

        service = MetricService()
        service.snapshot_phase(round_number=1)

        mc = company.get_component(MetricComponent)
        snap = mc.round_history[0]
        assert snap.prices[gt] == 600

    def test_folk_snapshot_created(self) -> None:
        folk = Folk(name="test_folk", population=100, w_quality=0.5, w_brand=0.3, w_price=0.2,
                    spending_flow={"tech": 0.5, "brand": 0.3, "maintenance": 0.2},
                    base_demands={})
        folk.get_component(LedgerComponent).cash = 8000

        service = MetricService()
        service.snapshot_phase(round_number=2)

        mc = folk.get_component(MetricComponent)
        assert len(mc.round_history) == 1
        assert mc.round_history[0].round_number == 2
        assert mc.round_history[0].cash == 8000

    def test_bank_snapshot_created(self) -> None:
        bank = Bank()
        bank.get_component(LedgerComponent).cash = 200000

        service = MetricService()
        service.snapshot_phase(round_number=3)

        mc = bank.get_component(MetricComponent)
        assert len(mc.round_history) == 1
        assert mc.round_history[0].round_number == 3
        assert mc.round_history[0].cash == 200000

    def test_multiple_rounds(self) -> None:
        gt = GoodsType(name="chip", base_price=500)
        company = _make_company(gt, cash=5000)

        service = MetricService()
        service.snapshot_phase(round_number=1)
        service.snapshot_phase(round_number=2)

        mc = company.get_component(MetricComponent)
        assert len(mc.round_history) == 2
        assert mc.round_history[0].round_number == 1
        assert mc.round_history[1].round_number == 2


class TestCumulativeCounters:
    """累计计数器测试。"""

    def test_cumulative_revenue_after_snapshot(self) -> None:
        gt = GoodsType(name="chip", base_price=500)
        company = _make_company(gt)
        mc = company.get_component(MetricComponent)
        mc.last_revenue = 3000

        service = MetricService()
        service.snapshot_phase(round_number=1)

        assert mc.cumulative_revenue == 3000

    def test_cumulative_revenue_accumulates(self) -> None:
        gt = GoodsType(name="chip", base_price=500)
        company = _make_company(gt)
        mc = company.get_component(MetricComponent)

        service = MetricService()

        mc.last_revenue = 3000
        service.snapshot_phase(round_number=1)
        mc.last_revenue = 2000
        service.snapshot_phase(round_number=2)

        assert mc.cumulative_revenue == 5000
