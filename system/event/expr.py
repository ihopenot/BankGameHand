from __future__ import annotations

import random as _random
from abc import ABC, abstractmethod
from typing import Any, List


class Expr(ABC):
    """表达式节点基类。所有节点求值后返回一个值。"""

    @abstractmethod
    def evaluate(self, context: "EventContext") -> Any:
        ...


class Literal(Expr):
    """常量值。"""

    def __init__(self, value: Any) -> None:
        self.value = value

    def evaluate(self, context: "EventContext") -> Any:
        return self.value


class GetField(Expr):
    """属性访问。返回对象的指定字段值。

    GetField(obj_expr, field) → 返回属性值
    """

    def __init__(self, obj_expr: Expr, field: str) -> None:
        self.obj_expr = obj_expr
        self.field = field

    def evaluate(self, context: "EventContext") -> Any:
        obj = self.obj_expr.evaluate(context)
        if isinstance(obj, dict):
            return obj[self.field]
        return getattr(obj, self.field)


class Compare(Expr):
    """比较表达式。对左值和右值执行比较操作，返回 bool。

    Compare(left_expr, op, right_expr)
    """

    def __init__(self, left: Expr, op: str, right: Expr) -> None:
        self.left = left
        self.op = op
        self.right = right

    def evaluate(self, context: "EventContext") -> Any:
        left_val = self.left.evaluate(context)
        right_val = self.right.evaluate(context)
        return _compare(left_val, self.op, right_val)


class VarRef(Expr):
    """变量引用，从上下文中取值。"""

    def __init__(self, var_name: str) -> None:
        self.var_name = var_name

    def evaluate(self, context: "EventContext") -> Any:
        return context.get(self.var_name)


class Exprs(Expr):
    """表达式列表，顺序执行，返回最后一个值。"""

    def __init__(self, exprs: List[Expr]) -> None:
        self.exprs = exprs

    def evaluate(self, context: "EventContext") -> Any:
        result: Any = None
        for expr in self.exprs:
            result = expr.evaluate(context)
        return result


class If(Expr):
    """条件执行。condition为falsy时跳过body，返回None。"""

    def __init__(self, condition: Expr, body: Expr) -> None:
        self.condition = condition
        self.body = body

    def evaluate(self, context: "EventContext") -> Any:
        if self.condition.evaluate(context):
            return self.body.evaluate(context)
        return None


class And(Expr):
    """短路与。返回最后一个truthy值，或第一个falsy值。"""

    def __init__(self, exprs: List[Expr]) -> None:
        self.exprs = exprs

    def evaluate(self, context: "EventContext") -> Any:
        result: Any = True
        for expr in self.exprs:
            result = expr.evaluate(context)
            if not result:
                return result
        return result


class Or(Expr):
    """短路或。返回第一个truthy值，或最后一个falsy值。"""

    def __init__(self, exprs: List[Expr]) -> None:
        self.exprs = exprs

    def evaluate(self, context: "EventContext") -> Any:
        result: Any = None
        for expr in self.exprs:
            result = expr.evaluate(context)
            if result:
                return result
        return result


class Not(Expr):
    """逻辑非。"""

    def __init__(self, expr: Expr) -> None:
        self.expr = expr

    def evaluate(self, context: "EventContext") -> Any:
        return not self.expr.evaluate(context)


# ─── 比较辅助 ───────────────────────────────────────────

def _compare(left: Any, op: str, right: Any) -> bool:
    """执行比较操作。"""
    if op == ">":
        return left > right
    elif op == ">=":
        return left >= right
    elif op == "<":
        return left < right
    elif op == "<=":
        return left <= right
    elif op == "==":
        return left == right
    elif op == "!=":
        return left != right
    elif op == "belongs_to":
        # 检查左值是否属于右值（引用相等或包含关系）
        if isinstance(right, list):
            return left in right
        return left is right
    else:
        raise ValueError(f"Unknown comparison operator: {op}")


# ─── 捕获节点 ─────────────────────────────────────────────

class CaptureAny(Expr):
    """从集合中找第一个满足条件的实体，绑定到var。找不到返回None(falsy)。"""

    def __init__(self, all_expr: Expr, condition: Expr, var: str) -> None:
        self.all_expr = all_expr
        self.condition = condition
        self.var = var

    def evaluate(self, context: "EventContext") -> Any:
        items = self.all_expr.evaluate(context)
        for item in items:
            context.set(self.var, item)
            if self.condition.evaluate(context):
                return item
        context.unbind(self.var)
        return None


class CaptureEvery(Expr):
    """从集合中找所有满足条件的实体，绑定列表到var。空列表=falsy。"""

    def __init__(self, all_expr: Expr, condition: Expr, var: str) -> None:
        self.all_expr = all_expr
        self.condition = condition
        self.var = var

    def evaluate(self, context: "EventContext") -> Any:
        items = self.all_expr.evaluate(context)
        matches = []
        for item in items:
            context.set(self.var, item)
            if self.condition.evaluate(context):
                matches.append(item)
        if matches:
            context.set(self.var, matches)
        else:
            context.unbind(self.var)
        return matches


class CaptureRandom(Expr):
    """从满足条件的实体中随机选一个，绑定到var。找不到返回None。"""

    def __init__(self, all_expr: Expr, condition: Expr, var: str) -> None:
        self.all_expr = all_expr
        self.condition = condition
        self.var = var

    def evaluate(self, context: "EventContext") -> Any:
        items = self.all_expr.evaluate(context)
        matches = []
        for item in items:
            context.set(self.var, item)
            if self.condition.evaluate(context):
                matches.append(item)
        if matches:
            chosen = _random.choice(matches)
            context.set(self.var, chosen)
            return chosen
        context.unbind(self.var)
        return None


# ─── 效果节点 ─────────────────────────────────────────────

class Modifier:
    """属性修改描述。"""

    def __init__(self, field: str, mod_type: str, value: Any) -> None:
        self.field = field
        self.mod_type = mod_type  # "add", "percent", "set"
        self.value = value

    def apply(self, entity: Any) -> None:
        """对单个实体应用修改。"""
        if isinstance(entity, dict):
            current = entity.get(self.field, 0)
        else:
            current = getattr(entity, self.field, 0)

        if self.mod_type == "add":
            new_val = current + self.value
        elif self.mod_type == "percent":
            new_val = current * (1 + self.value / 100.0)
        elif self.mod_type == "set":
            new_val = self.value
        else:
            raise ValueError(f"Unknown modifier type: {self.mod_type}")

        if isinstance(entity, dict):
            entity[self.field] = new_val
        else:
            setattr(entity, self.field, new_val)


class ModifyAttr(Expr):
    """修改实体属性。target可以是单个实体或列表。"""

    def __init__(self, target_var: str, modifiers: List[Modifier]) -> None:
        self.target_var = target_var
        self.modifiers = modifiers

    def evaluate(self, context: "EventContext") -> Any:
        target = context.get(self.target_var)
        targets = target if isinstance(target, list) else [target]
        for entity in targets:
            for mod in self.modifiers:
                mod.apply(entity)
        return None


class EffectCall(Expr):
    """调用注册表中的效果处理器。"""

    def __init__(self, effect_name: str, target_var: str, params: dict) -> None:
        self.effect_name = effect_name
        self.target_var = target_var
        self.params = params

    def evaluate(self, context: "EventContext") -> Any:
        from system.event.effect_registry import get_effect

        handler = get_effect(self.effect_name)
        target = context.get(self.target_var)
        handler(context, target, **self.params)
        return None


# 避免循环导入，类型注解用字符串
from system.event.context import EventContext  # noqa: E402
