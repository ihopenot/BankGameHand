from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, List, Type

if TYPE_CHECKING:
    from core.entity import Entity


class BaseComponent:
    """所有组件的基类，持有所属 Entity 的引用。

    每个子类自动维护一个 ``components`` 类变量，追踪该子类的所有存活实例。
    """

    components: ClassVar[List[BaseComponent]] = []

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.components = []

    def __init__(self, outer: Entity) -> None:
        self.outer: Entity = outer
        type(self).components.append(self)
