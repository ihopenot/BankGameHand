from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Type

from component.base_component import BaseComponent

if TYPE_CHECKING:
    from core.entity import Entity

# 居民决策组件注册表：name → subclass of BaseFolkDecisionComponent
_FOLK_DECISION_REGISTRY: Dict[str, Type[BaseFolkDecisionComponent]] = {}


def register_folk_decision_component(name: str):
    """类装饰器：将居民决策组件类注册到全局注册表。"""
    def decorator(cls: Type[BaseFolkDecisionComponent]) -> Type[BaseFolkDecisionComponent]:
        _FOLK_DECISION_REGISTRY[name] = cls
        return cls
    return decorator


def get_folk_decision_component_class(name: str) -> Type[BaseFolkDecisionComponent]:
    """根据名称获取居民决策组件类。首次查询时自动导入子模块以触发注册。"""
    if not _FOLK_DECISION_REGISTRY:
        import component.decision.folk.classic  # noqa: F401 — 触发 @register_folk_decision_component
    return _FOLK_DECISION_REGISTRY[name]


class BaseFolkDecisionComponent(BaseComponent, ABC):
    """居民决策抽象基类：定义支出决策 API。"""

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)
        self._context: dict = {}

    def set_context(self, context: dict) -> None:
        """接收并存储决策上下文数据。"""
        self._context = context

    @abstractmethod
    def decide_spending(self) -> Dict[str, Dict]:
        """支出决策：返回 {goods_type_name: {"budget": int, "demand": int}}。"""
