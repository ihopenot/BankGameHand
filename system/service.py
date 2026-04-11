from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.game import Game


class Service(ABC):
    def __init__(self, game: Game):
        self.game = game

    @abstractmethod
    def update_phase(self):
        pass

    @abstractmethod
    def sell_phase():
        pass

    @abstractmethod
    def buy_phase():
        pass

    @abstractmethod
    def product_phase():
        pass

    @abstractmethod
    def plan_phase():
        pass

    @abstractmethod
    def settlement_phase():
        pass

    @abstractmethod
    def act_phase():
        pass