import pytest
from system.economy_models import EconomyModel
from core.base_model import BaseModel


class TestEconomyModel:
    def test_inherits_from_base_model(self):
        """EconomyModel 继承自 BaseModel"""
        assert issubclass(EconomyModel, BaseModel)

    def test_cannot_instantiate_directly(self):
        """EconomyModel 是 ABC，不可直接实例化"""
        with pytest.raises(TypeError):
            EconomyModel()

    def test_subclass_must_implement_calculate(self):
        """子类必须实现 calculate 方法"""

        class IncompleteEconomy(EconomyModel):
            model_name = "incomplete"

            def get_state(self) -> dict:
                return {}

        with pytest.raises(TypeError):
            IncompleteEconomy()

    def test_complete_subclass_can_instantiate(self):
        """完整实现所有抽象方法的子类可以正常实例化"""

        class ConcreteEconomy(EconomyModel):
            model_name = "concrete"

            def get_state(self) -> dict:
                return {}

            def calculate(self, t: int) -> int:
                return 0

        model = ConcreteEconomy()
        assert model.model_name == "concrete"
        assert model.calculate(0) == 0
        assert model.get_state() == {}
