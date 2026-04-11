# ConfigManager 设计与测试方案

## 1. 概述

实现 `core/config.py`，提供 `ConfigManager`（单例）和 `AttrDict` 两个类，用于加载项目 `config/` 目录下的 YAML 配置文件，支持按文件名获取配置段，并以属性方式访问配置值。

## 2. 文件结构

```
d:\BankGameHand\
├── config/                    # YAML 配置文件目录（项目根目录下）
│   ├── economy.yaml
│   ├── market.yaml
│   └── ...
├── core/
│   └── config.py              # ConfigManager + AttrDict 实现
└── tests/
    └── test_config.py          # 测试用例
```

## 3. 依赖

- `PyYAML` (`import yaml`)

## 4. 类设计

### 4.1 AttrDict

继承 `dict`，支持通过 `.` 访问键值，递归处理嵌套结构。

**核心行为：**

- 构造时递归转换：嵌套的 `dict` 转为 `AttrDict`，`list` 中的 `dict` 元素也转为 `AttrDict`
- `list` 中的 `list` 保持原样（内部 `dict` 仍递归转换）
- `__getattr__` 映射到 `__getitem__`，找不到时抛 `AttributeError`
- `__setattr__` 映射到 `__setitem__`
- `__delattr__` 映射到 `__delitem__`
- 保留原生 `dict` 的 `[]` 访问方式

**嵌套转换规则：**

| 原始类型 | 转换结果 |
|---------|---------|
| `dict` | `AttrDict` |
| `list[dict]` | `list[AttrDict]` |
| `list[list[...]]` | `list[list[...]]`（内部 dict 仍递归） |
| `list[非dict]` | 保持不变 |
| 标量值 | 保持不变 |

### 4.2 ConfigManager

单例模式配置管理器。

**单例实现：** 通过 `__new__` 方法，`_instance` 类变量存储唯一实例。

**方法：**

| 方法 | 签名 | 说明 |
|-----|------|------|
| `load` | `load(path: str = None) -> None` | 扫描目录下所有 `.yaml`/`.yml` 文件并加载。`path` 默认为项目根目录下的 `config/`。重复调用会清除旧数据。 |
| `section` | `section(name: str) -> AttrDict` | 按文件名（不含扩展名）获取配置段。不存在时抛 `KeyError`。 |

**默认路径推导：** `Path(__file__).resolve().parent.parent / "config"`（从 `core/config.py` 向上两级到项目根目录）。

## 5. 使用示例

```yaml
# config/economy.yaml
base_rate: 500
growth:
  min: 100
  max: 1000
```

```python
from core.config import ConfigManager

cfg = ConfigManager()
cfg.load()

eco = cfg.section("economy")
eco.base_rate       # -> 500
eco.growth.min      # -> 100
eco["growth"]["max"] # -> 1000
```

## 6. 测试用例

### 6.1 AttrDict 测试

| # | 测试场景 | 输入 | 预期结果 |
|---|---------|------|---------|
| 1 | 基础属性访问 | `{"name": "test", "value": 42}` | `d.name == "test"`, `d.value == 42` |
| 2 | 字典风格访问 | `{"name": "test"}` | `d["name"] == "test"` |
| 3 | 嵌套 dict | `{"server": {"host": "localhost", "port": 8080}}` | `d.server.host == "localhost"`, `isinstance(d.server, AttrDict)` |
| 4 | list 内嵌 dict | `{"players": [{"name": "Alice"}, {"name": "Bob"}]}` | `d.players[0].name == "Alice"`, `isinstance(d.players[0], AttrDict)` |
| 5 | dict 内嵌 list | `{"group": {"members": ["a", "b", "c"]}}` | `d.group.members == ["a", "b", "c"]` |
| 6 | list 内嵌 list | `{"matrix": [[1, 2], [3, 4]]}` | `d.matrix[0] == [1, 2]`, `d.matrix[1][1] == 4` |
| 7 | 深层嵌套 dict->list->dict->list | 见下方 | `d.companies[0].departments[0].members[1] == "Bob"` |
| 8 | list 含混合类型 | `{"items": [1, "two", {"three": 3}, [4, 5]]}` | `d.items[2].three == 3`, `d.items[3] == [4, 5]` |
| 9 | 访问不存在属性 | `{"a": 1}` | 访问 `d.nonexistent` 抛 `AttributeError` |
| 10 | 空字典 | `{}` | 访问任何属性抛 `AttributeError` |
| 11 | None 值 | `{"val": None}` | `d.val is None` |

**用例 7 深层嵌套数据：**

```python
{
    "companies": [
        {
            "name": "CorpA",
            "departments": [
                {"name": "Engineering", "members": ["Alice", "Bob"]},
                {"name": "Sales", "members": ["Charlie"]},
            ],
        },
        {
            "name": "CorpB",
            "departments": [
                {"name": "HR", "members": ["Dave"]},
            ],
        },
    ]
}
```

### 6.2 ConfigManager 测试

| # | 测试场景 | 说明 | 预期结果 |
|---|---------|------|---------|
| 1 | 单例验证 | `ConfigManager() is ConfigManager()` | `True` |
| 2 | load + section 基础 | 加载含 `economy.yaml` 的目录 | `section("economy").base_rate == 500` |
| 3 | section 含 list of dicts | `market.yaml` 含产品列表 | `section("market").products[0].name == "iron"` |
| 4 | section 含 dict 内嵌 list | `market.yaml` 含 rules.discounts 列表 | `section("market").rules.discounts == [0.1, 0.2, 0.3]` |
| 5 | 深层嵌套 yml 文件 | `nested.yml` dict->list->dict->list | `section("nested").level1.level2[0].level3.info.deep is True` |
| 6 | section 不存在 | 获取未加载的 section | 抛 `KeyError` |
| 7 | 自定义路径 | `load(custom_path)` | 正确加载自定义目录 |
| 8 | 无效路径 | `load("/nonexistent")` | 抛 `FileNotFoundError` |
| 9 | 重新加载清除旧数据 | 先加载 dir1，再加载 dir2 | dir1 的 section 不再可用，dir2 的可用 |

**测试用 YAML 数据：**

```yaml
# economy.yaml
base_rate: 500
growth:
  min: 100
  max: 1000

# market.yaml
products:
  - name: iron
    price: 100
    tags: [metal, raw]
  - name: wood
    price: 50
    tags: [organic]
rules:
  tax_rate: 0.05
  discounts: [0.1, 0.2, 0.3]

# nested.yml
level1:
  level2:
    - level3:
        values: [10, 20, 30]
        info:
          deep: true
```
