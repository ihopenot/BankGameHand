"""LaborService 匹配逻辑测试。"""
from __future__ import annotations

import pytest

from entity.factory import Factory, FactoryType, Recipe
from entity.folk import DemandFeedbackParams, Folk
from entity.goods import GoodsType
from system.labor_service import LaborService

_DEFAULT_DEMAND_FEEDBACK = DemandFeedbackParams(
    savings_target_ratio=5.0,
    max_adjustment=0.15,
    sensitivity=1.0,
    min_multiplier=0.3,
    max_multiplier=2.0,
)

_DEFAULT_DEMAND_FEEDBACK = DemandFeedbackParams(
    savings_target_ratio=5.0,
    max_adjustment=0.15,
    sensitivity=1.0,
    min_multiplier=0.3,
    max_multiplier=2.0,
)


def _make_folk(population: int, participation_rate: float, points_per_capita: float = 1.0) -> Folk:
    return Folk(
        name=f"folk_{population}",
        population=population,
        w_quality=0.5,
        w_brand=0.5,
        w_price=0.0,
        spending_flow={},
        base_demands={},
        labor_participation_rate=participation_rate,
        labor_points_per_capita=points_per_capita,
        demand_feedback=_DEFAULT_DEMAND_FEEDBACK,
    )


def _make_company(name: str, wage: int, labor_demand: int):
    from core.entity import Entity
    from component.productor_component import ProductorComponent

    gt = GoodsType(name=f"goods_{name}", base_price=100)
    recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt,
                    output_quantity=100, tech_quality_weight=1.0)
    ft = FactoryType(recipe=recipe, labor_demand=labor_demand,
                     build_cost=10000, maintenance_cost=500, build_time=0)
    from component.metric_component import MetricComponent
    company = Entity("test")
    company.name = name
    company.wage = wage
    pc = company.init_component(ProductorComponent)
    company.init_component(MetricComponent)
    pc.factories[ft].append(Factory(factory_type=ft, build_remaining=0))
    return company


class TestLaborServiceMatch:
    def test_returns_hire_records(self):
        """match() 返回雇佣关系列表。"""
        folk = _make_folk(1000, 0.6)  # labor_supply = 600
        company = _make_company("A", 10, 400)
        service = LaborService()
        records = service.match([company], [folk])
        assert isinstance(records, list)
        assert len(records) > 0
        folk_r, company_r, points = records[0]
        assert folk_r is folk
        assert company_r is company
        assert points > 0

    def test_high_wage_filled_first(self):
        """高工资企业优先被填满。"""
        folk = _make_folk(1000, 0.6)  # 600 点
        high = _make_company("High", 20, 400)
        low = _make_company("Low", 10, 400)
        service = LaborService()
        records = service.match([high, low], [folk])

        hired = {}
        for _, company, pts in records:
            hired[company.name] = hired.get(company.name, 0) + pts

        assert hired.get("High", 0) == 400   # 满员
        assert hired.get("Low", 0) == 200    # 剩余 200

    def test_same_wage_split_proportionally(self):
        """同工资企业，劳动力不足时按需求比例均分。"""
        folk = _make_folk(600, 1.0, points_per_capita=1.0)  # 600 点
        a = _make_company("A", 10, 300)  # 需求 300
        b = _make_company("B", 10, 600)  # 需求 600，总需 900 > 600
        service = LaborService()
        records = service.match([a, b], [folk])

        hired = {}
        for _, company, pts in records:
            hired[company.name] = hired.get(company.name, 0) + pts

        # 600 点按 300:600 = 1:2 分配 → A≈200, B≈400
        assert hired.get("A", 0) == pytest.approx(200, abs=2)
        assert hired.get("B", 0) == pytest.approx(400, abs=2)

    def test_high_ppc_folk_hired_first(self):
        """高 labor_points_per_capita 的居民优先受雇。"""
        folk_high = _make_folk(100, 1.0, points_per_capita=2.0)  # supply=200
        folk_low = _make_folk(1000, 1.0, points_per_capita=1.0)  # supply=1000
        company = _make_company("X", 10, 150)  # 只需 150 点
        service = LaborService()
        records = service.match([company], [folk_high, folk_low])

        hired_by_folk = {}
        for folk, _, pts in records:
            key = folk.labor_points_per_capita
            hired_by_folk[key] = hired_by_folk.get(key, 0) + pts

        # folk_high 先受雇，供给 200 > 需求 150，应全由 folk_high 填满
        assert hired_by_folk.get(2.0, 0) == 150
        assert hired_by_folk.get(1.0, 0) == 0

    def test_multiple_folks_pooled_within_batch(self):
        """同 ppc 的多个 Folk 按 labor_supply 比例分配。"""
        folk_a = _make_folk(600, 1.0, points_per_capita=1.0)  # supply=600
        folk_b = _make_folk(400, 1.0, points_per_capita=1.0)  # supply=400
        company = _make_company("X", 10, 500)
        service = LaborService()
        records = service.match([company], [folk_a, folk_b])

        hired_a = sum(pts for f, _, pts in records if f is folk_a)
        hired_b = sum(pts for f, _, pts in records if f is folk_b)

        # 按 600:400 比例分配 500 点
        assert hired_a == pytest.approx(300, abs=2)
        assert hired_b == pytest.approx(200, abs=2)


class TestLaborServiceApply:
    def test_apply_sets_hired_labor_points(self):
        """apply() 将劳动力点数累加到 ProductorComponent。"""
        from component.ledger_component import LedgerComponent
        from component.productor_component import ProductorComponent

        folk = _make_folk(1000, 1.0, points_per_capita=1.0)
        folk.init_component(LedgerComponent)
        company = _make_company("X", 10, 200)
        from component.ledger_component import LedgerComponent as LC
        company.init_component(LC)

        service = LaborService()
        records = [(folk, company, 150)]
        service.apply([company], records)

        assert company.get_component(ProductorComponent).hired_labor_points == 150

    def test_apply_creates_wage_liability_per_folk(self):
        """apply() 对每条雇佣关系生成独立的工资负债。"""
        from component.ledger_component import LedgerComponent
        from core.types import LoanType

        folk_a = _make_folk(600, 1.0, points_per_capita=1.0)
        folk_b = _make_folk(400, 1.0, points_per_capita=2.0)
        folk_a.init_component(LedgerComponent)
        folk_b.init_component(LedgerComponent)

        company = _make_company("X", 10, 500)
        company.init_component(LedgerComponent)

        service = LaborService()
        records = [
            (folk_a, company, 300),  # 300 / 1.0 × 10 = 3000
            (folk_b, company, 200),  # 200 / 2.0 × 10 = 1000
        ]
        service.apply([company], records)

        ledger = company.get_component(LedgerComponent)
        payables = ledger.filter_loans(LoanType.TRADE_PAYABLE)
        total = sum(l.remaining for l in payables)
        assert total == 4000  # 3000 + 1000

    def test_apply_wage_uses_ppc(self):
        """工资按人口单位计算：labor_points / ppc × wage。"""
        from component.ledger_component import LedgerComponent
        from core.types import LoanType

        folk = _make_folk(100, 1.0, points_per_capita=2.0)
        folk.init_component(LedgerComponent)
        company = _make_company("X", 20, 100)
        company.init_component(LedgerComponent)

        service = LaborService()
        records = [(folk, company, 60)]  # 60 / 2.0 × 20 = 600
        service.apply([company], records)

        ledger = company.get_component(LedgerComponent)
        payables = ledger.filter_loans(LoanType.TRADE_PAYABLE)
        assert sum(l.remaining for l in payables) == 600
