"""事件系统单元测试。"""

from __future__ import annotations

import pytest

from system.event.context import EventContext
from system.event.effect_registry import clear_registry, register_effect
from system.event.expr import (
    And,
    CaptureAny,
    CaptureEvery,
    CaptureRandom,
    Compare,
    EffectCall,
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


# ─── 测试辅助 ─────────────────────────────────────────────

class MockEntity:
    """测试用模拟实体。"""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def ctx():
    """基础上下文。"""
    return EventContext()


@pytest.fixture
def game_ctx():
    """带全局状态的上下文。"""
    countries = [
        MockEntity(name="A", stability=20, companies=[]),
        MockEntity(name="B", stability=5, companies=[]),
        MockEntity(name="C", stability=15, companies=[]),
    ]
    companies = [
        MockEntity(name="C1", country=countries[0], labor_capital_conflict=60, max_history_sales=600, production=100),
        MockEntity(name="C2", country=countries[0], labor_capital_conflict=30, max_history_sales=200, production=80),
        MockEntity(name="C3", country=countries[2], labor_capital_conflict=70, max_history_sales=800, production=120),
    ]
    countries[0].companies = [companies[0], companies[1]]
    countries[2].companies = [companies[2]]

    g = {
        "all_countries": countries,
        "all_companies": companies,
        "current_round": 5,
    }
    return EventContext(g)


# ─── 基础表达式测试 ────────────────────────────────────────

class TestLiteral:
    def test_returns_value(self, ctx):
        assert Literal(42).evaluate(ctx) == 42
        assert Literal("hello").evaluate(ctx) == "hello"
        assert Literal(None).evaluate(ctx) is None


class TestVarRef:
    def test_returns_bound_value(self, ctx):
        ctx.set("x", 99)
        assert VarRef("x").evaluate(ctx) == 99

    def test_raises_on_unbound(self, ctx):
        with pytest.raises(KeyError):
            VarRef("missing").evaluate(ctx)


class TestGetField:
    def test_attr_access(self, ctx):
        entity = MockEntity(stability=25)
        ctx.set("e", entity)
        expr = GetField(VarRef("e"), "stability")
        assert expr.evaluate(ctx) == 25

    def test_dict_access(self, ctx):
        ctx.set("d", {"key": "value"})
        expr = GetField(VarRef("d"), "key")
        assert expr.evaluate(ctx) == "value"


class TestCompare:
    def test_greater_than(self, ctx):
        ctx.set("e", MockEntity(stability=25))
        expr = Compare(GetField(VarRef("e"), "stability"), ">", Literal(10))
        assert expr.evaluate(ctx) is True

    def test_less_than(self, ctx):
        ctx.set("e", MockEntity(stability=25))
        expr = Compare(GetField(VarRef("e"), "stability"), "<", Literal(10))
        assert expr.evaluate(ctx) is False

    def test_equal(self, ctx):
        ctx.set("e", MockEntity(stability=25))
        expr = Compare(GetField(VarRef("e"), "stability"), "==", Literal(25))
        assert expr.evaluate(ctx) is True

    def test_belongs_to_identity(self, ctx):
        parent = MockEntity(name="parent")
        child = MockEntity(country=parent)
        ctx.set("child", child)
        ctx.set("parent", parent)
        expr = Compare(GetField(VarRef("child"), "country"), "belongs_to", VarRef("parent"))
        assert expr.evaluate(ctx) is True

    def test_belongs_to_list(self, ctx):
        items = [1, 2, 3]
        ctx.set("val", 2)
        ctx.set("lst", items)
        expr = Compare(VarRef("val"), "belongs_to", VarRef("lst"))
        assert expr.evaluate(ctx) is True

    def test_compare_two_fields(self, ctx):
        ctx.set("a", MockEntity(x=10))
        ctx.set("b", MockEntity(y=5))
        expr = Compare(GetField(VarRef("a"), "x"), ">", GetField(VarRef("b"), "y"))
        assert expr.evaluate(ctx) is True


class TestExprs:
    def test_sequential_execution(self, ctx):
        result = Exprs([Literal(1), Literal(2), Literal(3)]).evaluate(ctx)
        assert result == 3

    def test_empty_returns_none(self, ctx):
        assert Exprs([]).evaluate(ctx) is None


class TestIf:
    def test_truthy_condition(self, ctx):
        expr = If(Literal(True), Literal("yes"))
        assert expr.evaluate(ctx) == "yes"

    def test_falsy_condition(self, ctx):
        expr = If(Literal(False), Literal("yes"))
        assert expr.evaluate(ctx) is None

    def test_falsy_none(self, ctx):
        expr = If(Literal(None), Literal("yes"))
        assert expr.evaluate(ctx) is None

    def test_falsy_empty_list(self, ctx):
        expr = If(Literal([]), Literal("yes"))
        assert expr.evaluate(ctx) is None


class TestAnd:
    def test_all_truthy(self, ctx):
        assert And([Literal(1), Literal(2), Literal(3)]).evaluate(ctx) == 3

    def test_short_circuit(self, ctx):
        assert And([Literal(1), Literal(0), Literal(3)]).evaluate(ctx) == 0
        assert And([Literal(None), Literal(3)]).evaluate(ctx) is None


class TestOr:
    def test_first_truthy(self, ctx):
        assert Or([Literal(0), Literal(2), Literal(3)]).evaluate(ctx) == 2

    def test_all_falsy(self, ctx):
        assert Or([Literal(0), Literal(None), Literal("")]).evaluate(ctx) == ""


class TestNot:
    def test_negation(self, ctx):
        assert Not(Literal(True)).evaluate(ctx) is False
        assert Not(Literal(False)).evaluate(ctx) is True
        assert Not(Literal(0)).evaluate(ctx) is True


# ─── 捕获节点测试 ──────────────────────────────────────────

class TestCaptureAny:
    def test_finds_first_match(self, game_ctx):
        expr = CaptureAny(
            all_expr=GetField(VarRef("_G"), "all_countries"),
            condition=Compare(GetField(VarRef("target"), "stability"), ">", Literal(10)),
            var="target",
        )
        result = expr.evaluate(game_ctx)
        assert result is not None
        assert result.stability > 10
        assert game_ctx.get("target") is result

    def test_returns_none_when_no_match(self, game_ctx):
        expr = CaptureAny(
            all_expr=GetField(VarRef("_G"), "all_countries"),
            condition=Compare(GetField(VarRef("target"), "stability"), ">", Literal(100)),
            var="target",
        )
        result = expr.evaluate(game_ctx)
        assert result is None
        assert not game_ctx.has("target")


class TestCaptureEvery:
    def test_finds_all_matches(self, game_ctx):
        expr = CaptureEvery(
            all_expr=GetField(VarRef("_G"), "all_countries"),
            condition=Compare(GetField(VarRef("targets"), "stability"), ">", Literal(10)),
            var="targets",
        )
        result = expr.evaluate(game_ctx)
        assert len(result) == 2  # A(20) and C(15)
        assert all(c.stability > 10 for c in result)
        assert game_ctx.get("targets") == result

    def test_empty_list_when_no_match(self, game_ctx):
        expr = CaptureEvery(
            all_expr=GetField(VarRef("_G"), "all_countries"),
            condition=Compare(GetField(VarRef("targets"), "stability"), ">", Literal(100)),
            var="targets",
        )
        result = expr.evaluate(game_ctx)
        assert result == []
        assert not game_ctx.has("targets")


class TestCaptureRandom:
    def test_finds_one_from_matches(self, game_ctx):
        expr = CaptureRandom(
            all_expr=GetField(VarRef("_G"), "all_countries"),
            condition=Compare(GetField(VarRef("target"), "stability"), ">", Literal(10)),
            var="target",
        )
        result = expr.evaluate(game_ctx)
        assert result is not None
        assert result.stability > 10

    def test_returns_none_when_no_match(self, game_ctx):
        expr = CaptureRandom(
            all_expr=GetField(VarRef("_G"), "all_countries"),
            condition=Compare(GetField(VarRef("target"), "stability"), ">", Literal(100)),
            var="target",
        )
        result = expr.evaluate(game_ctx)
        assert result is None


class TestNestedCapture:
    def test_capture_inside_capture_condition(self, game_ctx):
        """测试嵌套捕获：在捕获国家的条件中嵌套捕获公司。"""
        inner_capture = CaptureEvery(
            all_expr=GetField(VarRef("target_country"), "companies"),
            condition=Compare(GetField(VarRef("target_companies"), "labor_capital_conflict"), ">", Literal(50)),
            var="target_companies",
        )

        outer_condition = And([
            Compare(GetField(VarRef("target_country"), "stability"), ">", Literal(10)),
            inner_capture,
        ])

        outer_capture = CaptureAny(
            all_expr=GetField(VarRef("_G"), "all_countries"),
            condition=outer_condition,
            var="target_country",
        )

        result = outer_capture.evaluate(game_ctx)
        assert result is not None
        assert result.name == "A"
        target_companies = game_ctx.get("target_companies")
        assert len(target_companies) == 1
        assert target_companies[0].name == "C1"


# ─── 效果节点测试 ──────────────────────────────────────────

class TestModifier:
    def test_add(self):
        entity = MockEntity(stability=20)
        Modifier("stability", "add", -10).apply(entity)
        assert entity.stability == 10

    def test_percent(self):
        entity = MockEntity(production=100)
        Modifier("production", "percent", 10).apply(entity)
        assert entity.production == pytest.approx(110.0)

    def test_set(self):
        entity = MockEntity(stability=20)
        Modifier("stability", "set", 50).apply(entity)
        assert entity.stability == 50

    def test_dict_entity(self):
        entity = {"stability": 20}
        Modifier("stability", "add", 5).apply(entity)
        assert entity["stability"] == 25


class TestModifyAttr:
    def test_single_entity(self, ctx):
        entity = MockEntity(stability=20, production=100)
        ctx.set("target", entity)
        expr = ModifyAttr("target", [
            Modifier("stability", "add", -10),
            Modifier("production", "percent", 10),
        ])
        expr.evaluate(ctx)
        assert entity.stability == 10
        assert entity.production == pytest.approx(110.0)

    def test_list_target(self, ctx):
        entities = [MockEntity(production=100), MockEntity(production=200)]
        ctx.set("targets", entities)
        expr = ModifyAttr("targets", [Modifier("production", "percent", 50)])
        expr.evaluate(ctx)
        assert entities[0].production == 150.0
        assert entities[1].production == 300.0


class TestEffectCall:
    def setup_method(self):
        clear_registry()

    def teardown_method(self):
        clear_registry()

    def test_calls_registered_handler(self, ctx):
        calls = []

        def handler(context, target, **params):
            calls.append((target, params))

        register_effect("TestEffect", handler)
        entity = MockEntity(name="test")
        ctx.set("t", entity)
        expr = EffectCall("TestEffect", "t", {"template": "B01"})
        expr.evaluate(ctx)
        assert len(calls) == 1
        assert calls[0] == (entity, {"template": "B01"})


# ─── YAML 加载器测试 ───────────────────────────────────────

class TestEventLoader:
    def test_load_simple_event_with_compare(self, tmp_path):
        """测试新的 Compare 节点 YAML 格式。"""
        from system.event.event_loader import load_events

        yaml_content = """
events:
  - id: test_event
    name: "测试事件"
    expr:
      - If:
        - Compare:
          - GetField:
              - _G
              - current_round
          - ">"
          - 3
        - ModifyAttr:
          - target
          - Modifiers:
            - Modifier:
                type: add
                field: stability
                value: -5
"""
        event_file = tmp_path / "test.yaml"
        event_file.write_text(yaml_content, encoding="utf-8")

        events = load_events(str(tmp_path))
        assert len(events) == 1
        assert events[0].id == "test_event"
        assert events[0].name == "测试事件"

    def test_backward_compat_getfield_with_op(self, tmp_path):
        """测试向后兼容：GetField 带 op/value 自动转为 Compare。"""
        from system.event.event_loader import load_events

        yaml_content = """
events:
  - id: compat_test
    expr:
      - If:
        - GetField:
            - _G
            - current_round
          op: ">"
          value: 3
        - Literal: done
"""
        event_file = tmp_path / "compat.yaml"
        event_file.write_text(yaml_content, encoding="utf-8")

        events = load_events(str(tmp_path))
        assert len(events) == 1
        # 验证能正确执行
        from system.event.context import EventContext
        ctx = EventContext({"current_round": 5})
        result = events[0].expr.evaluate(ctx)
        assert result == "done"

    def test_load_capture_event(self, tmp_path):
        from system.event.event_loader import load_events

        yaml_content = """
events:
  - id: capture_test
    expr:
      - If:
        - Any:
            all:
              GetField:
                - _G
                - all_countries
            condition:
              - Compare:
                - GetField:
                    - target_country
                    - stability
                - ">"
                - 10
            var: target_country
        - Exprs:
          - ModifyAttr:
            - target_country
            - Modifiers:
              - Modifier:
                  type: add
                  field: stability
                  value: -10
"""
        event_file = tmp_path / "capture.yaml"
        event_file.write_text(yaml_content, encoding="utf-8")

        events = load_events(str(tmp_path))
        assert len(events) == 1
        assert events[0].id == "capture_test"


# ─── 端到端集成测试 ────────────────────────────────────────

class TestEndToEnd:
    def test_full_event_evaluation(self, game_ctx):
        """完整事件流程：捕获国家 → 捕获公司 → 修改属性。"""
        inner_capture = CaptureEvery(
            all_expr=GetField(VarRef("target_country"), "companies"),
            condition=And([
                Compare(GetField(VarRef("target_companies"), "labor_capital_conflict"), ">", Literal(50)),
                Compare(GetField(VarRef("target_companies"), "max_history_sales"), ">", Literal(500)),
            ]),
            var="target_companies",
        )

        outer_capture = CaptureAny(
            all_expr=GetField(VarRef("_G"), "all_countries"),
            condition=And([
                Compare(GetField(VarRef("target_country"), "stability"), ">", Literal(10)),
                inner_capture,
            ]),
            var="target_country",
        )

        effects = Exprs([
            ModifyAttr("target_country", [Modifier("stability", "add", -10)]),
            ModifyAttr("target_companies", [Modifier("production", "percent", 10)]),
        ])

        event_expr = If(outer_capture, effects)
        event_expr.evaluate(game_ctx)

        country_a = game_ctx.get("target_country")
        assert country_a.name == "A"
        assert country_a.stability == 10  # 20 - 10

        target_companies = game_ctx.get("target_companies")
        assert len(target_companies) == 1
        assert target_companies[0].name == "C1"
        assert target_companies[0].production == pytest.approx(110.0)

    def test_event_does_not_fire_when_no_match(self, game_ctx):
        """所有国家stability都不满足条件时，事件不触发。"""
        for c in game_ctx.get("_G")["all_countries"]:
            c.stability = 1

        capture = CaptureAny(
            all_expr=GetField(VarRef("_G"), "all_countries"),
            condition=Compare(GetField(VarRef("target"), "stability"), ">", Literal(10)),
            var="target",
        )
        effects = ModifyAttr("target", [Modifier("stability", "add", -100)])
        event_expr = If(capture, effects)
        event_expr.evaluate(game_ctx)

        for c in game_ctx.get("_G")["all_countries"]:
            assert c.stability == 1
