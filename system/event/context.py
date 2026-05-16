from __future__ import annotations

from typing import Any, Dict


class EventContext:
    """事件执行上下文，维护变量绑定。"""

    def __init__(self, global_state: Any = None) -> None:
        self.bindings: Dict[str, Any] = {}
        if global_state is not None:
            self.bindings["_G"] = global_state

    def get(self, var_name: str) -> Any:
        """获取变量值。未绑定时抛出 KeyError。"""
        if var_name not in self.bindings:
            raise KeyError(f"Unbound variable: {var_name}")
        return self.bindings[var_name]

    def set(self, var_name: str, value: Any) -> None:
        """绑定变量。"""
        self.bindings[var_name] = value

    def has(self, var_name: str) -> bool:
        """检查变量是否已绑定。"""
        return var_name in self.bindings

    def unbind(self, var_name: str) -> None:
        """解绑变量。"""
        self.bindings.pop(var_name, None)
