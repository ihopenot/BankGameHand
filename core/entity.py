from __future__ import annotations

from typing import Dict, Type, TypeVar

from component.base_component import BaseComponent

T = TypeVar("T", bound=BaseComponent)


class Entity:
    """实体基类，维护组件字典，提供组件挂载和获取。"""

    def __init__(self) -> None:
        self._components: Dict[Type[BaseComponent], BaseComponent] = {}

    def init_component(self, comp_type: Type[T]) -> T:
        """初始化组件。已存在则跳过，返回已有实例。"""
        if comp_type in self._components:
            return self._components[comp_type]  # type: ignore[return-value]
        comp = comp_type(self)
        self._components[comp_type] = comp
        return comp

    def get_component(self, comp_type: Type[T]) -> T:
        """获取已初始化的组件。不存在则抛出 KeyError。"""
        if comp_type not in self._components:
            raise KeyError(f"Component {comp_type.__name__} not found")
        return self._components[comp_type]  # type: ignore[return-value]
