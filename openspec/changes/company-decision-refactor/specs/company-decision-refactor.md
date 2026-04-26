## ADDED Requirements

### Requirement: BaseCompanyDecisionComponent 抽象基类

定义统一的企业决策组件接口，合并原 DecisionComponent 的 CEO 特质存储。

#### Scenario: 基类定义完整 API

- **WHEN** 创建 BaseCompanyDecisionComponent
- **THEN** 包含 6 维 CEO 特质属性（business_acumen, risk_appetite, profit_focus, marketing_awareness, tech_focus, price_sensitivity），取值 [0, 1]
- **THEN** 包含 investment_plan 字典属性
- **THEN** 定义 `set_context(context: dict) -> None` 方法
- **THEN** 定义 5 个抽象决策方法：`decide_pricing()`, `decide_investment_plan()`, `decide_loan_needs()`, `decide_budget_allocation()`, `make_purchase_sort_key()`

#### Scenario: Context Dict 结构

- **WHEN** 调用 `set_context(context)`
- **THEN** context 包含 5 个模块 key：`company`, `ledger`, `productor`, `metric`, `market`
- **THEN** `company` 包含 `name: str` 和 `ceo_traits: dict`（6 个特质）
- **THEN** `ledger` 包含 `cash`, `revenue`, `expense`, `receivables`, `payables`（全部 int）
- **THEN** `productor` 包含 `factories: list`, `tech_levels: dict`, `brand_values: dict`, `current_prices: dict`
- **THEN** `metric` 包含 `my_sell_orders: dict`, `my_sold_quantities: dict`, `last_revenue: int`
- **THEN** `market` 包含 `economy_index: float`, `sell_orders: list`, `trades: list`

### Requirement: ClassicCompanyDecisionComponent 经典决策

将现有 DecisionService 的公式逻辑迁移为组件方法，行为完全一致。

#### Scenario: 定价决策与原逻辑一致

- **WHEN** 调用 `set_context()` 后调用 `decide_pricing()`
- **THEN** 返回 `dict[str, int]`（goods_type_name → new_price）
- **THEN** 定价逻辑与原 `DecisionService.decide_pricing()` 完全一致（基于 sold/listed 比较、risk_appetite、profit_focus、business_acumen 噪声）

#### Scenario: 投资计划与原逻辑一致

- **WHEN** 调用 `decide_investment_plan()`
- **THEN** 返回 `{"expansion": int, "brand": int, "tech": int}`
- **THEN** 各项计算与原 `_plan_expansion`, `_plan_brand`, `_plan_tech` 一致

#### Scenario: 贷款需求与原逻辑一致

- **WHEN** 调用 `decide_loan_needs()`
- **THEN** 返回 `(amount: int, max_rate: int)`
- **THEN** 计算逻辑与原 `calc_loan_needs` 一致

#### Scenario: 预算分配与原逻辑一致

- **WHEN** 调用 `decide_budget_allocation()`
- **THEN** 返回实际分配金额 `{"expansion": int, "brand": int, "tech": int}`
- **THEN** 逻辑与原 `act_phase` 的预算分配一致

#### Scenario: 采购排序与原逻辑一致

- **WHEN** 调用 `make_purchase_sort_key()`
- **THEN** 返回 `Callable[[SellOrder], float]`
- **THEN** 排序逻辑与原 `make_purchase_sort_key` 一致

### Requirement: AICompanyDecisionComponent AI 决策

通过 MCPAgentSDK 调用 LLM 完成定价、投资计划、贷款需求决策。

#### Scenario: set_context 触发 AI 调用

- **WHEN** 调用 `set_context(context)`
- **THEN** 内部使用 `asyncio.run()` 启动 MCPAgentSDK agent
- **THEN** agent 收到包含完整 context JSON 的 prompt
- **THEN** agent 返回包含 3 个决策的 JSON
- **THEN** 结果缓存在 `self._ai_decisions`

#### Scenario: AI 返回 JSON 验证

- **WHEN** agent 返回结果
- **THEN** `validate_fn` 检查 JSON 包含 `pricing`, `investment_plan`, `loan_needs` 三个 key
- **THEN** 验证 `pricing` 值为 `dict[str, int]`（goods_type → price, price > 0）
- **THEN** 验证 `investment_plan` 包含 `expansion`, `brand`, `tech` 三个 int >= 0 的值
- **THEN** 验证 `loan_needs` 包含 `amount: int >= 0` 和 `max_rate: int >= 0`
- **THEN** 验证失败时自动重试（最多 3 次）

#### Scenario: AI 决策方法读取缓存

- **WHEN** `set_context()` 完成后调用 `decide_pricing()`
- **THEN** 直接返回 `self._ai_decisions["pricing"]`，不再调用 AI

#### Scenario: 预算分配和采购排序沿用 Classic

- **WHEN** 调用 `decide_budget_allocation()` 或 `make_purchase_sort_key()`
- **THEN** 使用继承自 ClassicCompanyDecisionComponent 的实现

### Requirement: DecisionService 重构为编排层

#### Scenario: 通过组件委托决策

- **WHEN** `plan_phase(companies)` 被调用
- **THEN** 对每个 company：组装 context dict → 调用 `component.set_context()` → 读取决策结果
- **THEN** 不再直接计算任何决策逻辑

#### Scenario: 组装 Context Dict

- **WHEN** 构建 context
- **THEN** `_build_context(company)` 从 LedgerComponent, ProductorComponent, MetricComponent, DecisionComponent(base) 读取数据
- **THEN** market 数据由外部传入（Game 在调用 DecisionService 前提供）

### Requirement: 删除旧 DecisionComponent

#### Scenario: 完全移除

- **WHEN** 重构完成
- **THEN** `component/decision_component.py` 文件删除
- **THEN** 所有 `from component.decision_component import DecisionComponent` 引用迁移
- **THEN** `Company.__init__` 改为初始化 ClassicCompanyDecisionComponent 或 AICompanyDecisionComponent
