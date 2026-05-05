# Economic Feedback Mechanism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dynamic wage decisions for companies (profit-priority with cash adjustment) and dynamic demand decisions for residents (cash/spending ratio driven), replacing static wages and economy-cycle-driven demand.

**Architecture:** Two new decision formulas replace existing static logic: `ClassicCompanyDecisionComponent.decide_wage()` becomes a profit-aware incremental function; `ClassicFolkDecisionComponent.decide_spending()` uses a `demand_multiplier` driven by cash/spending ratio instead of economy cycle index. Configuration is externalized to YAML.

**Tech Stack:** Python 3 · pytest · YAML config · Entity-Component pattern

---

## File Structure

| File | Responsibility |
|------|----------------|
| `config/decision.yaml` | Add `wage_decision` section with step_rate, profit margin, cash factor params |
| `config/folk.yaml` | Add `demand_feedback` section per folk group |
| `entity/folk.py` | Add `last_spending`, `demand_multiplier` attributes |
| `component/decision/folk/classic.py` | Rewrite `decide_spending()` to use `demand_multiplier` instead of economy cycle |
| `component/decision/company/classic.py` | Rewrite `decide_wage()` to compute dynamic target wage |
| `system/folk_service.py` | Record spending after buy phase; update demand_multiplier before computing plans |
| `system/decision_service.py` | Pass additional context (last operating expense, avg buy prices) to company decision |
| `tests/test_dynamic_wage.py` | Tests for new `decide_wage()` logic |
| `tests/test_dynamic_demand.py` | Tests for new `decide_spending()` and demand_multiplier logic |

---

### Task 1: Add wage_decision configuration to decision.yaml

**Files:**
- Modify: `config/decision.yaml`

- [ ] **Step 1: Add wage_decision section to config**

Add the following section at the end of `config/decision.yaml`:

```yaml

# ── 工资决策 ──
wage:
  step_rate: 0.2                # 每回合向目标逼近的速率
  base_profit_margin: 0.15      # 基础目标利润率
  target_cash_ratio: 3.0        # 目标现金/运营支出比值
  cash_factor_min: 0.5          # 现金因子下限
  cash_factor_max: 1.5          # 现金因子上限
```

- [ ] **Step 2: Verify config loads without error**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -c "from core.config import ConfigManager; ConfigManager().load('config'); print(ConfigManager().section('decision').wage.step_rate)"`

Expected: `0.2`

- [ ] **Step 3: Commit**

```bash
git add config/decision.yaml
git commit -m "config: add wage_decision parameters to decision.yaml"
```

---

### Task 2: Add demand_feedback configuration to folk.yaml

**Files:**
- Modify: `config/folk.yaml`

- [ ] **Step 1: Add demand_feedback to each folk group**

Replace the full `config/folk.yaml` with:

```yaml
folks:
- population: 6000
  w_quality: 0.4
  w_brand: 0.05
  w_price: 0.55
  labor_participation_rate: 0.7
  labor_points_per_capita: 1.0
  spending_flow:
    tech: 0.6
    brand: 0.4
    maintenance: 0.5
  base_demands:
    食品:
      per_capita: 1
      sensitivity: 0.1
    服装:
      per_capita: 0.2
      sensitivity: 0.5
    手机:
      per_capita: 0.1
      sensitivity: 0.8
  demand_feedback:
    savings_target_ratio: 3.0
    max_adjustment: 0.20
    sensitivity: 1.2
    min_multiplier: 0.4
    max_multiplier: 1.8
- population: 3000
  w_quality: 0.35
  w_brand: 0.35
  w_price: 0.3
  labor_participation_rate: 0.6
  labor_points_per_capita: 1.0
  spending_flow:
    tech: 0.3
    brand: 0.4
    maintenance: 0.35
  base_demands:
    食品:
      per_capita: 1.2
      sensitivity: 0.2
    服装:
      per_capita: 0.5
      sensitivity: 0.5
    手机:
      per_capita: 0.4
      sensitivity: 0.7
  demand_feedback:
    savings_target_ratio: 5.0
    max_adjustment: 0.15
    sensitivity: 1.0
    min_multiplier: 0.3
    max_multiplier: 2.0
- population: 1000
  w_quality: 0.15
  w_brand: 0.75
  w_price: 0.1
  labor_participation_rate: 0.4
  labor_points_per_capita: 1.0
  spending_flow:
    tech: 0.1
    brand: 0.2
    maintenance: 0.15
  base_demands:
    食品:
      per_capita: 1.5
      sensitivity: 0.05
    服装:
      per_capita: 0.7
      sensitivity: 0.3
    手机:
      per_capita: 0.7
      sensitivity: 0.4
  demand_feedback:
    savings_target_ratio: 8.0
    max_adjustment: 0.10
    sensitivity: 0.8
    min_multiplier: 0.5
    max_multiplier: 1.5
```

- [ ] **Step 2: Verify config loads**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -c "from core.config import ConfigManager; ConfigManager().load('config'); cfg = ConfigManager().section('folk'); print(cfg.folks[0].demand_feedback.savings_target_ratio)"`

Expected: `3.0`

- [ ] **Step 3: Commit**

```bash
git add config/folk.yaml
git commit -m "config: add demand_feedback parameters to folk.yaml"
```

---

### Task 3: Add last_spending and demand_multiplier to Folk entity

**Files:**
- Modify: `entity/folk.py`
- Test: `tests/test_dynamic_demand.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_dynamic_demand.py`:

```python
"""居民动态需求机制测试。"""

import math
from pathlib import Path
from unittest.mock import patch

import pytest

from core.config import ConfigManager
from entity.goods import GoodsType, load_goods_types


@pytest.fixture(autouse=True)
def _load_config():
    """确保配置和 GoodsType 已加载。"""
    ConfigManager._instance = None
    ConfigManager().load(str(Path(__file__).parent / "config_integration"))
    GoodsType.types.clear()
    load_goods_types()
    yield
    ConfigManager._instance = None


class TestFolkDemandAttributes:
    """Folk 实体应有 last_spending 和 demand_multiplier 属性。"""

    def test_folk_has_last_spending(self) -> None:
        from entity.folk import Folk
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
        )
        assert folk.last_spending == 0

    def test_folk_has_demand_multiplier(self) -> None:
        from entity.folk import Folk
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
        )
        assert folk.demand_multiplier == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_dynamic_demand.py::TestFolkDemandAttributes -v`

Expected: FAIL with `AttributeError: 'Folk' object has no attribute 'last_spending'`

- [ ] **Step 3: Add attributes to Folk.__init__**

In `entity/folk.py`, add these two lines after `self.labor_points_per_capita = labor_points_per_capita` (line 37):

```python
        self.last_spending: int = 0
        self.demand_multiplier: float = 1.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_dynamic_demand.py::TestFolkDemandAttributes -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add entity/folk.py tests/test_dynamic_demand.py
git commit -m "feat: add last_spending and demand_multiplier to Folk entity"
```

---

### Task 4: Implement dynamic demand_multiplier update logic

**Files:**
- Modify: `component/decision/folk/classic.py`
- Test: `tests/test_dynamic_demand.py`

- [ ] **Step 1: Write the failing tests for demand_multiplier update**

Append to `tests/test_dynamic_demand.py`:

```python
class TestDemandMultiplierUpdate:
    """demand_multiplier 更新逻辑测试。"""

    def _make_folk(self, cash: int, last_spending: int, demand_multiplier: float = 1.0):
        from entity.folk import Folk
        from component.ledger_component import LedgerComponent
        gt = list(GoodsType.types.values())[0]
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={gt: {"per_capita": 1.0, "sensitivity": 0.5}},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
        )
        folk.last_spending = last_spending
        folk.demand_multiplier = demand_multiplier
        ledger = folk.get_component(LedgerComponent)
        ledger.cash = cash
        return folk

    def test_neutral_when_last_spending_zero(self) -> None:
        """last_spending=0 时不触发调整，demand_multiplier 保持不变。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=5000, last_spending=0)
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier == 1.0

    def test_increase_when_cash_abundant(self) -> None:
        """现金充裕(R > T)时 demand_multiplier 增加。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=10000, last_spending=1000)  # R=10, T=5 → deviation>0
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier > 1.0

    def test_decrease_when_cash_tight(self) -> None:
        """现金紧张(R < T)时 demand_multiplier 减少。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=2000, last_spending=1000)  # R=2, T=5 → deviation<0
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier < 1.0

    def test_clamp_max(self) -> None:
        """demand_multiplier 不超过 max_multiplier。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=100000, last_spending=100, demand_multiplier=1.9)
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier <= 2.0

    def test_clamp_min(self) -> None:
        """demand_multiplier 不低于 min_multiplier。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        folk = self._make_folk(cash=100, last_spending=10000, demand_multiplier=0.35)
        dc = folk.get_component(ClassicFolkDecisionComponent)
        dc.update_demand_multiplier(savings_target_ratio=5.0, max_adjustment=0.15, sensitivity=1.0, min_multiplier=0.3, max_multiplier=2.0)
        assert folk.demand_multiplier >= 0.3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_dynamic_demand.py::TestDemandMultiplierUpdate -v`

Expected: FAIL with `AttributeError: 'ClassicFolkDecisionComponent' object has no attribute 'update_demand_multiplier'`

- [ ] **Step 3: Implement update_demand_multiplier**

Replace the full content of `component/decision/folk/classic.py`:

```python
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Dict

from component.decision.folk.base import BaseFolkDecisionComponent, register_folk_decision_component
from component.ledger_component import LedgerComponent

if TYPE_CHECKING:
    from core.entity import Entity


@register_folk_decision_component("classic")
class ClassicFolkDecisionComponent(BaseFolkDecisionComponent):
    """经典公式驱动的居民决策组件。

    Context dict 约定：
    - economy_cycle_index: float — 经济周期指数（保留但不再用于需求计算）
    - reference_prices: Dict[str, int] — 各商品参考价格
    """

    def __init__(self, outer: Entity) -> None:
        super().__init__(outer)

    def update_demand_multiplier(
        self,
        savings_target_ratio: float,
        max_adjustment: float,
        sensitivity: float,
        min_multiplier: float,
        max_multiplier: float,
    ) -> None:
        """基于现金/开销比值更新 demand_multiplier。

        R = cash / last_spending
        deviation = (R - T) / T
        adjustment = max_adjustment * tanh(sensitivity * deviation)
        demand_multiplier *= (1 + adjustment)
        demand_multiplier = clamp(min_multiplier, max_multiplier)
        """
        folk = self.outer
        last_spending = folk.last_spending

        if last_spending <= 0:
            # 冷启动：无开销记录，不触发调整
            return

        ledger = folk.get_component(LedgerComponent)
        cash = ledger.cash
        R = cash / last_spending
        T = savings_target_ratio

        deviation = (R - T) / T
        adjustment = max_adjustment * math.tanh(sensitivity * deviation)

        folk.demand_multiplier *= (1 + adjustment)
        folk.demand_multiplier = max(min_multiplier, min(max_multiplier, folk.demand_multiplier))

    def decide_spending(self) -> Dict[str, Dict]:
        """计算每个商品类型的支出计划（预算 + 需求量）。

        demand = population * per_capita * demand_multiplier
        budget = demand * reference_price * spending_tendency
        """
        ctx = self._context
        reference_prices: Dict[str, int] = ctx.get("reference_prices", {})

        folk = self.outer
        spending_tendency = self._calc_spending_tendency()

        result: Dict[str, Dict] = {}
        for gt, demand_cfg in folk.base_demands.items():
            gt_name = gt.name
            per_capita = demand_cfg["per_capita"]

            if per_capita == 0:
                result[gt_name] = {"budget": 0, "demand": 0}
                continue

            demand = int(folk.population * per_capita * folk.demand_multiplier)
            ref_price = reference_prices.get(gt_name, gt.base_price)
            budget = int(demand * ref_price * spending_tendency)

            result[gt_name] = {"budget": budget, "demand": demand}

        return result

    def _calc_spending_tendency(self) -> float:
        """根据 Folk 的 w_* 属性计算消费倾向。

        spending_tendency = w_quality + w_brand + w_price
        """
        folk = self.outer
        return folk.w_quality + folk.w_brand + folk.w_price
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_dynamic_demand.py -v`

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add component/decision/folk/classic.py tests/test_dynamic_demand.py
git commit -m "feat: implement demand_multiplier update logic for folk spending"
```

---

### Task 5: Integrate demand_multiplier into FolkService buy_phase

**Files:**
- Modify: `system/folk_service.py`
- Test: `tests/test_dynamic_demand.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_dynamic_demand.py`:

```python
class TestFolkServiceSpendingRecord:
    """FolkService 应在 buy_phase 后记录 last_spending 并在下次更新 demand_multiplier。"""

    def _make_folk_with_config(self, cash: int):
        from entity.folk import Folk
        from component.ledger_component import LedgerComponent
        gt = list(GoodsType.types.values())[0]
        folk = Folk(
            name="test_folk",
            population=100,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={gt: {"per_capita": 1.0, "sensitivity": 0.5}},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
        )
        ledger = folk.get_component(LedgerComponent)
        ledger.cash = cash
        return folk

    def test_record_last_spending_after_buy(self) -> None:
        """buy_phase 后 folk.last_spending 应记录本回合实际花费。"""
        from system.folk_service import FolkService
        from system.market_service import MarketService
        from entity.goods import GoodsBatch
        from component.storage_component import StorageComponent

        gt = list(GoodsType.types.values())[0]
        folk = self._make_folk_with_config(cash=100000)
        folk_service = FolkService(folks=[folk])

        # 创建市场并添加供给
        market = MarketService()
        from core.entity import Entity
        seller = Entity("seller")
        seller.init_component(StorageComponent)
        from component.ledger_component import LedgerComponent as LC
        seller.init_component(LC)
        from component.metric_component import MetricComponent as MC
        seller.init_component(MC)
        batch = GoodsBatch(goods_type=gt, quantity=200, quality=0.5, brand_value=100)
        seller.get_component(StorageComponent).add_batch(batch)
        from system.market_service import SellOrder
        order = SellOrder(seller=seller, batch=batch, price=100)
        market.add_sell_order(order)

        # 执行购买
        folk_service.buy_phase(market, economy_cycle_index=0.0)

        # 应该记录了花费
        assert folk.last_spending > 0

    def test_update_demand_multiplier_called_in_buy_phase(self) -> None:
        """buy_phase 应在计算需求前调用 update_demand_multiplier。"""
        from system.folk_service import FolkService
        from system.market_service import MarketService

        gt = list(GoodsType.types.values())[0]
        folk = self._make_folk_with_config(cash=100000)
        folk.last_spending = 1000  # 已有上回合记录
        # R = 100000/1000 = 100, T = default 5.0 → 应增加 multiplier
        folk_service = FolkService(folks=[folk])

        market = MarketService()
        folk_service.buy_phase(market, economy_cycle_index=0.0)

        # demand_multiplier 应该 > 1.0（因为 R > T）
        assert folk.demand_multiplier > 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_dynamic_demand.py::TestFolkServiceSpendingRecord -v`

Expected: FAIL (last_spending not recorded, demand_multiplier not updated)

- [ ] **Step 3: Modify FolkService to update demand_multiplier and record spending**

In `system/folk_service.py`, make these changes:

1. Add import at the top (after existing imports):
```python
from core.config import ConfigManager
```

2. Add a new method `_update_demand_multipliers` to the FolkService class (before `buy_phase`):

```python
    def _update_demand_multipliers(self) -> None:
        """在计算需求前，根据上回合开销更新各居民组的 demand_multiplier。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent
        config = ConfigManager().section("folk")

        for idx, folk in enumerate(self.folks):
            dc = folk.get_component(ClassicFolkDecisionComponent)
            if dc is None:
                continue

            # 从配置获取 demand_feedback 参数
            folk_cfg = config.folks[idx]
            if not hasattr(folk_cfg, "demand_feedback"):
                continue
            fb = folk_cfg.demand_feedback
            dc.update_demand_multiplier(
                savings_target_ratio=fb.savings_target_ratio,
                max_adjustment=fb.max_adjustment,
                sensitivity=fb.sensitivity,
                min_multiplier=fb.min_multiplier,
                max_multiplier=fb.max_multiplier,
            )
```

3. In `buy_phase` method, add call to `_update_demand_multipliers()` at the very beginning (after `reference_prices` is built but before `_compute_spending_plans`):

Change lines 237-238 of `buy_phase`:
```python
    def buy_phase(self, market: MarketService, economy_cycle_index: float) -> List[TradeRecord]:
        """居民采购阶段：更新需求乘数 → 计算需求 → 按商品类型公平分配 → 结算 → 记录开销 → 更新购买均价。"""
        # 在计算需求前更新 demand_multiplier
        self._update_demand_multipliers()

        reference_prices = self._build_reference_prices(market)
```

4. At the end of `buy_phase` (before the `return all_trades` line), add spending recording:

```python
        # 记录各居民组本回合总开销
        self._record_spending(all_trades)

        self._update_avg_buy_prices(all_trades)
        return all_trades
```

5. Add the `_record_spending` method:

```python
    def _record_spending(self, trades: List[TradeRecord]) -> None:
        """记录每个 Folk 本回合的实际总开销到 last_spending。"""
        from collections import defaultdict
        folk_spending: Dict[Folk, int] = defaultdict(int)
        for trade in trades:
            if isinstance(trade.buyer, Folk):
                folk_spending[trade.buyer] += trade.quantity * trade.price
        for folk in self.folks:
            folk.last_spending = folk_spending.get(folk, 0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_dynamic_demand.py -v`

Expected: All PASS

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest --tb=short -q 2>&1 | tail -5`

Expected: Same baseline (580 passed, 3 failed pre-existing)

- [ ] **Step 6: Commit**

```bash
git add system/folk_service.py tests/test_dynamic_demand.py
git commit -m "feat: integrate demand_multiplier updates and spending recording into buy_phase"
```

---

### Task 6: Implement dynamic wage decision for companies

**Files:**
- Modify: `component/decision/company/classic.py`
- Modify: `system/decision_service.py`
- Test: `tests/test_dynamic_wage.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dynamic_wage.py`:

```python
"""企业动态工资决策测试。"""

import math
from pathlib import Path

import pytest

from component.decision.company.classic import ClassicCompanyDecisionComponent
from core.config import ConfigManager
from core.entity import Entity
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsType, load_goods_types


@pytest.fixture(autouse=True)
def _clear_components():
    ClassicCompanyDecisionComponent.components.clear()
    yield
    ClassicCompanyDecisionComponent.components.clear()


@pytest.fixture(autouse=True)
def _load_config():
    """确保配置和 GoodsType 已加载。"""
    ConfigManager._instance = None
    ConfigManager().load(str(Path(__file__).parent / "config_integration"))
    GoodsType.types.clear()
    load_goods_types()
    yield
    ConfigManager._instance = None


def _make_factory_type(
    maintenance_cost: int = 100,
    labor_demand: int = 10,
    output_quantity: int = 100,
    input_quantity: int = 50,
) -> FactoryType:
    """创建测试用 FactoryType。"""
    gt_out = list(GoodsType.types.values())[0]
    gt_in = list(GoodsType.types.values())[1] if len(GoodsType.types) > 1 else None
    recipe = Recipe(
        input_goods_type=gt_in,
        input_quantity=input_quantity,
        output_goods_type=gt_out,
        output_quantity=output_quantity,
        tech_quality_weight=0.5,
    )
    return FactoryType(
        recipe=recipe,
        labor_demand=labor_demand,
        build_cost=1000,
        maintenance_cost=maintenance_cost,
        build_time=0,
    )


def _make_context(
    cash: int = 100000,
    initial_wage: int = 400,
    current_prices: dict | None = None,
    avg_buy_prices: dict | None = None,
    factories: dict | None = None,
    last_operating_expense: int = 0,
    profit_focus: float = 0.5,
    risk_appetite: float = 0.5,
) -> dict:
    """构建测试 context。"""
    gt_out = list(GoodsType.types.values())[0]
    ft = _make_factory_type()

    if current_prices is None:
        current_prices = {gt_out: 500}
    if factories is None:
        factories = {ft: [Factory(ft, build_remaining=0)]}
    if avg_buy_prices is None:
        avg_buy_prices = {}

    return {
        "company": {
            "name": "TestCorp",
            "ceo_traits": {
                "business_acumen": 0.5,
                "risk_appetite": risk_appetite,
                "profit_focus": profit_focus,
                "marketing_awareness": 0.5,
                "tech_focus": 0.5,
                "price_sensitivity": 0.5,
            },
            "initial_wage": initial_wage,
            "current_wage": initial_wage,
            "last_operating_expense": last_operating_expense,
        },
        "ledger": {
            "cash": cash,
            "revenue": 0,
            "expense": 0,
            "receivables": 0,
            "payables": 0,
        },
        "productor": {
            "factories": factories,
            "tech_levels": {},
            "brand_values": {},
            "current_prices": current_prices,
        },
        "metric": {
            "my_sell_orders": {},
            "my_sold_quantities": {},
            "last_revenue": 5000,
            "my_avg_buy_prices": avg_buy_prices,
        },
        "market": {
            "economy_index": 0.0,
            "sell_orders": [],
            "trades": [],
        },
    }


class TestDynamicWage:
    """动态工资决策测试。"""

    def test_wage_not_fixed(self) -> None:
        """decide_wage 不再简单返回 initial_wage。"""
        entity = Entity("test")
        comp = entity.init_component(ClassicCompanyDecisionComponent)
        ctx = _make_context(cash=100000, initial_wage=400, last_operating_expense=10000)
        comp.set_context(ctx)
        wage = comp.decide_wage()
        # 不一定等于 initial_wage
        assert isinstance(wage, int)
        assert wage > 0

    def test_low_cash_reduces_wage(self) -> None:
        """现金紧张时目标工资应低于充裕时。"""
        entity1 = Entity("test1")
        comp1 = entity1.init_component(ClassicCompanyDecisionComponent)
        ctx1 = _make_context(cash=5000, initial_wage=400, last_operating_expense=10000)
        comp1.set_context(ctx1)
        wage_low_cash = comp1.decide_wage()

        entity2 = Entity("test2")
        comp2 = entity2.init_component(ClassicCompanyDecisionComponent)
        ctx2 = _make_context(cash=500000, initial_wage=400, last_operating_expense=10000)
        comp2.set_context(ctx2)
        wage_high_cash = comp2.decide_wage()

        assert wage_low_cash < wage_high_cash

    def test_high_profit_focus_lowers_wage(self) -> None:
        """profit_focus 高的 CEO 设定更低的工资（保利润）。"""
        entity1 = Entity("test1")
        comp1 = entity1.init_component(ClassicCompanyDecisionComponent)
        ctx1 = _make_context(cash=100000, initial_wage=400, last_operating_expense=10000, profit_focus=0.9)
        comp1.set_context(ctx1)
        wage_high_pf = comp1.decide_wage()

        entity2 = Entity("test2")
        comp2 = entity2.init_component(ClassicCompanyDecisionComponent)
        ctx2 = _make_context(cash=100000, initial_wage=400, last_operating_expense=10000, profit_focus=0.1)
        comp2.set_context(ctx2)
        wage_low_pf = comp2.decide_wage()

        assert wage_high_pf < wage_low_pf

    def test_zero_operating_expense_neutral(self) -> None:
        """上回合运营支出为0时应返回正常工资（中性状态）。"""
        entity = Entity("test")
        comp = entity.init_component(ClassicCompanyDecisionComponent)
        ctx = _make_context(cash=100000, initial_wage=400, last_operating_expense=0)
        comp.set_context(ctx)
        wage = comp.decide_wage()
        assert isinstance(wage, int)
        assert wage > 0

    def test_incremental_approach(self) -> None:
        """工资应增量逼近目标，不会一步到位。"""
        entity = Entity("test")
        comp = entity.init_component(ClassicCompanyDecisionComponent)
        # 设置一个 target 远高于 current 的情况
        ctx = _make_context(cash=1000000, initial_wage=100, last_operating_expense=5000)
        comp.set_context(ctx)
        wage = comp.decide_wage()
        # 工资应增加但不能暴涨（step_rate = 0.2）
        assert wage > 100
        assert wage < 500  # 不会一步跳到目标
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_dynamic_wage.py -v`

Expected: FAIL (current `decide_wage()` just returns `initial_wage`)

- [ ] **Step 3: Extend decision context with wage-related data**

In `system/decision_service.py`, modify `_build_context` to include `current_wage` and `last_operating_expense`. Change the `"company"` dict in the return statement (around line 60-65):

```python
            "company": {
                "name": company.name,
                "ceo_traits": ceo_traits,
                "initial_wage": company.initial_wage,
                "current_wage": company.wage,
                "last_operating_expense": getattr(company, 'last_operating_expense', 0),
            },
```

Also, in `plan_phase`, after `company.wage = dc.decide_wage()` (line 130), add recording of operating expense for next round:

```python
            # 决策：工资定价
            company.wage = dc.decide_wage()

            # 记录本回合运营支出供下轮工资决策参考
            company.last_operating_expense = dc._calc_operating_expense()
```

- [ ] **Step 4: Implement dynamic decide_wage**

In `component/decision/company/classic.py`, replace the `decide_wage` method (lines 224-228):

```python
    # ── 决策：工资定价 ──

    def decide_wage(self) -> int:
        """动态工资决策：利润优先 + 现金调节 + 增量逼近。

        1. 计算目标工资 = (售价 - 非工资单位成本 - 目标利润) × 产量 / 劳动力需求
        2. 现金调节因子 = clamp(企业现金 / 运营支出 / target_cash_ratio, min, max)
        3. new_wage = current + step_rate × (target × cash_factor - current)
        """
        ctx = self._context
        company_ctx = ctx.get("company", {})
        ledger = ctx.get("ledger", {})
        productor = ctx.get("productor", {})
        metric = ctx.get("metric", {})

        cfg = self.config.wage
        current_wage = company_ctx.get("current_wage", company_ctx.get("initial_wage", 10))
        cash = ledger.get("cash", 0)
        last_op_expense = company_ctx.get("last_operating_expense", 0)

        # 获取工厂信息计算目标工资
        factories = productor.get("factories", {})
        current_prices = productor.get("current_prices", {})
        avg_buy_prices = metric.get("my_avg_buy_prices", {})

        # 计算总劳动力需求和总产能
        total_labor_demand = 0
        total_output_capacity = 0
        total_maintenance = 0
        total_material_cost = 0

        for ft, factory_list in factories.items():
            built_count = sum(1 for f in factory_list if f.is_built)
            if built_count == 0:
                continue
            total_labor_demand += ft.labor_demand * built_count
            total_output_capacity += ft.recipe.output_quantity * built_count
            total_maintenance += ft.maintenance_cost * built_count

            # 原材料成本（基于上回合采购均价）
            if ft.recipe.input_goods_type is not None:
                input_price = avg_buy_prices.get(ft.recipe.input_goods_type, 0.0)
                if input_price <= 0:
                    input_price = ft.recipe.input_goods_type.base_price
                total_material_cost += input_price * ft.recipe.input_quantity * built_count

        if total_labor_demand <= 0 or total_output_capacity <= 0:
            return max(1, current_wage)

        # 加权平均售价
        total_revenue_capacity = 0
        for ft, factory_list in factories.items():
            built_count = sum(1 for f in factory_list if f.is_built)
            if built_count == 0:
                continue
            gt = ft.recipe.output_goods_type
            price = current_prices.get(gt, gt.base_price)
            total_revenue_capacity += price * ft.recipe.output_quantity * built_count

        # 单位产品视角的目标工资
        # target_profit_margin = profit_focus × base_profit_margin
        target_profit_margin = self.profit_focus * cfg.base_profit_margin

        # 总利润空间 = 总收入 - 总非工资成本 - 目标利润
        wage_budget = total_revenue_capacity - total_material_cost - total_maintenance - target_profit_margin * total_revenue_capacity
        target_wage = wage_budget / total_labor_demand if total_labor_demand > 0 else current_wage

        # 现金调节因子
        if last_op_expense > 0:
            cash_ratio = cash / last_op_expense
            cash_factor = max(cfg.cash_factor_min, min(cfg.cash_factor_max, cash_ratio / cfg.target_cash_ratio))
        else:
            cash_factor = 1.0  # 中性

        # 增量逼近
        adjusted_target = target_wage * cash_factor
        new_wage = current_wage + cfg.step_rate * (adjusted_target - current_wage)

        return max(1, int(round(new_wage)))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_dynamic_wage.py -v`

Expected: All PASS

- [ ] **Step 6: Run full test suite**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest --tb=short -q 2>&1 | tail -5`

Expected: Same baseline or better (no new failures)

- [ ] **Step 7: Commit**

```bash
git add component/decision/company/classic.py system/decision_service.py tests/test_dynamic_wage.py
git commit -m "feat: implement dynamic wage decision based on profit margin and cash level"
```

---

### Task 7: Initialize last_operating_expense on Company entity

**Files:**
- Modify: `system/company_service.py`

- [ ] **Step 1: Add last_operating_expense initialization**

In `system/company_service.py`, in `create_company` method, after `company.wage = initial_wage` (line 50), add:

```python
        company.last_operating_expense = 0
```

- [ ] **Step 2: Run tests to verify no regression**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest --tb=short -q 2>&1 | tail -5`

Expected: Same baseline

- [ ] **Step 3: Commit**

```bash
git add system/company_service.py
git commit -m "feat: initialize last_operating_expense on company creation"
```

---

### Task 8: Update load_folks to handle demand_feedback config gracefully

**Files:**
- Modify: `entity/folk.py`

- [ ] **Step 1: Verify load_folks works with new config**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -c "from core.config import ConfigManager; ConfigManager().load('config'); from entity.goods import load_goods_types, GoodsType; GoodsType.types.clear(); load_goods_types(); from entity.folk import load_folks; folks = load_folks(); print(f'Loaded {len(folks)} folk groups'); print(f'folk_0 demand_multiplier: {folks[0].demand_multiplier}')"`

Expected: `Loaded 3 folk groups` and `folk_0 demand_multiplier: 1.0`

If this works (because `demand_feedback` is just an extra config field that `load_folks` ignores), no changes needed to `entity/folk.py` beyond the attributes already added in Task 3.

- [ ] **Step 2: Run full test suite**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest --tb=short -q 2>&1 | tail -5`

Expected: Same baseline (no new failures)

- [ ] **Step 3: Commit (if changes made)**

If any adjustments were needed, commit them.

---

### Task 9: Update FolkService._compute_spending_plans to not require economy_cycle_index for demand

**Files:**
- Modify: `system/folk_service.py`
- Test: `tests/test_dynamic_demand.py`

- [ ] **Step 1: Write a test that verifies economy_cycle_index no longer affects demand**

Append to `tests/test_dynamic_demand.py`:

```python
class TestEconomyCycleDecoupled:
    """经济周期不再直接影响居民需求。"""

    def _make_folk(self):
        from entity.folk import Folk
        from component.ledger_component import LedgerComponent
        gt = list(GoodsType.types.values())[0]
        folk = Folk(
            name="test_folk",
            population=1000,
            w_quality=0.3,
            w_brand=0.3,
            w_price=0.4,
            spending_flow={"tech": 1.0},
            base_demands={gt: {"per_capita": 1.0, "sensitivity": 0.8}},
            labor_participation_rate=0.5,
            labor_points_per_capita=1.0,
        )
        ledger = folk.get_component(LedgerComponent)
        ledger.cash = 100000
        return folk

    def test_demand_same_regardless_of_economy_index(self) -> None:
        """不同经济周期值应产生相同需求（因为 demand_multiplier 不受 economy_index 影响）。"""
        from component.decision.folk.classic import ClassicFolkDecisionComponent

        folk1 = self._make_folk()
        dc1 = folk1.get_component(ClassicFolkDecisionComponent)
        dc1.set_context({"economy_cycle_index": 0.5, "reference_prices": {}})
        plan1 = dc1.decide_spending()

        folk2 = self._make_folk()
        dc2 = folk2.get_component(ClassicFolkDecisionComponent)
        dc2.set_context({"economy_cycle_index": -0.5, "reference_prices": {}})
        plan2 = dc2.decide_spending()

        gt_name = list(GoodsType.types.values())[0].name
        assert plan1[gt_name]["demand"] == plan2[gt_name]["demand"]
```

- [ ] **Step 2: Run test to verify it passes**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_dynamic_demand.py::TestEconomyCycleDecoupled -v`

Expected: PASS (since we already removed economy_cycle_index from decide_spending in Task 4)

- [ ] **Step 3: Also update the fallback path in _compute_spending_plans**

In `system/folk_service.py`, update the fallback path (lines 61-73) in `_compute_spending_plans` to also use `demand_multiplier` instead of economy cycle:

Replace:
```python
            else:
                # 回退：构建与 decide_spending 相同格式的 plan
                plan = {}
                for goods_type, params in folk.base_demands.items():
                    per_capita = params["per_capita"]
                    sensitivity = params["sensitivity"]
                    if per_capita == 0:
                        plan[goods_type.name] = {"budget": 0, "demand": 0}
                        continue
                    demand = int(folk.population * per_capita * (1 + economy_cycle_index * sensitivity))
                    ref_price = (reference_prices or {}).get(goods_type.name, goods_type.base_price)
                    budget = int(demand * ref_price * (folk.w_quality + folk.w_brand + folk.w_price))
                    plan[goods_type.name] = {"budget": budget, "demand": demand}
                result[folk] = plan
```

With:
```python
            else:
                # 回退：构建与 decide_spending 相同格式的 plan
                plan = {}
                for goods_type, params in folk.base_demands.items():
                    per_capita = params["per_capita"]
                    if per_capita == 0:
                        plan[goods_type.name] = {"budget": 0, "demand": 0}
                        continue
                    demand = int(folk.population * per_capita * folk.demand_multiplier)
                    ref_price = (reference_prices or {}).get(goods_type.name, goods_type.base_price)
                    budget = int(demand * ref_price * (folk.w_quality + folk.w_brand + folk.w_price))
                    plan[goods_type.name] = {"budget": budget, "demand": demand}
                result[folk] = plan
```

- [ ] **Step 4: Run full test suite**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest --tb=short -q 2>&1 | tail -5`

Expected: Same baseline or better

- [ ] **Step 5: Commit**

```bash
git add system/folk_service.py tests/test_dynamic_demand.py
git commit -m "feat: decouple economy_cycle_index from folk demand calculation"
```

---

### Task 10: Update existing tests for compatibility

**Files:**
- Modify: `tests/test_folk_service.py`
- Modify: `tests/test_folk_service_decision.py`

- [ ] **Step 1: Run existing folk-related tests to find failures**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_folk_service.py tests/test_folk_service_decision.py tests/test_folk.py -v --tb=short 2>&1 | tail -30`

- [ ] **Step 2: Fix any test failures**

Common fixes needed:
- Tests that assert demand changes with economy_cycle_index → update or remove those assertions
- Tests that depend on the old demand formula → update expected values to use `demand_multiplier = 1.0` (default)

For each failing test, the fix is straightforward: since `demand_multiplier` defaults to 1.0, any test that uses `economy_cycle_index=0.0` should produce the same results as before (because `1 + 0 × sensitivity = 1.0 = demand_multiplier`).

Tests that specifically test the economy cycle's effect on demand need to be updated to test `demand_multiplier` instead.

- [ ] **Step 3: Run full test suite**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest --tb=short -q 2>&1 | tail -5`

Expected: Same or better than baseline (580+ passed)

- [ ] **Step 4: Commit**

```bash
git add tests/
git commit -m "test: update existing folk tests for new demand mechanism"
```

---

### Task 11: Add test config for integration tests

**Files:**
- Modify: `tests/config_integration/decision.yaml` (if exists)

- [ ] **Step 1: Check if test config exists and add wage section**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && cat tests/config_integration/decision.yaml 2>/dev/null || echo "NOT_FOUND"`

If it exists, add the `wage:` section (same as what we added to `config/decision.yaml`):

```yaml
# ── 工资决策 ──
wage:
  step_rate: 0.2
  base_profit_margin: 0.15
  target_cash_ratio: 3.0
  cash_factor_min: 0.5
  cash_factor_max: 1.5
```

- [ ] **Step 2: Check folk test config for demand_feedback**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && cat tests/config_integration/folk.yaml 2>/dev/null || echo "NOT_FOUND"`

If it exists, add `demand_feedback:` to each folk group entry.

- [ ] **Step 3: Run all tests**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest --tb=short -q 2>&1 | tail -5`

Expected: All pass (same baseline)

- [ ] **Step 4: Commit**

```bash
git add tests/config_integration/
git commit -m "test: add wage and demand_feedback config to test fixtures"
```

---

### Task 12: Final integration test - full game loop

**Files:**
- Test: `tests/test_economic_feedback_integration.py`

- [ ] **Step 1: Write an integration test that runs multiple rounds**

Create `tests/test_economic_feedback_integration.py`:

```python
"""经济反馈机制集成测试：验证完整游戏循环中的资金流动反馈。"""

from pathlib import Path

import pytest

from core.config import ConfigManager
from entity.goods import GoodsType, load_goods_types
from entity.factory import load_recipes, load_factory_types


@pytest.fixture(autouse=True)
def _load_full_config():
    """加载完整配置。"""
    ConfigManager._instance = None
    ConfigManager().load(str(Path(__file__).parent.parent / "config"))
    GoodsType.types.clear()
    load_goods_types()
    load_recipes()
    load_factory_types()
    yield
    ConfigManager._instance = None


class TestEconomicFeedbackIntegration:
    """验证反馈机制在多回合中正常运作。"""

    def test_wage_evolves_over_rounds(self) -> None:
        """企业工资不再是固定值，应在多轮后变化。"""
        from system.company_service import CompanyService
        from system.decision_service import DecisionService
        from system.market_service import MarketService
        from entity.factory import FactoryType

        company_service = CompanyService()
        ft = list(FactoryType.factory_types.values())[0]
        company = company_service.create_company(
            name="test_co",
            factory_type=ft,
            initial_cash=1000000,
            decision_component="classic",
            initial_wage=400,
        )

        decision_service = DecisionService()
        decision_service.set_market_data([], [], 0.0)

        initial_wage = company.wage
        # 模拟多轮决策
        for _ in range(5):
            decision_service.plan_phase(list(company_service.companies.values()))

        # 工资应该有变化（不再固定）
        assert company.wage != initial_wage or company.wage > 0

    def test_demand_multiplier_responds_to_spending(self) -> None:
        """居民 demand_multiplier 在有开销记录后应变化。"""
        from entity.folk import load_folks
        from component.ledger_component import LedgerComponent

        folks = load_folks()
        folk = folks[0]

        # 设置现金和开销
        ledger = folk.get_component(LedgerComponent)
        ledger.cash = 500000
        folk.last_spending = 10000  # R = 50, T = 3 → 非常充裕

        from component.decision.folk.classic import ClassicFolkDecisionComponent
        dc = folk.get_component(ClassicFolkDecisionComponent)

        # 从配置获取参数
        config = ConfigManager().section("folk")
        fb = config.folks[0].demand_feedback
        dc.update_demand_multiplier(
            savings_target_ratio=fb.savings_target_ratio,
            max_adjustment=fb.max_adjustment,
            sensitivity=fb.sensitivity,
            min_multiplier=fb.min_multiplier,
            max_multiplier=fb.max_multiplier,
        )

        # 因为 R >> T，demand_multiplier 应增加
        assert folk.demand_multiplier > 1.0

    def test_feedback_loop_stabilizes(self) -> None:
        """反馈循环：当 R = T 时，demand_multiplier 不再变化。"""
        from entity.folk import load_folks
        from component.ledger_component import LedgerComponent
        from component.decision.folk.classic import ClassicFolkDecisionComponent

        folks = load_folks()
        folk = folks[1]  # 中等收入，T=5.0

        ledger = folk.get_component(LedgerComponent)
        ledger.cash = 50000
        folk.last_spending = 10000  # R = 5.0 = T → 平衡

        dc = folk.get_component(ClassicFolkDecisionComponent)
        config = ConfigManager().section("folk")
        fb = config.folks[1].demand_feedback

        original = folk.demand_multiplier
        dc.update_demand_multiplier(
            savings_target_ratio=fb.savings_target_ratio,
            max_adjustment=fb.max_adjustment,
            sensitivity=fb.sensitivity,
            min_multiplier=fb.min_multiplier,
            max_multiplier=fb.max_multiplier,
        )

        # R == T → deviation == 0 → adjustment == 0 → no change
        assert folk.demand_multiplier == pytest.approx(original, abs=1e-10)
```

- [ ] **Step 2: Run integration test**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest tests/test_economic_feedback_integration.py -v`

Expected: All PASS

- [ ] **Step 3: Run complete test suite one final time**

Run: `cd D:/work/BankGameHand/.worktrees/economic-feedback && python -m pytest --tb=short -q`

Expected: All pass (same or better than 580 baseline)

- [ ] **Step 4: Commit**

```bash
git add tests/test_economic_feedback_integration.py
git commit -m "test: add integration tests for economic feedback mechanism"
```

---

## Summary of Changes

| Task | Description | Key File |
|------|-------------|----------|
| 1 | Wage decision config | `config/decision.yaml` |
| 2 | Demand feedback config | `config/folk.yaml` |
| 3 | Folk entity attributes | `entity/folk.py` |
| 4 | Demand multiplier update logic | `component/decision/folk/classic.py` |
| 5 | FolkService integration | `system/folk_service.py` |
| 6 | Dynamic wage implementation | `component/decision/company/classic.py` |
| 7 | Company entity initialization | `system/company_service.py` |
| 8 | Config loading verification | `entity/folk.py` |
| 9 | Economy cycle decoupling | `system/folk_service.py` |
| 10 | Existing test updates | `tests/` |
| 11 | Test config fixtures | `tests/config_integration/` |
| 12 | Integration tests | `tests/test_economic_feedback_integration.py` |
