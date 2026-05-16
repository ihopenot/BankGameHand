# Event System Implementation Plan

**Design doc:** `docs/plans/2026-05-16-event-system-design.md`
**Branch:** `feature/event-system`
**Worktree:** `.worktrees/event-system`

---

## Task Breakdown

### Task 1: Expression Node Base + Core Nodes
**File:** `system/event/expr.py`

Implement:
- `Expr` abstract base class with `evaluate(context) -> Any`
- `Literal(value)` — returns constant
- `GetField(obj_expr, field_name, op=None, value=None)` — attribute access + optional comparison
- `Exprs(exprs: List[Expr])` — sequential eval, return last
- `If(condition: Expr, body: Expr)` — conditional execution
- `And(exprs: List[Expr])` — short-circuit AND
- `Or(exprs: List[Expr])` — short-circuit OR
- `Not(expr: Expr)` — logical negation

### Task 2: Context
**File:** `system/event/context.py`

Implement:
- `EventContext` class with `bindings: Dict[str, Any]`
- Method `get(var_name)` → raises if unbound
- Method `set(var_name, value)` → binds variable
- `_G` injected at construction time as a special binding

### Task 3: Capture Nodes
**File:** `system/event/expr.py` (add to existing)

Implement:
- `Any(all_expr: Expr, condition: Expr, var: str)` — iterate all_expr result, eval condition per item with item bound to var, return first match
- `Every(all_expr: Expr, condition: Expr, var: str)` — collect all matches
- `Random(all_expr: Expr, condition: Expr, var: str)` — random from matches
- On success, leave final binding in context; on failure (none found), unbind var and return falsy

### Task 4: Effect Registry + ModifyAttr
**Files:** `system/event/effect_registry.py`, extend `expr.py`

Implement:
- `EffectRegistry` — dict-based, `register(name, handler)`, `execute(name, context, params)`
- `ModifyAttr` expr node — takes target var name + list of Modifier specs
- Modifier types: `add` (absolute), `percent` (multiplicative), `set` (override)
- Handle both single entity and list targets (iterate if list)

### Task 5: YAML Loader
**File:** `system/event/event_loader.py`

Implement:
- `load_events(path: str) -> List[Event]` — load all .yaml from directory
- `Event` dataclass: `id`, `name`, `expr: Expr`
- `parse_expr(node: Any) -> Expr` — recursive parser that maps YAML structure to Expr nodes
- Handle all node types: If, Any, Every, Random, And, Or, Not, GetField, Exprs, ModifyAttr, Literal
- Handle registered effect names (lookup in registry, create generic `EffectCall` node)

### Task 6: EventService
**File:** `system/event/event_service.py`

Implement:
- `EventService` class
- `__init__(game)` — load events from `config/events/`
- `build_global_context() -> EventContext` — construct `_G` from current game state
- `evaluate_events()` — iterate all events, for each: create context, evaluate expr tree
- Error handling: log and skip events that fail evaluation (don't crash game loop)

### Task 7: Integration + `__init__.py`
**Files:** `system/event/__init__.py`, `game/game.py`

Implement:
- Export public API from `__init__.py`
- Add `EventService` to `Game.__init__`
- Call `event_service.evaluate_events()` in game loop (add event_phase or call in update_phase)

### Task 8: Tests
**File:** `tests/test_event_system.py`

Test cases:
- Expr node evaluation (GetField, And, Or, Not, If, Exprs)
- Capture semantics (Any returns first, Every returns all, Random returns one)
- Nested captures
- ModifyAttr effects (add, percent, set) on single and list targets
- YAML loader produces correct Expr tree
- EventService end-to-end: define event in YAML, verify it fires and modifies entities
- Failure cases: Any finds nothing → event doesn't fire

---

## Execution Order

Tasks 1-2 are independent (parallel).
Task 3 depends on 1+2.
Task 4 depends on 1+2.
Task 5 depends on 1+2+3+4.
Task 6 depends on 5.
Task 7 depends on 6.
Task 8 can start after task 3 (incremental testing).

## Constraints

- Python, no external dependencies beyond PyYAML (already used)
- Follow existing code conventions (type hints, docstrings in Chinese where appropriate)
- Keep the interpreter simple — no optimization needed for <100 events
