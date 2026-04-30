# 地图与国家系统设计

## 概述

为 BankGameHand 增加地图和国家系统。每个公司属于一个地块，地块属于国家，地块之间有相邻关系。当前阶段只做归属标签和展示，架构上预留扩展空间（未来可加入运输成本、关税等机制影响）。

## 需求

1. **数据模型**：定义 Country（国家）和 Plot（地块）数据结构
2. **归属关系**：Company 持有 Plot 引用，Plot 持有 Country 引用
3. **相邻关系**：地块之间有双向相邻关系
4. **配置驱动**：国家和地块定义在 `config/map.yaml`，公司与地块的对应关系在 `config/game.yaml`
5. **展示 — 公司表格**：公司信息表增加"地块"列
6. **展示 — 地图面板**：新增地图展示区块，按国家分组显示地块及其公司数量和相邻关系

## 数据模型

### Country（国家）

```python
@dataclass
class Country:
    name: str           # 国家名称，如 "华夏"
    description: str    # 可选描述，如 "东方大国"
```

### Plot（地块）

```python
@dataclass
class Plot:
    name: str                   # 地块名称，如 "硅谷工业区"
    country: Country            # 所属国家引用
    description: str            # 可选描述
    neighbors: List['Plot']     # 相邻地块列表（运行时解析填充）
```

**说明：**
- 配置文件中 `neighbors` 使用名称字符串列表
- 运行时由 MapService 解析为 Plot 对象引用
- 相邻关系是双向的，MapService 加载时校验一致性

### Company 变化

Company 实体增加 `plot: Plot` 属性：
- 在创建时由 CompanyService 根据 game.yaml 配置赋值
- 通过 `company.plot` 可获取地块信息
- 通过 `company.plot.country` 可获取国家信息

## 文件位置

| 新增文件 | 位置 | 职责 |
|---------|------|------|
| Country/Plot dataclass | `entity/map.py` | 数据模型定义 |
| MapService | `system/map_service.py` | 地图数据加载、校验、查询 |
| map.yaml | `config/map.yaml` | 国家和地块配置 |

| 修改文件 | 变化 |
|---------|------|
| `entity/company/company.py` | 增加 `plot: Plot` 属性 |
| `config/game.yaml` | 公司配置增加 `plot` 字段 |
| `system/company_service.py` | 创建公司时赋值 plot |
| `system/player_service.py` | 公司表格增加"地块"列 + 新增地图面板渲染 |
| `game/game.py` | 初始化阶段加载 MapService |

## 配置文件设计

### config/map.yaml

```yaml
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

### config/game.yaml（公司配置变化）

每个公司配置项增加 `plot` 字段：

```yaml
companies:
  - factory_type: "硅矿场"
    count: 2
    initial_cash: 500000
    initial_wage: 5000
    plot: "硅谷工业区"
    decision_component: "classic"
  - factory_type: "芯片工厂"
    count: 2
    initial_cash: 800000
    initial_wage: 6000
    plot: "硅谷工业区"
    decision_component: "classic"
  # ... 其他公司类似
```

## MapService 设计

```python
class MapService(Service):
    """地图服务 - 管理国家、地块数据的加载和查询"""

    countries: Dict[str, Country]    # name → Country
    plots: Dict[str, Plot]           # name → Plot

    def load_map(self, config: dict) -> None:
        """
        从 map.yaml 配置加载国家和地块。
        1. 创建 Country 对象
        2. 创建 Plot 对象（country 为引用）
        3. 解析 neighbors 字段，将名称转为 Plot 引用
        4. 校验相邻关系双向一致性（A 列 B 为邻居 ↔ B 列 A 为邻居）
        """

    def get_country(self, name: str) -> Country:
        """按名称获取国家"""

    def get_plot(self, name: str) -> Plot:
        """按名称获取地块"""

    def get_plots_by_country(self, country_name: str) -> List[Plot]:
        """获取某国家下所有地块"""

    def get_companies_in_plot(self, plot_name: str) -> List[Company]:
        """获取某地块中所有公司"""

    def get_companies_in_country(self, country_name: str) -> List[Company]:
        """获取某国家中所有公司"""

    def get_neighbors(self, plot_name: str) -> List[Plot]:
        """获取地块的相邻地块列表"""
```

### 初始化流程

在 `game.py` 的游戏初始化中：

1. `MapService.load_map()` 加载 `config/map.yaml`
2. `CompanyService` 创建公司时，读取公司配置中的 `plot` 字段
3. 调用 `MapService.get_plot(plot_name)` 获取 Plot 对象
4. 赋值 `company.plot = plot`

## 展示设计

### 公司表格 — 增加"地块"列

在 `player_service.py` 的 `render_company_table()` 中：

- 在"公司名"列之后新增"地块"列
- 样式：普通文本，不加特殊颜色
- 数据来源：`company.plot.name`

表格效果：

| 公司名 | 地块 | 工厂类型 | 开工 | 停工 | ... |
|--------|------|---------|------|------|-----|
| company_0 | 硅谷工业区 | 硅矿 | 2 | 0 | ... |
| company_1 | 硅谷工业区 | 硅矿 | 2 | 0 | ... |
| company_2 | 硅谷工业区 | 芯片 | 2 | 0 | ... |

### 地图面板 — 新增展示区块

在 `player_service.py` 中新增 `render_map_panel()` 方法，使用 Rich Panel 展示：

- 按国家分组
- 每个国家下列出所有地块
- 每个地块显示：名称、公司数量、相邻地块名称

展示效果（Rich Panel）：

```
┌─────────────────────────── 地图 ───────────────────────────┐
│ 华夏                                                        │
│   硅谷工业区    [6家]  相邻: 江南纺织区, 北方粮仓            │
│   江南纺织区    [6家]  相邻: 硅谷工业区, 北方粮仓            │
│   北方粮仓      [7家]  相邻: 硅谷工业区, 江南纺织区, 新大陆科技园 │
│                                                             │
│ 西洋联邦                                                    │
│   新大陆科技园  [6家]  相邻: 北方粮仓                        │
└─────────────────────────────────────────────────────────────┘
```

在 `player_act_phase()` 中，地图面板放在公司表格之前展示。

### JSON 输出（Web 端）

在 `company_table_dict()` 中，为每个公司的 dict 增加 `"plot"` 和 `"country"` 字段。

## 测试策略

1. **MapService 单元测试**：
   - 正确加载国家和地块
   - 相邻关系解析正确
   - 双向一致性校验：不一致时抛出异常
   - 查询方法正确返回

2. **Company 集成测试**：
   - 公司创建后正确持有 Plot 引用
   - 通过 company.plot.country 可链式访问

3. **展示测试**：
   - 公司表格包含地块列
   - 地图面板正确渲染

## 扩展预留

当前设计为纯标签展示，但以下扩展路径已预留：

- **运输成本**：相邻地块间运输成本低，非相邻需经过中间地块
- **关税/政策**：Country 可扩展为持有政策属性（税率、补贴等）
- **区域效应**：同一地块的公司可能有集聚效应
- **升级为 Entity**：Plot/Country 未来可升级为继承 Entity 的完整实体，挂载组件

这些扩展只需：
1. 将 dataclass 升级为 Entity
2. 为其添加相应 Component
3. 在相关 Service 中利用地理关系计算影响

当前架构不阻碍这些扩展。
