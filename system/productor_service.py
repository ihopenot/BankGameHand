from __future__ import annotations

from typing import TYPE_CHECKING

from component.productor_component import ProductorComponent
from system.service import Service

if TYPE_CHECKING:
    from game.game import Game


class ProductorService(Service):
    """生产者服务：编排所有 ProductorComponent 的科技更新与生产流程。"""

    def __init__(self, game: Game) -> None:
        super().__init__(game)

    def update_phase(self) -> None:
        """遍历所有 ProductorComponent，更新全局 max_tech。"""
        ProductorComponent.max_tech.clear()
        for prod in ProductorComponent.components:
            prod.update_max_tech()

    def product_phase(self) -> None:
        """遍历所有 ProductorComponent，执行生产并存入库存。"""
        for prod in ProductorComponent.components:
            prod.produce_all()

    def sell_phase(self) -> None:
        pass

    def buy_phase(self) -> None:
        pass

    def plan_phase(self) -> None:
        pass

    def settlement_phase(self) -> None:
        pass

    def act_phase(self) -> None:
        pass
