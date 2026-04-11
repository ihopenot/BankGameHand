import pytest
from core.base_model import BaseModel


class TestBaseModel:
    def test_cannot_instantiate_directly(self):
        """BaseModel 是 ABC，不可直接实例化"""
        with pytest.raises(TypeError):
            BaseModel()

    def test_subclass_must_implement_get_state(self):
        """子类必须实现 get_state 方法"""

        class IncompleteModel(BaseModel):
            model_name = "incomplete"

        with pytest.raises(TypeError):
            IncompleteModel()

    def test_complete_subclass_can_instantiate(self):
        """完整实现所有抽象方法的子类可以正常实例化"""

        class ConcreteModel(BaseModel):
            model_name = "concrete"

            def get_state(self) -> dict:
                return {"status": "ok"}

        model = ConcreteModel()
        assert model.model_name == "concrete"
        assert model.get_state() == {"status": "ok"}
