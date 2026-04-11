from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from core.base_model import BaseModel


class Registry:
    """通用类注册表，支持按名称注册和实例化类。

    注册时自动从类的 model_name 属性读取名称。
    """

    def __init__(self) -> None:
        self._registry: dict[str, type[BaseModel]] = {}

    def register(self, cls: type[BaseModel] | None = None) -> type[BaseModel] | Callable[[type[BaseModel]], type[BaseModel]]:
        """注册一个类。支持两种用法：
        1. registry.register(SomeClass) — 直接注册，从 cls.model_name 读取名称
        2. @registry.register 作为装饰器
        """
        if cls is not None:
            self._registry[cls.model_name] = cls
            return cls

        def decorator(cls: type[BaseModel]) -> type[BaseModel]:
            self._registry[cls.model_name] = cls
            return cls

        return decorator

    def create(self, name: str, **kwargs: object) -> BaseModel:
        """根据注册名称创建实例，kwargs 传递给构造函数。"""
        return self._registry[name](**kwargs)

    def available(self) -> list[str]:
        """返回所有已注册名称的列表。"""
        return list(self._registry.keys())
