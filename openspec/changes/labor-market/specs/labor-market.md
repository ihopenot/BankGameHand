## ADDED Requirements

### Requirement: labor-demand-on-factory

每种工厂类型定义满效率运转所需的劳动力点数（`labor_demand`）。

#### Scenario: factory-type-has-labor-demand
- **WHEN** 加载工厂类型配置
- **THEN** 每个 `FactoryType` 包含 `labor_demand: int` 字段，表示满产所需劳动力点数

### Requirement: remove-base-production

移除 `FactoryType.base_production` 参数，基础产量固定为 1 倍。

#### Scenario: production-without-base-production
- **WHEN** 工厂执行生产
- **THEN** 基础产量 = `recipe.output_quantity`（不再乘以 `base_production`）

### Requirement: folk-labor-supply

居民组提供可配置的劳动力供给。

#### Scenario: folk-provides-labor-points
- **WHEN** 计算居民组劳动力供给
- **THEN** 劳动力点数 = `population × labor_participation_rate × labor_points_per_capita`

### Requirement: enterprise-wage-decision

企业决策组件包含工资决策能力。

#### Scenario: classic-decision-fixed-wage
- **WHEN** ClassicCompanyDecisionComponent 执行 `decide_wage()`
- **THEN** 返回配置中的 `initial_wage`，不做动态调整

### Requirement: labor-market-matching

劳动力市场按工资从高到低匹配岗位。

#### Scenario: jobs-filled-by-wage-descending
- **WHEN** 多家企业发布岗位（各企业的所有工厂 `labor_demand` 之和），各自标价为企业统一 `wage`
- **THEN** 所有岗位按 wage 从高到低排序，从总劳动力池中依次填满，直到劳动力耗尽或全部岗位填满

#### Scenario: partial-staffing
- **WHEN** 劳动力不足以填满某企业全部岗位
- **THEN** 该企业 `staffing_ratio = filled_points / total_demand`，且 `0 ≤ staffing_ratio ≤ 1`

#### Scenario: excess-labor
- **WHEN** 劳动力供给超过所有企业岗位总需求
- **THEN** 所有企业 `staffing_ratio = 1.0`，剩余劳动力闲置

### Requirement: production-constrained-by-staffing

生产同时受原材料和劳动力约束，取最小值。

#### Scenario: production-with-both-constraints
- **WHEN** 工厂拥有原材料且已知 staffing_ratio
- **THEN** `output = recipe.output_quantity × min(material_ratio, staffing_ratio)`

#### Scenario: zero-staffing-no-production
- **WHEN** 企业 staffing_ratio = 0（无工人到岗）
- **THEN** 工厂产出为 0，即使原材料充足

### Requirement: wage-payment-as-liability

工资以当回合到期负债形式支付。

#### Scenario: wage-liability-created-at-production
- **WHEN** 生产阶段完成
- **THEN** 为企业生成一笔负债：金额 = `filled_labor_points × wage`，当回合到期

#### Scenario: wage-settled-in-settlement-phase
- **WHEN** 结算阶段执行
- **THEN** 工资负债从企业 cash 中扣除

### Requirement: game-loop-reorder

游戏循环新增 Labor Match 阶段，Plan 阶段前移。

#### Scenario: new-phase-order
- **WHEN** 执行一个完整回合
- **THEN** 阶段顺序为：Update → Sell → Buy → Plan → Labor Match → Produce → Loan → Player Act → Settlement → Act → Snapshot
