from __future__ import annotations

from typing import Any, Callable, Dict


# 效果处理器类型：接收 (context, target, **params)
EffectHandler = Callable[..., None]

_registry: Dict[str, EffectHandler] = {}


def register_effect(name: str, handler: EffectHandler) -> None:
    """注册一个效果处理器。"""
    _registry[name] = handler


def get_effect(name: str) -> EffectHandler:
    """获取已注册的效果处理器。"""
    if name not in _registry:
        raise KeyError(f"Unknown effect type: {name}")
    return _registry[name]


def has_effect(name: str) -> bool:
    """检查效果是否已注册。"""
    return name in _registry


def clear_registry() -> None:
    """清空注册表（测试用）。"""
    _registry.clear()
