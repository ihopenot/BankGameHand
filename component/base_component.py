from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.entity import Entity


class BaseComponent:
    """所有组件的基类，持有所属 Entity 的引用。"""

    def __init__(self, outer: Entity) -> None:
        self.outer = outer
