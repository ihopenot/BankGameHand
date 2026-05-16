# 事件系统表达式规范

## 概述

事件系统使用**统一表达式树**来描述事件逻辑。所有内容——条件判断、实体捕获、效果执行——都是表达式（Expr）。每个表达式求值后返回一个值，这个值的真假性（truthy/falsy）驱动控制流。

事件定义文件放在 `config/events/` 目录下，使用 YAML 格式，每回合由 EventService 全量扫描执行。

---

## 文件结构

```yaml
events:
  - id: <唯一标识>
    name: <可选中文名>
    expr:
      <表达式 或 表达式列表>
```

`expr` 字段是事件的入口。如果是列表，则顺序执行所有表达式，返回最后一个的值。

---

## 全局上下文 `_G`

每个事件执行时自动注入全局变量 `_G`，包含：

| 字段 | 类型 | 说明 |
|------|------|------|
| `all_countries` | List[Country] | 所有国家 |
| `all_companies` | List[Company] | 所有公司 |
| `all_plots` | List[Plot] | 所有地块 |
| `current_round` | int | 当前回合数 |

通过 `GetField` 访问：
```yaml
GetField:
  - _G
  - all_countries
```

---

## 表达式节点

### GetField — 属性访问

从对象上取一个字段的值。**仅做取值，不做比较。**

```yaml
GetField:
  - <对象变量名>
  - <字段名>
```

对象变量名是字符串，引用上下文中的变量（如 `_G`、`target_country`）。也可以是嵌套的表达式节点。

示例：
```yaml
# 取 _G 的 all_countries 字段
GetField:
  - _G
  - all_countries

# 取 target_country 的 stability 字段
GetField:
  - target_country
  - stability
```

---

### Compare — 比较

独立的比较表达式，接受左值、运算符、右值，返回 bool。

```yaml
Compare:
  - <左值表达式>
  - <运算符>
  - <右值表达式>
```

左值和右值都是完整的表达式（可以是 GetField、Literal、Var 等任意 Expr）。

**支持的运算符：**

| op | 含义 |
|----|------|
| `>` | 大于 |
| `>=` | 大于等于 |
| `<` | 小于 |
| `<=` | 小于等于 |
| `==` | 等于 |
| `!=` | 不等于 |
| `belongs_to` | 属于（引用相等或包含于列表） |

示例：
```yaml
# stability > 10
Compare:
  - GetField:
      - target_country
      - stability
  - ">"
  - 10

# 比较两个实体的字段
Compare:
  - GetField:
      - company_a
      - revenue
  - ">"
  - GetField:
      - company_b
      - revenue

# 检查所属关系
Compare:
  - GetField:
      - target_company
      - country
  - belongs_to
  - Var: target_country
```

---

### If — 条件执行

```yaml
If:
  - <条件表达式>
  - <主体表达式>
```

条件为 truthy 时执行主体并返回其值，否则返回 None。

**典型用法**：条件是一个捕获表达式，捕获成功（找到实体）则执行效果。

---

### And — 短路与

```yaml
And:
  - <表达式1>
  - <表达式2>
  - ...
```

从左到右求值，遇到第一个 falsy 值立即返回该值。全部 truthy 则返回最后一个值。

---

### Or — 短路或

```yaml
Or:
  - <表达式1>
  - <表达式2>
  - ...
```

从左到右求值，遇到第一个 truthy 值立即返回。全部 falsy 则返回最后一个值。

---

### Not — 逻辑非

```yaml
Not: <表达式>
```

返回 `not` 求值结果。

---

### Exprs — 表达式序列

```yaml
Exprs:
  - <表达式1>
  - <表达式2>
  - ...
```

顺序执行所有表达式，返回最后一个值。用于在 If 的主体中执行多个效果。

---

### Literal — 字面量

```yaml
Literal: 42
```

返回一个常量。YAML 中的裸数字/字符串/布尔值也会自动识别为 Literal。

---

### Var — 变量引用

```yaml
Var: target_country
```

从上下文中取变量值。注意：`GetField` 的第一个参数如果是字符串，也会自动当作变量引用，所以通常不需要显式写 `Var`。

---

## 捕获节点

捕获节点从集合中筛选实体，将结果绑定到变量名，供后续表达式使用。同时作为布尔值：找到=truthy，找不到=falsy。

### 变量绑定的两种状态

捕获节点在执行过程中，`var` 有两种状态：

1. **迭代中（condition 求值时）**：`var` 绑定的是**当前正在检查的单个实体**。此时对 `var` 做 `GetField` 是安全的，取到的是该实体的字段值。

2. **完成后（捕获结束后）**：
   - `Any` / `Random`：`var` 绑定**单个实体**，可以正常 `GetField`
   - `Every`：`var` 绑定**实体列表**，**不能**对列表做 `GetField`

**约束：`Every` 捕获完成后的列表变量只能用于以下场景：**
- `ModifyAttr` 的目标（内部自动遍历列表）
- `EffectCall` 的目标（handler 自行处理列表）
- 作为另一个捕获节点的 `all` 输入（提供集合供下一层筛选）
- 作为 truthy/falsy 判断（非空=truthy）

**不要**对列表变量做 `GetField` 或 `Compare`，这会导致运行时错误。

### Any — 捕获第一个匹配

```yaml
Any:
  all: <提供集合的表达式>
  condition:
    - <过滤条件（列表隐含 And）>
  var: <绑定变量名>
```

遍历集合，对每个元素求值 condition（元素临时绑定到 var），返回**第一个**满足条件的实体。找不到则返回 None 并解绑变量。

### Every — 捕获所有匹配

```yaml
Every:
  all: <提供集合的表达式>
  condition:
    - <过滤条件>
  var: <绑定变量名>
```

收集**所有**满足条件的实体为列表，绑定到 var。空列表 = falsy。

### Random — 随机捕获一个

```yaml
Random:
  all: <提供集合的表达式>
  condition:
    - <过滤条件>
  var: <绑定变量名>
```

从满足条件的实体中**随机选一个**，绑定到 var。找不到返回 None。

### 嵌套捕获

捕获节点可以嵌套在另一个捕获的 condition 中：

```yaml
Any:
  all:
    GetField:
      - _G
      - all_countries
  condition:
    - And:
      - Compare:
        - GetField:
            - country
            - stability
        - ">"
        - 10
      - Every:
          all:
            GetField:
              - country
              - companies
          condition:
            - Compare:
              - GetField:
                  - company
                  - labor_capital_conflict
              - ">"
              - 50
          var: target_companies
  var: country
```

内层捕获的变量在整个事件上下文中可见，外层和效果部分都可以引用。

---

## 效果节点

### ModifyAttr — 修改属性

```yaml
ModifyAttr:
  - <目标变量名>
  - Modifiers:
    - Modifier:
        type: <修改类型>
        field: <字段名>
        value: <数值>
```

如果目标变量绑定的是列表，则对列表中每个实体都应用修改。

**修改类型：**

| type | 计算方式 | 示例 |
|------|---------|------|
| `add` | `current + value` | `value: -10` → 减少10 |
| `percent` | `current * (1 + value/100)` | `value: 10` → 增加10% |
| `set` | `value` | `value: 50` → 直接设为50 |

可以对同一目标写多个 Modifier，按顺序执行。

### EffectCall — 注册效果调用

通过效果注册表调用自定义业务逻辑：

```yaml
LoanRequest:
  - <目标变量名>
  - template: B01
    amount: 1000
```

YAML 加载器会根据节点名称查找注册表。如果名称已注册，则解析为 EffectCall 节点。

Python 侧注册：
```python
from system.event import register_effect

def handle_loan_request(context, target, template, **kwargs):
    ...

register_effect("LoanRequest", handle_loan_request)
```

---

## Truthy/Falsy 规则

| 值 | 判定 |
|----|------|
| `None` | falsy |
| `0` | falsy |
| `""` (空字符串) | falsy |
| `[]` (空列表) | falsy |
| `False` | falsy |
| 其他一切 | truthy |

这些规则决定了 If 是否执行、And/Or 的短路行为、以及捕获是否算成功。

---

## 完整示例

### 示例 1：找所有稳定值大于 10 的国家

```yaml
events:
  - id: find_stable_countries
    name: "标记稳定国家"
    expr:
      - If:
        - Every:
            all:
              GetField:
                - _G
                - all_countries
            condition:
              - Compare:
                - GetField:
                    - target
                    - stability
                - ">"
                - 10
            var: target
        - ModifyAttr:
          - target
          - Modifiers:
            - Modifier:
                type: add
                field: stability
                value: -5
```

### 示例 2：完整事件——嵌套捕获 + 多效果

"找一个社会稳定度 > 10 的国家，并找到该国所有劳资冲突度 > 50 且最大历史销量 > 500 的公司，然后降低国家稳定度，提高这些公司产量"。

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
                - Compare:
                  - GetField:
                      - target_country
                      - stability
                  - ">"
                  - 10
                - Every:
                    all:
                      GetField:
                        - target_country
                        - companies
                    condition:
                      - And:
                        - Compare:
                          - GetField:
                              - target_company
                              - labor_capital_conflict
                          - ">"
                          - 50
                        - Compare:
                          - GetField:
                              - target_company
                              - max_history_sales
                          - ">"
                          - 500
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
```

**执行流程：**

1. 遍历 `_G.all_countries`
2. 对每个国家，临时绑定到 `target_country`，用 Compare 检查 `stability > 10`
3. 如果通过，在该国家的 `companies` 中用 Every 筛选 `labor_capital_conflict > 50 And max_history_sales > 500`
4. 如果内层 Every 结果非空（有满足条件的公司），And 整体为 truthy → Any 捕获成功
5. If 条件为 truthy → 执行 Exprs 主体
6. 对 `target_country` 的 stability 减 10
7. 对 `target_companies` 列表中每个公司的 production 加 10%

---

## 向后兼容

旧格式（GetField 带 op/value）仍然支持，加载时自动转为 Compare：

```yaml
# 旧格式（仍可用，但不推荐）
GetField:
  - target_country
  - stability
op: ">"
value: 10

# 等价于新格式
Compare:
  - GetField:
      - target_country
      - stability
  - ">"
  - 10
```

---

## 扩展指南

### 添加新的效果类型

1. 在 Python 侧定义 handler 函数
2. 调用 `register_effect("EffectName", handler)` 注册
3. 在 YAML 中直接使用 `EffectName:` 作为节点名

### 添加新的比较运算符

修改 `system/event/expr.py` 中的 `_compare` 函数，添加新的 op 分支。

### 添加新的表达式节点类型

1. 在 `expr.py` 中继承 `Expr`，实现 `evaluate` 方法
2. 在 `event_loader.py` 的 `_parse_node` 中添加对应的解析分支
