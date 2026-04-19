"""DecisionComponent 单元测试。"""

import pytest

from component.base_component import BaseComponent
from component.decision_component import DecisionComponent
from core.entity import Entity
from entity.company.company import Company


class TestDecisionComponentInit:
    """1.1: DecisionComponent 基础结构测试。"""

    def setup_method(self) -> None:
        DecisionComponent.components.clear()

    def teardown_method(self) -> None:
        DecisionComponent.components.clear()

    def test_inherits_base_component(self) -> None:
        assert issubclass(DecisionComponent, BaseComponent)

    def test_init_via_entity(self) -> None:
        entity = Entity()
        dc = entity.init_component(DecisionComponent)
        assert isinstance(dc, DecisionComponent)
        assert dc.outer is entity

    def test_has_five_traits(self) -> None:
        """DecisionComponent 应有 5 维 CEO 特质。"""
        entity = Entity()
        dc = entity.init_component(DecisionComponent)
        assert hasattr(dc, "business_acumen")
        assert hasattr(dc, "risk_appetite")
        assert hasattr(dc, "profit_focus")
        assert hasattr(dc, "marketing_awareness")
        assert hasattr(dc, "tech_focus")

    def test_traits_are_float(self) -> None:
        entity = Entity()
        dc = entity.init_component(DecisionComponent)
        for attr in [
            "business_acumen",
            "risk_appetite",
            "profit_focus",
            "marketing_awareness",
            "tech_focus",
        ]:
            assert isinstance(getattr(dc, attr), float)

    def test_traits_in_range(self) -> None:
        """CEO 特质应在 [0, 1] 范围。"""
        entity = Entity()
        dc = entity.init_component(DecisionComponent)
        for attr in [
            "business_acumen",
            "risk_appetite",
            "profit_focus",
            "marketing_awareness",
            "tech_focus",
        ]:
            val = getattr(dc, attr)
            assert 0.0 <= val <= 1.0, f"{attr}={val} 超出 [0,1] 范围"

    def test_sales_tracking_moved_to_metric(self) -> None:
        """销售追踪字段已迁移到 MetricComponent。"""
        entity = Entity()
        dc = entity.init_component(DecisionComponent)
        assert not hasattr(dc, "last_sell_orders")
        assert not hasattr(dc, "last_sold_quantities")

    def test_revenue_tracking_moved_to_metric(self) -> None:
        """营收追踪字段已迁移到 MetricComponent。"""
        entity = Entity()
        dc = entity.init_component(DecisionComponent)
        assert not hasattr(dc, "last_revenue")

    def test_has_investment_plan(self) -> None:
        """DecisionComponent 应有投资计划表。"""
        entity = Entity()
        dc = entity.init_component(DecisionComponent)
        assert hasattr(dc, "investment_plan")
        assert isinstance(dc.investment_plan, dict)
        assert dc.investment_plan == {}

    def test_component_tracking(self) -> None:
        """创建后应注册到 components 列表。"""
        entity = Entity()
        dc = entity.init_component(DecisionComponent)
        assert dc in DecisionComponent.components

    def test_destroy_cleanup(self) -> None:
        entity = Entity()
        dc = entity.init_component(DecisionComponent)
        entity.destroy()
        assert dc not in DecisionComponent.components


class TestCompanyDecisionComponent:
    """1.2: Company 挂载 DecisionComponent 测试。"""

    def setup_method(self) -> None:
        DecisionComponent.components.clear()

    def teardown_method(self) -> None:
        DecisionComponent.components.clear()

    def test_company_has_decision_component(self) -> None:
        """Company 创建时应自动挂载 DecisionComponent。"""
        company = Company()
        dc = company.get_component(DecisionComponent)
        assert dc is not None
        assert isinstance(dc, DecisionComponent)

    def test_company_traits_random(self) -> None:
        """多次创建 Company，CEO 特质应有随机性（不全相同）。"""
        companies = [Company() for _ in range(20)]
        # 收集所有 business_acumen 值
        acumen_values = [
            c.get_component(DecisionComponent).business_acumen for c in companies
        ]
        # 20 个随机值不应全部相同
        assert len(set(acumen_values)) > 1

    def test_company_traits_all_in_range(self) -> None:
        """Company 的 CEO 特质应全部在 [0, 1] 范围。"""
        for _ in range(10):
            company = Company()
            dc = company.get_component(DecisionComponent)
            for attr in [
                "business_acumen",
                "risk_appetite",
                "profit_focus",
                "marketing_awareness",
                "tech_focus",
            ]:
                val = getattr(dc, attr)
                assert 0.0 <= val <= 1.0, f"{attr}={val} 超出 [0,1] 范围"
