"""BaseCompanyDecisionComponent 抽象基类测试。"""

import pytest
from abc import ABC
from typing import Callable

from component.base_component import BaseComponent
from component.decision.company.base import BaseCompanyDecisionComponent
from core.entity import Entity


class _StubDecisionComponent(BaseCompanyDecisionComponent):
    """最小具体子类，用于测试抽象基类。"""

    def decide_pricing(self) -> dict:
        return {}

    def decide_investment_plan(self) -> dict:
        return {}

    def decide_loan_needs(self) -> tuple:
        return (0, 0)

    def decide_budget_allocation(self) -> dict:
        return {}

    def make_purchase_sort_key(self) -> Callable:
        return lambda x: 0.0

    def decide_wage(self) -> int:
        return 0


class TestBaseCompanyDecisionComponentAbstract:
    """1.1.1: 抽象基类不可实例化，子类必须实现所有抽象方法。"""

    def setup_method(self) -> None:
        BaseCompanyDecisionComponent.components.clear()

    def teardown_method(self) -> None:
        BaseCompanyDecisionComponent.components.clear()

    def test_cannot_instantiate_base_class(self) -> None:
        """基类不能直接实例化。"""
        entity = Entity("test")
        with pytest.raises(TypeError):
            BaseCompanyDecisionComponent(entity)

    def test_inherits_base_component_and_abc(self) -> None:
        """基类应同时继承 BaseComponent 和 ABC。"""
        assert issubclass(BaseCompanyDecisionComponent, BaseComponent)
        assert issubclass(BaseCompanyDecisionComponent, ABC)

    def test_incomplete_subclass_cannot_instantiate(self) -> None:
        """未实现全部抽象方法的子类不可实例化。"""

        class IncompleteSub(BaseCompanyDecisionComponent):
            pass

        entity = Entity("test")
        with pytest.raises(TypeError):
            IncompleteSub(entity)

    def test_complete_subclass_can_instantiate(self) -> None:
        """实现了所有抽象方法的子类可以实例化。"""
        entity = Entity("test")
        comp = _StubDecisionComponent(entity)
        assert isinstance(comp, BaseCompanyDecisionComponent)
        assert comp.outer is entity


class TestBaseCompanyDecisionComponentTraits:
    """1.1.1: CEO 特质属性和 investment_plan。"""

    def setup_method(self) -> None:
        BaseCompanyDecisionComponent.components.clear()

    def teardown_method(self) -> None:
        BaseCompanyDecisionComponent.components.clear()

    @pytest.fixture()
    def comp(self):
        entity = Entity("test")
        return _StubDecisionComponent(entity)

    def test_has_six_traits(self, comp) -> None:
        """基类应有 6 维 CEO 特质。"""
        for attr in [
            "business_acumen", "risk_appetite", "profit_focus",
            "marketing_awareness", "tech_focus", "price_sensitivity",
        ]:
            assert hasattr(comp, attr)

    def test_traits_are_float(self, comp) -> None:
        """所有 CEO 特质应为 float。"""
        for attr in [
            "business_acumen", "risk_appetite", "profit_focus",
            "marketing_awareness", "tech_focus", "price_sensitivity",
        ]:
            assert isinstance(getattr(comp, attr), float)

    def test_traits_in_range(self, comp) -> None:
        """CEO 特质应在 [0, 1] 范围。"""
        for attr in [
            "business_acumen", "risk_appetite", "profit_focus",
            "marketing_awareness", "tech_focus", "price_sensitivity",
        ]:
            val = getattr(comp, attr)
            assert 0.0 <= val <= 1.0, f"{attr}={val} 超出 [0,1] 范围"

    def test_has_investment_plan(self, comp) -> None:
        """基类应有 investment_plan 字典。"""
        assert hasattr(comp, "investment_plan")
        assert isinstance(comp.investment_plan, dict)
        assert comp.investment_plan == {}

    def test_set_context_stores_context(self, comp) -> None:
        """set_context 应存储上下文到 _context。"""
        ctx = {"company": {"name": "Test"}}
        comp.set_context(ctx)
        assert comp._context is ctx

    def test_context_initially_empty(self, comp) -> None:
        """_context 初始应为空字典。"""
        assert comp._context == {}


class TestBaseCompanyDecisionComponentLifecycle:
    """组件生命周期：注册和销毁。"""

    def setup_method(self) -> None:
        _StubDecisionComponent.components.clear()

    def teardown_method(self) -> None:
        _StubDecisionComponent.components.clear()

    def test_component_tracking(self) -> None:
        """创建后应注册到 components 列表。"""
        entity = Entity("test")
        comp = entity.init_component(_StubDecisionComponent)
        assert comp in _StubDecisionComponent.components

    def test_destroy_cleanup(self) -> None:
        """entity.destroy() 应从 components 列表移除。"""
        entity = Entity("test")
        comp = entity.init_component(_StubDecisionComponent)
        entity.destroy()
        assert comp not in _StubDecisionComponent.components


class TestBaseCompanyDecisionComponentAPI:
    """1.1.1: 5 个抽象决策方法签名验证。"""

    def test_set_context_is_concrete(self) -> None:
        """set_context 应为具体方法（非抽象）。"""
        assert not getattr(BaseCompanyDecisionComponent.set_context, "__isabstractmethod__", False)

    def test_decide_pricing_is_abstract(self) -> None:
        assert getattr(BaseCompanyDecisionComponent.decide_pricing, "__isabstractmethod__", False)

    def test_decide_investment_plan_is_abstract(self) -> None:
        assert getattr(BaseCompanyDecisionComponent.decide_investment_plan, "__isabstractmethod__", False)

    def test_decide_loan_needs_is_abstract(self) -> None:
        assert getattr(BaseCompanyDecisionComponent.decide_loan_needs, "__isabstractmethod__", False)

    def test_decide_budget_allocation_is_abstract(self) -> None:
        assert getattr(BaseCompanyDecisionComponent.decide_budget_allocation, "__isabstractmethod__", False)

    def test_make_purchase_sort_key_is_abstract(self) -> None:
        assert getattr(BaseCompanyDecisionComponent.make_purchase_sort_key, "__isabstractmethod__", False)

    def test_decide_wage_is_abstract(self) -> None:
        """decide_wage 应为抽象方法。"""
        assert getattr(BaseCompanyDecisionComponent.decide_wage, "__isabstractmethod__", False)
