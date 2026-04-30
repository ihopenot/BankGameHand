"""BaseFolkDecisionComponent 抽象基类测试。"""

import pytest

from core.entity import Entity


class TestBaseFolkDecisionComponentAbstract:
    """BaseFolkDecisionComponent 是抽象类，不能实例化。"""

    def test_cannot_instantiate_abstract(self) -> None:
        """抽象类不能直接实例化。"""
        from component.decision.folk.base import BaseFolkDecisionComponent
        entity = Entity("test")
        with pytest.raises(TypeError):
            entity.init_component(BaseFolkDecisionComponent)

    def test_decide_spending_is_abstract(self) -> None:
        """decide_spending() 是抽象方法。"""
        from component.decision.folk.base import BaseFolkDecisionComponent
        assert hasattr(BaseFolkDecisionComponent, "decide_spending")
        import inspect
        assert getattr(BaseFolkDecisionComponent.decide_spending, "__isabstractmethod__", False)

    def test_set_context_stores_context(self) -> None:
        """set_context() 存储上下文字典。"""
        from component.decision.folk.base import BaseFolkDecisionComponent

        # 创建一个具体子类来测试 set_context
        class ConcreteFolkDecision(BaseFolkDecisionComponent):
            def decide_spending(self):
                return {}

        entity = Entity("test")
        comp = entity.init_component(ConcreteFolkDecision)
        ctx = {"economy_index": 1.0, "reference_prices": {}}
        comp.set_context(ctx)
        assert comp._context == ctx
