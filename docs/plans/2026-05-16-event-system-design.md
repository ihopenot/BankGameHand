# Event System Design

## Overview

A YAML-driven event system with a unified expression tree interpreter. Events are defined as expression trees that combine **capture** (entity selection) and **effects** (state mutations) into a single evaluation model.

## Core Concepts

### Expression Tree

Everything is an **Expr** node. The system evaluates an event by walking its expression tree top-down. Nodes can:
- Query game state (`GetField`)
- Filter and capture entities (`Any`, `Every`, `Random`)
- Apply logic (`And`, `Or`, `Not`, `If`)
- Mutate state (`ModifyAttr`, registered effect handlers)

### Execution Context

A `Context` object holds:
- `_G`: global game state accessor (all_countries, all_companies, current_round, etc.)
- `bindings`: dict of `var_name → value` populated by capture nodes

### Capture Semantics

| Mode | Behavior | Return | Falsy when |
|------|----------|--------|------------|
| `Any` | First entity matching condition | entity | None found |
| `Every` | All entities matching condition | list | Empty list |
| `Random` | Random one from matching set | entity | None found |

Captures bind their result to `var` in the context, making it available to subsequent expressions.

### Condition Expressions

Conditions within captures are expressions that evaluate to truthy/falsy. They support:
- `GetField` + comparison operators (inline `op` and `value` on GetField node)
- `And` / `Or` / `Not` combinators
- Nested captures (a capture inside another capture's condition)

### Effects

Effects are expressions with side-effects. Initial set:
- `ModifyAttr`: modify entity attributes (add, multiply/percent, set)
- Registered handlers: extensible via `effect_registry` (e.g., `LoanRequest`)

## YAML Format

```yaml
events:
  - id: labor_strike_boost
    name: "劳资矛盾催产"
    expr:
      - If:
        - Any:
            all:
              GetField:
                - _G
                - all_countries
            condition:
              - And:
                - GetField:
                    - target_country
                    - stability
                  op: ">"
                  value: 10
                - Every:
                    all:
                      GetField:
                        - target_country
                        - companies
                    condition:
                      - And:
                        - GetField:
                            - target_company
                            - labor_capital_conflict
                          op: ">"
                          value: 50
                        - GetField:
                            - target_company
                            - max_history_sales
                          op: ">"
                          value: 500
                    var: target_companies
            var: target_country
        - Exprs:
          - ModifyAttr:
            - target_country
            - Modifiers:
              - Modifier:
                  type: add
                  field: stability
                  value: -10
          - ModifyAttr:
            - target_companies
            - Modifiers:
              - Modifier:
                  type: percent
                  field: production
                  value: 10
          - LoanRequest:
            - target_companies
            - template: B01
```

## Architecture

### File Structure

```
system/event/
├── __init__.py
├── event_service.py      # EventService: loads events, runs per-turn scan
├── event_loader.py       # YAML → Event expression tree
├── expr.py               # Expr base + all built-in node types
├── context.py            # EventContext with bindings + _G
└── effect_registry.py    # Effect handler registry

config/events/
└── *.yaml                # Event definition files
```

### Node Types

**Control Flow:**
- `If(condition, body)` — evaluate body if condition truthy
- `Exprs([expr...])` — sequential execution, return last value
- `And([expr...])` — short-circuit AND
- `Or([expr...])` — short-circuit OR
- `Not(expr)` — logical negation

**Data Access:**
- `GetField(obj_expr, field_name)` — access attribute; supports inline `op`/`value` for comparison
- `Literal(value)` — constant value

**Capture:**
- `Any(all, condition, var)` — first match → bind to var
- `Every(all, condition, var)` — all matches → bind to var
- `Random(all, condition, var)` — random from matches → bind to var

**Effects:**
- `ModifyAttr(target_var, modifiers)` — modify entity attributes
- Custom effects via registry (e.g., `LoanRequest`)

### Integration

`EventService` integrates as a new service in `Game`:
- Loads all `config/events/*.yaml` at init
- Exposes `evaluate_events()` called once per turn (likely in `update_phase` or a dedicated `event_phase`)
- For each event: create fresh Context with `_G`, evaluate expr tree
- If Any/Every/Random find nothing → event short-circuits (If condition is falsy)

### Effect Registry

```python
# effect_registry.py
_registry: Dict[str, Callable[[Context, ...], None]] = {}

def register_effect(name: str, handler: Callable):
    _registry[name] = handler

def execute_effect(name: str, context: Context, **params):
    _registry[name](context, **params)
```

Built-in effects registered at import time. Game-specific effects (LoanRequest etc.) registered by their respective services.

## Evaluation Rules

1. `expr` field is a list of expressions, evaluated sequentially
2. Return value = last expression's value (unused at event level, but enables composability)
3. `Any` iterates `all`, evaluates `condition` for each with the candidate bound to `var`. Returns first truthy match.
4. `Every` same iteration but collects all matches into a list.
5. `Random` collects all matches, picks one uniformly at random.
6. `GetField` with `op`/`value` is syntactic sugar for comparison — returns bool.
7. `ModifyAttr` iterates target (if list) or applies to single entity. Modifier types: `add`, `percent`, `set`.
8. Nested captures: a capture inside another capture's condition is valid — the inner var is bound in the same context.

## Design Decisions

- **Unified expression tree** rather than separate trigger/effect sections — more composable, supports conditional effects naturally
- **YAML-native** — no custom DSL parser needed, leverages YAML's structure
- **Registry for effects** — new effect types added by registering a handler function, no core code changes
- **Context-based scoping** — all variable bindings in a flat dict (sufficient for event complexity level)
- **Per-turn full scan** — simple, no subscription/observer overhead; acceptable for expected event count (<100)
