# 经济反馈调节机制设计文档

## 概述

解决游戏中"资金堆积"问题——当前钱会自然累积在企业或居民手中，缺乏反馈调节。本设计引入两个互相耦合的动态机制：

1. **企业动态工资**：基于利润空间和现金水平渐进调整工资
2. **居民动态需求**：基于现金/开销比值调整消费需求，移除经济周期的直接影响

## 设计目标

- 资金在企业和居民之间自然流动，避免单向堆积
- 企业工资决策体现经济理性（优先保证利润）
- 居民消费行为反映财务状况（现金充裕则扩大消费）
- 变化平滑（增量式），符合经济粘性特征
- 与现有架构风格一致（配置驱动、Entity-Component模式）

## 一、企业动态工资机制

### 核心逻辑

企业每回合根据利润空间计算"目标工资"，然后从当前工资渐进逼近，同时用现金充裕度修正逼近速度。

### 公式

```
# 1. 计算目标工资（利润优先）
unit_cost_excl_wage = (原材料成本 + 维护费分摊) / 单位产量
target_profit_margin = profit_focus × base_profit_margin
target_wage_per_unit = 售价 - unit_cost_excl_wage - target_profit_margin × 售价
target_wage = target_wage_per_unit × 单位产量 / 劳动力需求

# 2. 现金调节因子
cash_ratio = 企业现金 / 上回合总运营支出
cash_factor = clamp(cash_ratio / target_cash_ratio, cash_factor_min, cash_factor_max)

# 3. 增量逼近
new_wage = current_wage + step_rate × (target_wage × cash_factor - current_wage)
```

### 参数说明

| 参数 | 含义 | 默认值 |
|------|------|--------|
| step_rate | 每回合向目标逼近的速率 | 0.2 |
| base_profit_margin | 基础目标利润率 | 0.15 |
| target_cash_ratio | 目标现金/运营支出比值 | 3.0 |
| cash_factor_min | 现金因子下限 | 0.5 |
| cash_factor_max | 现金因子上限 | 1.5 |

### CEO性格影响

- `profit_focus` 高 → 目标利润率高 → 目标工资较低（更看重企业盈利）
- `risk_appetite` 高 → 现金容忍度低 → cash_factor 倾向较大（愿意花钱）

### 数据来源

- **售价**：`ProductorComponent` 中的当前售价（取主要产品或加权平均）
- **原材料成本**：通过上回合采购记录计算单位原材料成本
- **维护费**：配置文件中工厂维护费 / 产能
- **劳动力需求**：工厂的 `labor_demand` 属性总和
- **上回合总运营支出**：`MetricComponent` 记录的上回合总支出（原材料+工资+维护）

### 初始化

- 第 1 回合：`current_wage = initial_wage`（配置值），开始演化
- 上回合运营支出为 0 时，`cash_ratio` 视为 `target_cash_ratio`（即中性状态）

### 无工资上下限

工资不设硬性上下限，由市场动态自行调节：
- 利润空间不足时目标工资自然降低
- 现金紧张时 cash_factor < 1 进一步抑制工资上涨
- 这两个因素共同构成自然约束

## 二、居民动态需求机制

### 核心逻辑

移除经济周期对需求的直接影响。居民记录上回合实际开销，通过"现金可支撑回合数"（R = 现金/开销）与目标阈值（T）的对比来调整需求乘数。

### 新增属性（Folk 实体）

| 属性 | 类型 | 含义 |
|------|------|------|
| last_spending | Money | 上回合实际总开销 |
| demand_multiplier | float | 当前需求乘数（初始 1.0） |
| savings_target_ratio | float | 目标现金/开销比值 |

### 公式

```
# 1. 计算当前比值
R = current_cash / last_spending
# 若 last_spending 为 0，则 R = savings_target_ratio（中性状态）

# 2. 计算偏离度
deviation = (R - T) / T    # T = savings_target_ratio

# 3. 平滑限幅调整（tanh）
adjustment = max_adjustment × tanh(sensitivity × deviation)

# 4. 增量更新 demand_multiplier
demand_multiplier = demand_multiplier × (1 + adjustment)
demand_multiplier = clamp(demand_multiplier, min_multiplier, max_multiplier)

# 5. 应用到需求计算（替代原有公式）
demand = population × per_capita × demand_multiplier
```

### 原公式对比

```
# 旧公式（移除）
demand = population × per_capita × (1 + economy_index × sensitivity)

# 新公式
demand = population × per_capita × demand_multiplier
```

### 不同居民群体参数

| 参数 | 低收入 | 中等 | 高收入 |
|------|--------|------|--------|
| savings_target_ratio | 3.0 | 5.0 | 8.0 |
| max_adjustment | 0.20 | 0.15 | 0.10 |
| sensitivity | 1.2 | 1.0 | 0.8 |
| min_multiplier | 0.4 | 0.3 | 0.5 |
| max_multiplier | 1.8 | 2.0 | 1.5 |

### 设计意图

- **低收入群体**：储蓄目标低（够用3回合即可），但调整幅度大（对财务变化更敏感）
- **高收入群体**：储蓄目标高（要求够用8回合），但调整温和（消费习惯稳定）

### 开销记录时机

- 在每回合 BUY 阶段结束后，将本回合所有商品购买的实际花费总和记录为 `last_spending`
- 包含所有类型商品（食品、电子、纺织等）的总花费

### 初始化

- 第 1 回合：`last_spending = 0`，此时 `R = T`（中性），`demand_multiplier = 1.0`
- 第 2 回合开始正常运作

## 三、经济周期角色变化

### 移除的影响

- 经济周期不再直接影响居民需求计算

### 保留的影响

- 经济周期仍然影响企业决策（如投资信心、定价策略）
- 经济周期通过影响企业行为（工资调整、雇佣策略），间接影响居民现金流入，从而间接影响需求

### 反馈闭环

```
经济周期 → 影响企业信心/投资 → 影响雇佣/工资 → 影响居民现金
→ 影响居民需求 → 影响企业销售/利润 → 影响企业工资决策 → (循环)
```

## 四、配置结构

### config/folk.yaml 新增

```yaml
demand_feedback:
  default_savings_target_ratio: 5.0
  default_max_adjustment: 0.15
  default_sensitivity: 1.0
  default_min_multiplier: 0.3
  default_max_multiplier: 2.0
```

每个居民组可覆盖默认值：

```yaml
folk_groups:
  - name: "低收入群体"
    demand_feedback:
      savings_target_ratio: 3.0
      max_adjustment: 0.20
      sensitivity: 1.2
      min_multiplier: 0.4
      max_multiplier: 1.8
```

### config/decisions.yaml（或 company 相关配置）新增

```yaml
wage_decision:
  step_rate: 0.2
  base_profit_margin: 0.15
  target_cash_ratio: 3.0
  cash_factor_min: 0.5
  cash_factor_max: 1.5
```

## 五、代码修改点

| 文件 | 改动内容 |
|------|---------|
| `entity/folk.py` | 新增 `last_spending`, `demand_multiplier` 属性 |
| `component/decision/folk/classic.py` | 重写需求计算：移除经济周期，使用 demand_multiplier |
| `system/folk_service.py` | BUY 阶段后记录 `last_spending`；需求计算前更新 `demand_multiplier` |
| `component/decision/company/classic.py` | 重写 `decide_wage()`：从固定值改为动态计算 |
| `config/folk.yaml` | 添加 demand_feedback 配置块 |
| `config/decisions.yaml` | 添加 wage_decision 配置块 |
| 相关测试文件 | 更新/新增测试覆盖新逻辑 |

## 六、游戏阶段集成

现有阶段顺序无需改变：

1. **UPDATE 阶段**：经济周期更新（保留，但不再直接影响需求）
2. **SELL 阶段前**：居民更新 `demand_multiplier`（基于上回合的 `last_spending`）
3. **BUY 阶段**：使用新的 `demand_multiplier` 计算需求量
4. **BUY 阶段后**：记录各居民组的实际花费 → `last_spending`
5. **PLAN 阶段**：企业 `decide_wage()` 使用新的动态逻辑
6. **LABOR MATCH 阶段**：使用新的动态工资值进行匹配

## 七、预期效果

- **资金堆积在企业时**：企业现金充裕 → cash_factor > 1 → 工资上涨 → 居民收入增加 → 消费增加 → 资金回流
- **资金堆积在居民时**：居民现金充裕 → R > T → demand_multiplier 上升 → 消费增加 → 企业收入增加
- **企业亏损时**：利润空间缩小 → 目标工资降低 → 工资下调 → 运营成本降低 → 利润恢复
- **居民现金不足时**：R < T → demand_multiplier 下降 → 消费减少 → 保存现金 → 恢复财务健康

## 八、风险与对策

| 风险 | 对策 |
|------|------|
| 工资螺旋下降（通缩循环） | step_rate 限制调整速度；cash_factor 在企业有钱时促进涨薪 |
| 需求过度波动 | tanh 限幅 + multiplier 的 min/max clamp |
| 第1回合冷启动 | last_spending=0 时视为中性状态，不触发调整 |
| 企业无销售数据 | 使用 initial_wage 作为 current_wage 起点，逐步演化 |
