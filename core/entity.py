from __future__ import annotations

from typing import Dict, Optional, Type, TypeVar

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

    def get_component(self, comp_type: Type[T]) -> Optional[T]:
        """获取已初始化的组件。不存在则返回 None。"""
        return self._components.get(comp_type)  # type: ignore[return-value]

    def destroy(self) -> None:
        """注销所有组件，从各子类的 components 列表中移除，清空组件注册表。"""
        for comp in self._components.values():
            comp_list = type(comp).components
            if comp in comp_list:
                comp_list.remove(comp)
        self._components.clear()
