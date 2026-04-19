## ADDED Requirements

### Requirement: MetricComponent 指标追踪

MetricComponent 是一个通用指标组件，挂载到 Company、Folk、Bank 实体，负责存储当前轮次指标和历史快照。

#### Scenario: Company 挂载 MetricComponent

- **WHEN** 创建一个 Company 实体
- **THEN** Company 自动拥有 MetricComponent
- **AND** MetricComponent 包含 `last_sell_orders`、`last_sold_quantities`、`last_revenue`、`last_avg_buy_prices` 字段，初始值为空/零
- **AND** MetricComponent 包含累计计数器 `cumulative_revenue`、`cumulative_brand_spend`、`cumulative_tech_spend`、`cumulative_expansion_spend`，初始为 0
- **AND** MetricComponent 包含 `round_history` 列表，初始为空

#### Scenario: Folk 挂载 MetricComponent

- **WHEN** 创建一个 Folk 实体
- **THEN** Folk 自动拥有 MetricComponent
- **AND** MetricComponent 包含 `last_avg_buy_prices` 字段，初始为空字典

#### Scenario: Bank 挂载 MetricComponent

- **WHEN** 创建一个 Bank 实体
- **THEN** Bank 自动拥有 MetricComponent

### Requirement: 销售指标写入

#### Scenario: sell_phase 记录挂单量

- **WHEN** CompanyService.sell_phase() 执行完毕
- **THEN** 每个 Company 的 MetricComponent.last_sell_orders 记录了该公司本轮对每种 GoodsType 的挂单总量

#### Scenario: trade 结算记录成交量和收入

- **WHEN** 居民或企业购买了某公司的商品（通过 FolkService 或 CompanyService 的 trade 结算）
- **THEN** 卖方 Company 的 MetricComponent.last_sold_quantities 累加实际成交量
- **AND** 卖方 Company 的 MetricComponent.last_revenue 累加成交金额

### Requirement: 价格更新生效

#### Scenario: 全部售罄时涨价

- **WHEN** 某公司某商品的 last_sold_quantities >= last_sell_orders（即全部售罄或超卖）
- **THEN** DecisionService.decide_pricing() 对该商品执行涨价逻辑
- **AND** 新价格 > 旧价格（忽略噪声影响）

#### Scenario: 部分滞销时降价

- **WHEN** 某公司某商品的 last_sold_quantities < last_sell_orders（有滞销）
- **THEN** DecisionService.decide_pricing() 对该商品执行降价逻辑
- **AND** 新价格 < 旧价格（忽略噪声影响）

### Requirement: 投资生效

#### Scenario: 有收入时品牌投资非零

- **WHEN** 某公司 MetricComponent.last_revenue > 0
- **THEN** _plan_brand() 返回正数品牌投资计划金额

#### Scenario: 有收入时科技投资非零

- **WHEN** 某公司 MetricComponent.last_revenue > 0
- **THEN** _plan_tech() 返回正数科技投资计划金额

### Requirement: 历史快照记录

#### Scenario: 每轮结束后采集快照

- **WHEN** 一轮游戏循环结束（act_phase 之后）
- **THEN** MetricService.snapshot_phase() 为每个实体生成一份 RoundSnapshot 并追加到 MetricComponent.round_history
- **AND** RoundSnapshot 包含轮次编号和该实体的关键指标

### Requirement: DecisionComponent 字段迁移

#### Scenario: DecisionComponent 不再包含观测字段

- **WHEN** 访问 DecisionComponent 实例
- **THEN** 不存在 `last_sell_orders`、`last_sold_quantities`、`last_revenue`、`last_avg_buy_prices` 属性

#### Scenario: Folk 不再直接包含 last_avg_buy_prices

- **WHEN** 访问 Folk 实例
- **THEN** `last_avg_buy_prices` 不作为 Folk 的直接属性存在
- **AND** 该数据存储在 Folk 的 MetricComponent 中
