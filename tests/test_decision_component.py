"""Test that Company uses ClassicCompanyDecisionComponent instead of the old DecisionComponent."""

import pytest

from component.base_component import BaseComponent
from component.decision.company.base import BaseCompanyDecisionComponent
from component.decision.company.classic import ClassicCompanyDecisionComponent
from core.entity import Entity
from entity.company.company import Company


class TestCompanyUsesClassicCompanyDecision:
    """Company should mount ClassicCompanyDecisionComponent."""

    def setup_method(self) -> None:
        ClassicCompanyDecisionComponent.components.clear()

    def teardown_method(self) -> None:
        ClassicCompanyDecisionComponent.components.clear()

    def test_company_has_classic_decision_component(self) -> None:
        """Company 创建后可手动挂载 ClassicCompanyDecisionComponent。"""
        company = Company(name="test_company")
        company.init_component(ClassicCompanyDecisionComponent)
        dc = company.get_component(ClassicCompanyDecisionComponent)
        assert dc is not None
        assert isinstance(dc, ClassicCompanyDecisionComponent)

    def test_classic_inherits_base_company_decision(self) -> None:
        assert issubclass(ClassicCompanyDecisionComponent, BaseCompanyDecisionComponent)

    def test_classic_inherits_base_component(self) -> None:
        assert issubclass(ClassicCompanyDecisionComponent, BaseComponent)

    def test_has_six_traits(self) -> None:
        """ClassicCompanyDecisionComponent 应有 6 维 CEO 特质。"""
        entity = Entity()
        dc = entity.init_component(ClassicCompanyDecisionComponent)
        assert hasattr(dc, "business_acumen")
        assert hasattr(dc, "risk_appetite")
        assert hasattr(dc, "profit_focus")
        assert hasattr(dc, "marketing_awareness")
        assert hasattr(dc, "tech_focus")
        assert hasattr(dc, "price_sensitivity")

    def test_traits_are_float(self) -> None:
        entity = Entity()
        dc = entity.init_component(ClassicCompanyDecisionComponent)
        for attr in [
            "business_acumen",
            "risk_appetite",
            "profit_focus",
            "marketing_awareness",
            "tech_focus",
            "price_sensitivity",
        ]:
            assert isinstance(getattr(dc, attr), float)

    def test_traits_in_range(self) -> None:
        """CEO 特质应在 [0, 1] 范围。"""
        entity = Entity()
        dc = entity.init_component(ClassicCompanyDecisionComponent)
        for attr in [
            "business_acumen",
            "risk_appetite",
            "profit_focus",
            "marketing_awareness",
            "tech_focus",
            "price_sensitivity",
        ]:
            val = getattr(dc, attr)
            assert 0.0 <= val <= 1.0, f"{attr}={val} 超出 [0,1] 范围"

    def test_company_traits_random(self) -> None:
        """多次创建 Company，CEO 特质应有随机性（不全相同）。"""
        companies = []
        for i in range(20):
            c = Company(name=f"company_{i}")
            c.init_component(ClassicCompanyDecisionComponent)
            companies.append(c)
        acumen_values = [
            c.get_component(ClassicCompanyDecisionComponent).business_acumen
            for c in companies
        ]
        assert len(set(acumen_values)) > 1

    def test_has_investment_plan(self) -> None:
        entity = Entity()
        dc = entity.init_component(ClassicCompanyDecisionComponent)
        assert hasattr(dc, "investment_plan")
        assert isinstance(dc.investment_plan, dict)
        assert dc.investment_plan == {}

    def test_component_tracking(self) -> None:
        entity = Entity()
        dc = entity.init_component(ClassicCompanyDecisionComponent)
        assert dc in ClassicCompanyDecisionComponent.components

    def test_destroy_cleanup(self) -> None:
        entity = Entity()
        dc = entity.init_component(ClassicCompanyDecisionComponent)
        entity.destroy()
        assert dc not in ClassicCompanyDecisionComponent.components
