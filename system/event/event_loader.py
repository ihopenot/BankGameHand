from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml

from system.event.effect_registry import has_effect
from system.event.expr import (
    And,
    CaptureAny,
    CaptureEvery,
    CaptureRandom,
    Compare,
    EffectCall,
    Expr,
    Exprs,
    GetField,
    If,
    Literal,
    Modifier,
    ModifyAttr,
    Not,
    Or,
    VarRef,
)


@dataclass
class Event:
    """事件定义。"""

    id: str
    name: str = ""
    expr: Expr = field(default_factory=lambda: Literal(None))


def load_events(path: str) -> List[Event]:
    """从目录中加载所有事件定义YAML文件。"""
    events: List[Event] = []
    config_dir = Path(path)
    if not config_dir.is_dir():
        return events

    for file in sorted(config_dir.iterdir()):
        if file.suffix in (".yaml", ".yml"):
            with open(file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data and "events" in data:
                for event_data in data["events"]:
                    events.append(_parse_event(event_data))
    return events


def _parse_event(data: Dict[str, Any]) -> Event:
    """解析单个事件定义。"""
    event_id = data.get("id", "unnamed")
    name = data.get("name", "")
    expr_data = data.get("expr", [])

    if isinstance(expr_data, list):
        expr = _parse_expr_list(expr_data)
    else:
        expr = _parse_node(expr_data)

    return Event(id=event_id, name=name, expr=expr)


def _parse_expr_list(nodes: List[Any]) -> Expr:
    """解析表达式列表为 Exprs 节点。"""
    exprs = [_parse_node(node) for node in nodes]
    if len(exprs) == 1:
        return exprs[0]
    return Exprs(exprs)


def _parse_node(node: Any) -> Expr:
    """递归解析单个YAML节点为 Expr。"""
    if node is None:
        return Literal(None)

    if isinstance(node, (int, float, bool, str)):
        return Literal(node)

    if not isinstance(node, dict):
        return Literal(node)

    # 每个节点是一个dict，键为节点类型
    # 匹配各种节点类型

    if "If" in node:
        return _parse_if(node["If"])

    if "Any" in node:
        return _parse_capture(node["Any"], "any")

    if "Every" in node:
        return _parse_capture(node["Every"], "every")

    if "Random" in node:
        return _parse_capture(node["Random"], "random")

    if "And" in node:
        return _parse_and(node["And"])

    if "Or" in node:
        return _parse_or(node["Or"])

    if "Not" in node:
        return _parse_not(node["Not"])

    if "GetField" in node:
        return _parse_getfield(node)

    if "Compare" in node:
        return _parse_compare(node["Compare"])

    if "Exprs" in node:
        return _parse_expr_list(node["Exprs"])

    if "ModifyAttr" in node:
        return _parse_modify_attr(node["ModifyAttr"])

    if "Literal" in node:
        return Literal(node["Literal"])

    if "Var" in node:
        return VarRef(node["Var"])

    # 尝试匹配注册表中的效果
    for key in node:
        if has_effect(key):
            return _parse_effect_call(key, node[key])

    # 未识别的节点，当作字面量
    return Literal(node)


def _parse_if(data: Any) -> Expr:
    """解析 If 节点。If: [condition, body]"""
    if isinstance(data, list) and len(data) == 2:
        condition = _parse_node(data[0])
        body = _parse_node(data[1])
        return If(condition, body)
    raise ValueError(f"If node expects a list of [condition, body], got: {data}")


def _parse_capture(data: Any, mode: str) -> Expr:
    """解析 Any/Every/Random 捕获节点。

    格式:
      Any:
        all: <expr>       # 提供实体集合的表达式
        condition: <expr> # 过滤条件（列表则为And）
        var: <name>       # 绑定变量名
    """
    if not isinstance(data, dict):
        raise ValueError(f"Capture node expects a dict, got: {data}")

    all_expr = _parse_node(data.get("all"))
    var = data.get("var", "_capture")

    # condition 可以是单个表达式或列表(隐式And)
    cond_data = data.get("condition")
    if cond_data is None:
        condition = Literal(True)
    elif isinstance(cond_data, list):
        if len(cond_data) == 1:
            condition = _parse_node(cond_data[0])
        else:
            condition = And([_parse_node(c) for c in cond_data])
    else:
        condition = _parse_node(cond_data)

    if mode == "any":
        return CaptureAny(all_expr, condition, var)
    elif mode == "every":
        return CaptureEvery(all_expr, condition, var)
    else:
        return CaptureRandom(all_expr, condition, var)


def _parse_and(data: Any) -> Expr:
    """解析 And 节点。"""
    if isinstance(data, list):
        return And([_parse_node(item) for item in data])
    raise ValueError(f"And expects a list, got: {data}")


def _parse_or(data: Any) -> Expr:
    """解析 Or 节点。"""
    if isinstance(data, list):
        return Or([_parse_node(item) for item in data])
    raise ValueError(f"Or expects a list, got: {data}")


def _parse_not(data: Any) -> Expr:
    """解析 Not 节点。"""
    return Not(_parse_node(data))


def _parse_getfield(node: Dict[str, Any]) -> Expr:
    """解析 GetField 节点。

    格式:
      GetField:
        - <obj_var_name or expr>
        - <field_name>

    向后兼容：如果带有 op/value，则自动包装为 Compare。
    """
    args = node["GetField"]
    if not isinstance(args, list) or len(args) < 2:
        raise ValueError(f"GetField expects [obj, field], got: {args}")

    obj_raw = args[0]
    field_name = args[1]

    # obj 可以是变量名字符串或嵌套表达式
    if isinstance(obj_raw, str):
        obj_expr = VarRef(obj_raw)
    else:
        obj_expr = _parse_node(obj_raw)

    getfield = GetField(obj_expr, field_name)

    # 向后兼容：如果有 op/value 则包装为 Compare
    op = node.get("op")
    if op is not None:
        compare_value = node.get("value")
        return Compare(getfield, op, Literal(compare_value))

    return getfield


def _parse_compare(data: Any) -> Expr:
    """解析 Compare 节点。

    格式:
      Compare:
        - <左值表达式>
        - <运算符字符串>
        - <右值表达式>
    """
    if not isinstance(data, list) or len(data) != 3:
        raise ValueError(f"Compare expects [left, op, right], got: {data}")

    left = _parse_node(data[0])
    op = data[1]
    right = _parse_node(data[2])
    return Compare(left, op, right)


def _parse_modify_attr(data: Any) -> Expr:
    """解析 ModifyAttr 节点。

    格式:
      ModifyAttr:
        - <target_var>
        - Modifiers:
          - Modifier:
              type: add
              field: stability
              value: -10
    """
    if not isinstance(data, list) or len(data) < 2:
        raise ValueError(f"ModifyAttr expects [target, modifiers_block], got: {data}")

    target_var = data[0]
    modifiers_block = data[1]

    modifiers: List[Modifier] = []
    if isinstance(modifiers_block, dict) and "Modifiers" in modifiers_block:
        for mod_item in modifiers_block["Modifiers"]:
            if isinstance(mod_item, dict) and "Modifier" in mod_item:
                mod_data = mod_item["Modifier"]
                modifiers.append(Modifier(
                    field=mod_data.get("field", mod_data.get("filed", "")),  # 兼容拼写
                    mod_type=mod_data.get("type", "add"),
                    value=mod_data.get("value", 0),
                ))

    return ModifyAttr(target_var, modifiers)


def _parse_effect_call(effect_name: str, data: Any) -> Expr:
    """解析注册效果调用。

    格式:
      EffectName:
        - <target_var>
        - param1: value1
          param2: value2
    """
    if isinstance(data, list):
        target_var = data[0] if data else "_G"
        params = data[1] if len(data) > 1 and isinstance(data[1], dict) else {}
    elif isinstance(data, dict):
        target_var = data.pop("target", "_G")
        params = data
    else:
        target_var = str(data) if data else "_G"
        params = {}

    return EffectCall(effect_name, target_var, params)
