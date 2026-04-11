from __future__ import annotations

from typing import TYPE_CHECKING

from core.config import ConfigManager
from core.registry import Registry
from core.types import Rate
from system.economy_models import EconomyModel
from system.economy_models.dual_cycle_model import DualCycleModel
from system.service import Service

if TYPE_CHECKING:
    from game.game import Game

# 经济模型注册表
economy_model_registry = Registry()
economy_model_registry.register(DualCycleModel)


class EconomyService(Service):
    economy_index: Rate

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.economy_index = 0

        config = ConfigManager().section("economy")
        model_name: str = config.model
        self.model: EconomyModel = economy_model_registry.create(model_name)

    def update_phase(self) -> None:
        self.economy_index = self.model.calculate(self.game.round)

    def sell_phase(self) -> None:
        pass

    def buy_phase(self) -> None:
        pass

    def product_phase(self) -> None:
        pass

    def plan_phase(self) -> None:
        pass

    def settlement_phase(self) -> None:
        pass

    def act_phase(self) -> None:
        pass
