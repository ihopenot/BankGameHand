# Map & Country System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a map/country system where companies belong to plots, plots belong to countries with neighbor relationships, and all of this is displayed in game output.

**Architecture:** Flat structure with Country and Plot as dataclasses, managed by a MapService that loads from `config/map.yaml`. Company gains a `plot` attribute assigned during creation. PlayerService gains a map panel and a "plot" column in the company table.

**Tech Stack:** Python 3, dataclasses, PyYAML (existing), Rich library (existing), pytest

---

## File Structure

| File | Responsibility |
|------|---------------|
| `entity/map.py` (create) | Country and Plot dataclass definitions |
| `system/map_service.py` (create) | Load map config, validate neighbors, provide query API |
| `config/map.yaml` (create) | Country and plot definitions with neighbor relationships |
| `config/game.yaml` (modify) | Add `plot` field to each company config entry |
| `entity/company/company.py` (modify) | Add `plot: Optional[Plot]` attribute |
| `system/company_service.py` (modify) | Accept and assign `plot` during `create_company` |
| `game/game.py` (modify) | Initialize MapService, pass plot to company creation |
| `system/player_service.py` (modify) | Add plot column to company table, add map panel rendering |
| `tests/test_map_service.py` (create) | Unit tests for MapService |
| `tests/test_map_integration.py` (create) | Integration tests for Company+Plot+display |

---

### Task 1: Country and Plot Data Models

**Files:**
- Create: `entity/map.py`
- Test: `tests/test_map_service.py`

- [ ] **Step 1: Write the failing test for Country and Plot dataclasses**

Create `tests/test_map_service.py`:

```python
"""MapService 及地图数据模型单元测试。"""

from entity.map import Country, Plot


class TestDataModels:
    def test_country_creation(self):
        country = Country(name="华夏", description="东方大国")
        assert country.name == "华夏"
        assert country.description == "东方大国"

    def test_plot_creation(self):
        country = Country(name="华夏", description="东方大国")
        plot = Plot(name="硅谷工业区", country=country, description="电子产业聚集地")
        assert plot.name == "硅谷工业区"
        assert plot.country is country
        assert plot.description == "电子产业聚集地"
        assert plot.neighbors == []

    def test_plot_neighbor_assignment(self):
        country = Country(name="华夏", description="东方大国")
        plot_a = Plot(name="A区", country=country, description="")
        plot_b = Plot(name="B区", country=country, description="")
        plot_a.neighbors.append(plot_b)
        plot_b.neighbors.append(plot_a)
        assert plot_b in plot_a.neighbors
        assert plot_a in plot_b.neighbors
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_map_service.py::TestDataModels -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'entity.map'`

- [ ] **Step 3: Implement Country and Plot dataclasses**

Create `entity/map.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Country:
    """国家数据模型。"""
    name: str
    description: str = ""


@dataclass
class Plot:
    """地块数据模型。"""
    name: str
    country: Country
    description: str = ""
    neighbors: List[Plot] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_map_service.py::TestDataModels -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add entity/map.py tests/test_map_service.py
git commit -m "feat: add Country and Plot dataclass models"
```

---

### Task 2: MapService — Loading and Validation

**Files:**
- Create: `system/map_service.py`
- Modify: `tests/test_map_service.py`

- [ ] **Step 1: Write failing tests for MapService load and validation**

Append to `tests/test_map_service.py`:

```python
import pytest

from system.map_service import MapService


class TestMapServiceLoad:
    def _sample_config(self):
        return {
            "countries": [
                {"name": "华夏", "description": "东方大国"},
                {"name": "西洋联邦", "description": "工业强国"},
            ],
            "plots": [
                {"name": "硅谷工业区", "country": "华夏", "description": "电子产业聚集地", "neighbors": ["江南纺织区"]},
                {"name": "江南纺织区", "country": "华夏", "description": "传统纺织业重镇", "neighbors": ["硅谷工业区"]},
                {"name": "新大陆科技园", "country": "西洋联邦", "description": "高科技产业基地", "neighbors": []},
            ],
        }

    def test_load_countries(self):
        svc = MapService()
        svc.load_map(self._sample_config())
        assert "华夏" in svc.countries
        assert "西洋联邦" in svc.countries
        assert svc.countries["华夏"].name == "华夏"

    def test_load_plots(self):
        svc = MapService()
        svc.load_map(self._sample_config())
        assert "硅谷工业区" in svc.plots
        assert svc.plots["硅谷工业区"].country.name == "华夏"

    def test_neighbors_resolved(self):
        svc = MapService()
        svc.load_map(self._sample_config())
        plot_a = svc.plots["硅谷工业区"]
        plot_b = svc.plots["江南纺织区"]
        assert plot_b in plot_a.neighbors
        assert plot_a in plot_b.neighbors

    def test_neighbor_consistency_error(self):
        """A 列 B 为邻居但 B 未列 A 时应报错。"""
        config = {
            "countries": [{"name": "X", "description": ""}],
            "plots": [
                {"name": "A", "country": "X", "description": "", "neighbors": ["B"]},
                {"name": "B", "country": "X", "description": "", "neighbors": []},
            ],
        }
        svc = MapService()
        with pytest.raises(ValueError, match="相邻关系不一致"):
            svc.load_map(config)

    def test_unknown_country_error(self):
        config = {
            "countries": [{"name": "X", "description": ""}],
            "plots": [
                {"name": "A", "country": "不存在", "description": "", "neighbors": []},
            ],
        }
        svc = MapService()
        with pytest.raises(ValueError, match="不存在"):
            svc.load_map(config)

    def test_unknown_neighbor_error(self):
        config = {
            "countries": [{"name": "X", "description": ""}],
            "plots": [
                {"name": "A", "country": "X", "description": "", "neighbors": ["不存在"]},
            ],
        }
        svc = MapService()
        with pytest.raises(ValueError, match="不存在"):
            svc.load_map(config)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_map_service.py::TestMapServiceLoad -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'system.map_service'`

- [ ] **Step 3: Implement MapService**

Create `system/map_service.py`:

```python
from __future__ import annotations

from typing import Dict, List

from entity.map import Country, Plot


class MapService:
    """地图服务 - 管理国家、地块数据的加载和查询。"""

    def __init__(self) -> None:
        self.countries: Dict[str, Country] = {}
        self.plots: Dict[str, Plot] = {}

    def load_map(self, config: dict) -> None:
        """从配置字典加载国家和地块，校验相邻关系双向一致性。"""
        self.countries.clear()
        self.plots.clear()

        # 1. 创建 Country
        for item in config.get("countries", []):
            name = item["name"]
            self.countries[name] = Country(
                name=name,
                description=item.get("description", ""),
            )

        # 2. 创建 Plot（neighbors 暂存名称列表）
        neighbor_names: Dict[str, List[str]] = {}
        for item in config.get("plots", []):
            name = item["name"]
            country_name = item["country"]
            if country_name not in self.countries:
                raise ValueError(f"地块 '{name}' 引用了未定义的国家 '{country_name}'")
            country = self.countries[country_name]
            self.plots[name] = Plot(
                name=name,
                country=country,
                description=item.get("description", ""),
            )
            neighbor_names[name] = item.get("neighbors", [])

        # 3. 解析 neighbors 引用
        for plot_name, names in neighbor_names.items():
            plot = self.plots[plot_name]
            for n_name in names:
                if n_name not in self.plots:
                    raise ValueError(f"地块 '{plot_name}' 引用了未定义的相邻地块 '{n_name}'")
                plot.neighbors.append(self.plots[n_name])

        # 4. 校验双向一致性
        for plot_name, plot in self.plots.items():
            for neighbor in plot.neighbors:
                if plot not in neighbor.neighbors:
                    raise ValueError(
                        f"相邻关系不一致: '{plot_name}' 列出 '{neighbor.name}' 为邻居，"
                        f"但 '{neighbor.name}' 未列出 '{plot_name}'"
                    )

    def get_country(self, name: str) -> Country:
        """按名称获取国家。"""
        if name not in self.countries:
            raise KeyError(f"国家 '{name}' 不存在")
        return self.countries[name]

    def get_plot(self, name: str) -> Plot:
        """按名称获取地块。"""
        if name not in self.plots:
            raise KeyError(f"地块 '{name}' 不存在")
        return self.plots[name]

    def get_plots_by_country(self, country_name: str) -> List[Plot]:
        """获取某国家下所有地块。"""
        return [p for p in self.plots.values() if p.country.name == country_name]

    def get_neighbors(self, plot_name: str) -> List[Plot]:
        """获取地块的相邻地块列表。"""
        return self.get_plot(plot_name).neighbors
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_map_service.py -v`
Expected: All tests PASS (both TestDataModels and TestMapServiceLoad)

- [ ] **Step 5: Commit**

```bash
git add system/map_service.py tests/test_map_service.py
git commit -m "feat: add MapService with load, validation, and query methods"
```

---

### Task 3: MapService — Query Methods (companies by plot/country)

**Files:**
- Modify: `system/map_service.py`
- Modify: `tests/test_map_service.py`

- [ ] **Step 1: Write failing tests for company query methods**

Append to `tests/test_map_service.py`:

```python
from unittest.mock import MagicMock

from entity.company.company import Company
from entity.map import Country, Plot


class TestMapServiceQueries:
    def _setup(self):
        svc = MapService()
        config = {
            "countries": [
                {"name": "华夏", "description": ""},
                {"name": "西洋联邦", "description": ""},
            ],
            "plots": [
                {"name": "A区", "country": "华夏", "description": "", "neighbors": ["B区"]},
                {"name": "B区", "country": "华夏", "description": "", "neighbors": ["A区"]},
                {"name": "C区", "country": "西洋联邦", "description": "", "neighbors": []},
            ],
        }
        svc.load_map(config)
        return svc

    def test_get_plots_by_country(self):
        svc = self._setup()
        plots = svc.get_plots_by_country("华夏")
        names = [p.name for p in plots]
        assert "A区" in names
        assert "B区" in names
        assert "C区" not in names

    def test_get_companies_in_plot(self):
        svc = self._setup()
        c1 = Company(name="c1")
        c1.plot = svc.get_plot("A区")
        c2 = Company(name="c2")
        c2.plot = svc.get_plot("B区")
        companies = [c1, c2]
        result = svc.get_companies_in_plot("A区", companies)
        assert result == [c1]

    def test_get_companies_in_country(self):
        svc = self._setup()
        c1 = Company(name="c1")
        c1.plot = svc.get_plot("A区")
        c2 = Company(name="c2")
        c2.plot = svc.get_plot("C区")
        companies = [c1, c2]
        result = svc.get_companies_in_country("华夏", companies)
        assert result == [c1]

    def test_get_neighbors(self):
        svc = self._setup()
        neighbors = svc.get_neighbors("A区")
        assert len(neighbors) == 1
        assert neighbors[0].name == "B区"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_map_service.py::TestMapServiceQueries -v`
Expected: FAIL — `Company` object has no attribute `plot` (AttributeError)

- [ ] **Step 3: Add company query methods to MapService and plot attribute to Company**

Add to `system/map_service.py` at the end of the class:

```python
    def get_companies_in_plot(self, plot_name: str, companies: list) -> list:
        """获取某地块中所有公司。"""
        plot = self.get_plot(plot_name)
        return [c for c in companies if getattr(c, 'plot', None) is plot]

    def get_companies_in_country(self, country_name: str, companies: list) -> list:
        """获取某国家中所有公司。"""
        country_plots = self.get_plots_by_country(country_name)
        return [c for c in companies if getattr(c, 'plot', None) in country_plots]
```

Modify `entity/company/company.py`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from component.ledger_component import LedgerComponent
from component.metric_component import MetricComponent
from component.productor_component import ProductorComponent
from core.entity import Entity

if TYPE_CHECKING:
    from entity.map import Plot


class Company(Entity):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.plot: Optional[Plot] = None
        self.init_component(ProductorComponent)
        self.init_component(LedgerComponent)
        self.init_component(MetricComponent)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_map_service.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add entity/company/company.py system/map_service.py tests/test_map_service.py
git commit -m "feat: add plot attribute to Company and query methods to MapService"
```

---

### Task 4: Map Configuration File

**Files:**
- Create: `config/map.yaml`
- Modify: `config/game.yaml`

- [ ] **Step 1: Create config/map.yaml**

Create `config/map.yaml`:

```yaml
# 地图配置：国家与地块定义

countries:
  - name: "华夏"
    description: "东方大国"
  - name: "西洋联邦"
    description: "工业强国"

plots:
  - name: "硅谷工业区"
    country: "华夏"
    description: "电子产业聚集地"
    neighbors: ["江南纺织区", "北方粮仓"]
  - name: "江南纺织区"
    country: "华夏"
    description: "传统纺织业重镇"
    neighbors: ["硅谷工业区", "北方粮仓"]
  - name: "北方粮仓"
    country: "华夏"
    description: "粮食主产区"
    neighbors: ["硅谷工业区", "江南纺织区", "新大陆科技园"]
  - name: "新大陆科技园"
    country: "西洋联邦"
    description: "高科技产业基地"
    neighbors: ["北方粮仓"]
```

- [ ] **Step 2: Add plot field to game.yaml companies**

Modify `config/game.yaml` — add `plot` field to each company entry:

```yaml
# 游戏初始化配置
total_rounds: 20

# 每种工厂类型对应的公司生成参数
companies:
  # 电子产业链
  - factory_type: "硅矿场"
    count: 2
    initial_cash: 100000
    initial_wage: 10
    plot: "硅谷工业区"
    decision_component: "classic"
  - factory_type: "芯片工厂"
    count: 2
    initial_cash: 200000
    initial_wage: 15
    plot: "硅谷工业区"
    decision_component: "classic"
  - factory_type: "手机工厂"
    count: 2
    initial_cash: 150000
    initial_wage: 12
    plot: "硅谷工业区"
    decision_component: "classic"
  # 纺织产业链
  - factory_type: "棉花农场"
    count: 2
    initial_cash: 80000
    initial_wage: 8
    plot: "江南纺织区"
    decision_component: "classic"
  - factory_type: "纺织厂"
    count: 2
    initial_cash: 120000
    initial_wage: 12
    plot: "江南纺织区"
    decision_component: "classic"
  - factory_type: "服装厂"
    count: 2
    initial_cash: 100000
    initial_wage: 10
    plot: "江南纺织区"
    decision_component: "classic"
  # 食品产业链
  - factory_type: "麦田"
    count: 3
    initial_cash: 60000
    initial_wage: 8
    plot: "北方粮仓"
    decision_component: "classic"
  - factory_type: "面粉厂"
    count: 2
    initial_cash: 80000
    initial_wage: 10
    plot: "北方粮仓"
    decision_component: "classic"
  - factory_type: "食品厂"
    count: 2
    initial_cash: 90000
    initial_wage: 10
    plot: "北方粮仓"
    decision_component: "classic"

# 银行（玩家控制）
banks:
  - name: "银行A"
    initial_cash: 2000000
  - name: "银行B"
    initial_cash: 2000000

# 居民初始现金
folk_initial_cash: 500000

# 破产清算与市场补充
bankruptcy:
  liquidation_factory_rate: 0.5
  min_producers_per_goods: 2
  new_company_initial_cash: 100000
  replenish_decision_component: "classic"
  replenish_initial_wage: 10
```

- [ ] **Step 3: Verify YAML is syntactically valid**

Run: `python -c "import yaml; yaml.safe_load(open('config/map.yaml')); yaml.safe_load(open('config/game.yaml')); print('OK')"`
Expected: prints `OK`

- [ ] **Step 4: Commit**

```bash
git add config/map.yaml config/game.yaml
git commit -m "feat: add map.yaml config and plot field to game.yaml companies"
```

---

### Task 5: Game Initialization — Wire MapService

**Files:**
- Modify: `game/game.py`
- Modify: `system/company_service.py`
- Test: `tests/test_map_integration.py`

- [ ] **Step 1: Write the failing integration test**

Create `tests/test_map_integration.py`:

```python
"""地图系统集成测试：Game 初始化后公司正确持有 Plot 引用。"""

from game.game import Game


class TestMapIntegration:
    def test_companies_have_plot_assigned(self):
        game = Game()
        for company in game.companies:
            assert company.plot is not None, f"{company.name} has no plot assigned"
            assert company.plot.name != ""
            assert company.plot.country is not None

    def test_plot_country_chain(self):
        game = Game()
        company = game.companies[0]
        # 电子产业链公司应在硅谷工业区，属于华夏
        assert company.plot.name == "硅谷工业区"
        assert company.plot.country.name == "华夏"

    def test_map_service_loaded(self):
        game = Game()
        assert hasattr(game, 'map_service')
        assert len(game.map_service.countries) == 2
        assert len(game.map_service.plots) == 4

    def test_map_service_query_companies_in_plot(self):
        game = Game()
        companies_in_plot = game.map_service.get_companies_in_plot("硅谷工业区", game.companies)
        # 硅矿场(2) + 芯片工厂(2) + 手机工厂(2) = 6
        assert len(companies_in_plot) == 6

    def test_map_service_query_companies_in_country(self):
        game = Game()
        companies_in_china = game.map_service.get_companies_in_country("华夏", game.companies)
        # 硅谷工业区(6) + 江南纺织区(6) + 北方粮仓(7) = 19
        assert len(companies_in_china) == 19
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_map_integration.py -v`
Expected: FAIL — `Game` has no `map_service` attribute / company.plot is None

- [ ] **Step 3: Modify CompanyService.create_company to accept plot parameter**

Edit `system/company_service.py` — modify the `create_company` method signature and body:

Add import at top:
```python
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from entity.map import Plot
```

Change `create_company` signature:
```python
    def create_company(
        self,
        name: str,
        factory_type: FactoryType,
        initial_cash: int,
        decision_component: str,
        initial_wage: int,
        plot: Optional[Plot] = None,
    ) -> Company:
        """创建一家拥有指定工厂类型和初始资金的公司。"""
        company = Company(name=name)
        company.plot = plot
        company.initial_wage = initial_wage
        company.wage = initial_wage
        ledger = company.get_component(LedgerComponent)
        ledger.cash = initial_cash
        pc = company.get_component(ProductorComponent)
        factory = Factory(factory_type, build_remaining=0)
        pc.factories[factory_type].append(factory)
        pc.init_prices()
        decision_cls = get_decision_component_class(decision_component)
        company.init_component(decision_cls)
        self.companies[name] = company
        return company
```

- [ ] **Step 4: Modify game.py to initialize MapService and pass plot**

Edit `game/game.py`:

Add import:
```python
from system.map_service import MapService
```

In `__init__`, after other service initializations, add:
```python
        self.map_service = MapService()
```

In `init_game`, after loading config, add map loading before company creation:
```python
        # 加载地图配置
        map_cfg = config.section("map")
        self.map_service.load_map({
            "countries": [{"name": c.name, "description": getattr(c, 'description', '')} for c in map_cfg.countries],
            "plots": [
                {
                    "name": p.name,
                    "country": p.country,
                    "description": getattr(p, 'description', ''),
                    "neighbors": p.neighbors if hasattr(p, 'neighbors') else [],
                }
                for p in map_cfg.plots
            ],
        })
```

In the company creation loop, pass plot:
```python
        for item in game_cfg.companies:
            ft = factory_types[item.factory_type]
            decision = item.decision_component
            plot_name = getattr(item, 'plot', None)
            plot = self.map_service.get_plot(plot_name) if plot_name else None
            for _ in range(item.count):
                name = f"company_{company_idx}"
                self.company_service.create_company(
                    name=name,
                    factory_type=ft,
                    initial_cash=item.initial_cash,
                    decision_component=decision,
                    initial_wage=item.initial_wage,
                    plot=plot,
                )
                company_idx += 1
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_map_integration.py -v`
Expected: All 5 tests PASS

- [ ] **Step 6: Run full test suite to check for regressions**

Run: `pytest --tb=short -q`
Expected: All existing tests still pass

- [ ] **Step 7: Commit**

```bash
git add game/game.py system/company_service.py tests/test_map_integration.py
git commit -m "feat: wire MapService into Game init, assign plots to companies"
```

---

### Task 6: Display — Plot Column in Company Table

**Files:**
- Modify: `system/player_service.py`
- Modify: `tests/test_player_service.py`

- [ ] **Step 1: Write the failing test for plot column**

Add to `tests/test_player_service.py` in `TestFormatCompanyTable`:

```python
    def test_includes_plot_column(self):
        svc = _make_player_service()
        company, gt, _ = _make_company_with_price()
        from entity.map import Country, Plot
        country = Country(name="华夏", description="")
        plot = Plot(name="硅谷工业区", country=country, description="")
        company.plot = plot
        svc.game.company_service.companies = {"company_0": company}
        table = svc.format_company_table()
        assert "地块" in table
        assert "硅谷工业区" in table
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_player_service.py::TestFormatCompanyTable::test_includes_plot_column -v`
Expected: FAIL — "地块" not in table output

- [ ] **Step 3: Add plot column to render_company_table**

Edit `system/player_service.py` in `render_company_table()`:

After the line `table.add_column("公司名", style="bold")`, add:
```python
        table.add_column("地块")
```

In the `table.add_row(...)` call, after `company.name`, add:
```python
                company.plot.name if company.plot else "-",
```

The full `add_row` becomes:
```python
            table.add_row(
                company.name,
                company.plot.name if company.plot else "-",
                ", ".join(ft_parts) or "-",
                str(mc.factories_active),
                str(mc.factories_idle),
                str(mc.factories_building),
                str(cash),
                str(company.wage),
                str(mc.last_hired_workers),
                str(total_tech),
                str(total_brand),
                ", ".join(price_parts) or "-",
                ", ".join(inv_parts) or "-",
                str(receivables),
                str(payables),
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_player_service.py::TestFormatCompanyTable -v`
Expected: All tests PASS

- [ ] **Step 5: Also add plot/country to company_table_dict (JSON output)**

In `company_table_dict()`, add these fields to the dict after `"name"`:
```python
                "plot": company.plot.name if company.plot else None,
                "country": company.plot.country.name if company.plot else None,
```

- [ ] **Step 6: Run full test suite**

Run: `pytest --tb=short -q`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add system/player_service.py tests/test_player_service.py
git commit -m "feat: add plot column to company table display and JSON output"
```

---

### Task 7: Display — Map Panel

**Files:**
- Modify: `system/player_service.py`
- Create: `tests/test_map_integration.py` (append)

- [ ] **Step 1: Write failing test for map panel rendering**

Append to `tests/test_map_integration.py`:

```python
from system.player_service import PlayerService
from rich.console import Console


class TestMapPanel:
    def test_render_map_panel_contains_countries(self):
        game = Game()
        svc = game.player_service
        with Console(width=200).capture() as capture:
            Console(width=200).print(svc.render_map_panel())
        output = capture.get()
        assert "华夏" in output
        assert "西洋联邦" in output

    def test_render_map_panel_contains_plots(self):
        game = Game()
        svc = game.player_service
        with Console(width=200).capture() as capture:
            Console(width=200).print(svc.render_map_panel())
        output = capture.get()
        assert "硅谷工业区" in output
        assert "江南纺织区" in output
        assert "北方粮仓" in output
        assert "新大陆科技园" in output

    def test_render_map_panel_contains_company_counts(self):
        game = Game()
        svc = game.player_service
        with Console(width=200).capture() as capture:
            Console(width=200).print(svc.render_map_panel())
        output = capture.get()
        # 硅谷工业区有6家公司
        assert "6家" in output

    def test_render_map_panel_contains_neighbors(self):
        game = Game()
        svc = game.player_service
        with Console(width=200).capture() as capture:
            Console(width=200).print(svc.render_map_panel())
        output = capture.get()
        # 硅谷工业区的相邻应显示江南纺织区
        assert "相邻" in output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_map_integration.py::TestMapPanel -v`
Expected: FAIL — `PlayerService` has no `render_map_panel` method

- [ ] **Step 3: Implement render_map_panel**

Add to `system/player_service.py`, in the `PlayerService` class, after `render_company_table`:

```python
    def render_map_panel(self) -> Panel:
        """渲染地图面板：按国家分组显示地块、公司数量和相邻关系。"""
        map_service = self.game.map_service
        companies = list(self.game.company_service.companies.values())

        lines: List[str] = []
        for country_name, country in map_service.countries.items():
            lines.append(f"[bold]{country.name}[/]")
            plots = map_service.get_plots_by_country(country_name)
            for plot in plots:
                company_count = len(map_service.get_companies_in_plot(plot.name, companies))
                neighbor_names = ", ".join(n.name for n in plot.neighbors)
                neighbor_str = f"  相邻: {neighbor_names}" if neighbor_names else ""
                lines.append(f"  {plot.name}  [{company_count}家]{neighbor_str}")
            lines.append("")

        text = "\n".join(lines).rstrip()
        return Panel(text, title="地图", border_style="green")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_map_integration.py::TestMapPanel -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Add map panel to player_act_phase**

In `player_act_phase()`, add after the economy summary print and before the company table:

```python
        console.print(self.render_map_panel())
```

So the order becomes:
```python
        console.print(self.render_economy_summary())
        console.print(self.render_map_panel())
        console.print(self.render_company_table())
```

- [ ] **Step 6: Run full test suite**

Run: `pytest --tb=short -q`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add system/player_service.py tests/test_map_integration.py
git commit -m "feat: add map panel display with countries, plots, and neighbors"
```

---

### Task 8: Handle Government-Created Companies (Plot Assignment)

**Files:**
- Modify: `system/company_service.py`

The `replenish_market` method creates new companies when producers go bankrupt. These companies need a plot too. Since we don't know which plot makes most sense for government companies, we assign them to the same plot as an existing producer of the same goods type, or the first available plot if none exist.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_map_integration.py`:

```python
from component.ledger_component import LedgerComponent


class TestGovernmentCompanyPlot:
    def test_replenished_company_has_plot(self):
        """政府补充的公司也应有 plot 属性。"""
        from component.productor_component import ProductorComponent

        game = Game()
        # 强制让食品厂公司全部破产
        food_companies = [
            c for c in game.companies
            if any("食品" in ft.recipe.output_goods_type.name
                   for ft in c.get_component(ProductorComponent).factories.keys())
        ]
        for c in food_companies:
            c.get_component(LedgerComponent).is_bankrupt = True

        # 执行破产清算和市场补充
        game.company_service.process_bankruptcies()
        game.company_service.replenish_market()
        game.companies = list(game.company_service.companies.values())

        # 新公司也应该有 plot
        for company in game.companies:
            assert company.plot is not None, f"{company.name} has no plot"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_map_integration.py::TestGovernmentCompanyPlot -v`
Expected: FAIL — newly created gov companies have `plot = None`

- [ ] **Step 3: Modify replenish_market to assign plot**

In `system/company_service.py`, modify `replenish_market` to determine a plot for new companies. Add a `default_plot` parameter tracking and pass it to `create_company`:

First, add at the top of `CompanyService.__init__`:
```python
        self._default_plot = None  # fallback plot for government companies
```

Add a method:
```python
    def _find_plot_for_goods(self, goods_type: GoodsType) -> 'Plot | None':
        """查找生产指定商品的现有公司的地块，用于政府补充公司。"""
        for company in self.companies.values():
            pc = company.get_component(ProductorComponent)
            if pc is None:
                continue
            for ft in pc.factories.keys():
                if ft.recipe.output_goods_type == goods_type:
                    return company.plot
        return self._default_plot
```

In `replenish_market`, before calling `self.create_company(...)`, add:
```python
                plot = self._find_plot_for_goods(gt)
```

And pass it:
```python
                self.create_company(
                    name=name,
                    factory_type=ft,
                    initial_cash=self._new_company_cash,
                    decision_component=self._replenish_decision_component,
                    initial_wage=self._replenish_initial_wage,
                    plot=plot,
                )
```

In `game/game.py` `init_game()`, after creating all companies, set the default plot:
```python
        # 设置 CompanyService 的默认地块（用于政府补充公司）
        if self.map_service.plots:
            first_plot = next(iter(self.map_service.plots.values()))
            self.company_service._default_plot = first_plot
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_map_integration.py::TestGovernmentCompanyPlot -v`
Expected: PASS

- [ ] **Step 5: Run full test suite**

Run: `pytest --tb=short -q`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add system/company_service.py game/game.py tests/test_map_integration.py
git commit -m "feat: assign plot to government-replenished companies"
```

---

### Task 9: Final Verification

- [ ] **Step 1: Run complete test suite**

Run: `pytest -v`
Expected: All tests PASS, no regressions

- [ ] **Step 2: Verify map.yaml loads correctly via ConfigManager**

Run: `python -c "from core.config import ConfigManager; c = ConfigManager(); c.load(); m = c.section('map'); print(f'Countries: {len(m.countries)}, Plots: {len(m.plots)}')"`
Expected: `Countries: 2, Plots: 4`

- [ ] **Step 3: Quick manual game init verification**

Run: `python -c "from game.game import Game; g = Game(); print(f'Companies: {len(g.companies)}'); print(f'Map plots: {len(g.map_service.plots)}'); c = g.companies[0]; print(f'{c.name} -> {c.plot.name} ({c.plot.country.name})')"`
Expected output like:
```
Companies: 19
Map plots: 4
company_0 -> 硅谷工业区 (华夏)
```

- [ ] **Step 4: Final commit (if any leftover changes)**

Run: `git status`
If clean, skip. Otherwise commit any remaining changes.
