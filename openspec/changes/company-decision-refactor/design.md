## Context

BankGameHand 使用 ECS 架构，企业决策当前由 `DecisionComponent`（存储 CEO 特质）和 `DecisionService`（决策逻辑）两部分组成。所有决策为公式驱动，参数化于 `config/decision.yaml`。

用户希望引入 AI 驱动的决策模式，使用 MCPAgentSDK 调用 LLM，与经典公式模式可互换。

## Goals / Non-Goals

**Goals:**
- 定义 `BaseCompanyDecisionComponent` 抽象基类，统一 5 个决策 API
- 将现有公式逻辑迁移为 `ClassicCompanyDecisionComponent`
- 实现 `AICompanyDecisionComponent`，通过 MCPAgentSDK 在 `set_context()` 时一次性完成 3 个 AI 决策
- 验证 AI 返回的 JSON 包含所有决策结果
- 保持所有现有测试通过（行为不变）

**Non-Goals:**
- 不修改 `config/decision.yaml` 的参数结构
- 不改变游戏循环的阶段顺序
- 不优化 MCPAgentSDK 的性能（subprocess 开销可接受）
- 不实现 AI 决策的 budget_allocation 和 purchase_preference（这两个沿用 Classic 逻辑）

## Decisions

### D1: 组件继承结构

```
BaseCompanyDecisionComponent (BaseComponent + ABC)
  └── ClassicCompanyDecisionComponent
        └── AICompanyDecisionComponent
```

AI 继承 Classic 而非直接继承 Base，因为 budget_allocation 和 purchase_preference 复用 Classic 实现。

### D2: CEO 特质合并入基类

删除原 `DecisionComponent`，将 6 维 CEO 特质和 `investment_plan` 移入 `BaseCompanyDecisionComponent`。
所有引用 `DecisionComponent` 的代码迁移至新基类。

### D3: Context Dict 设计

`set_context()` 接收按模块分类的 dict：

```python
{
    "company": { "name", "ceo_traits": {6 traits} },
    "ledger": { "cash", "revenue", "expense", "receivables", "payables" },
    "productor": { "factories": Dict[FactoryType, List[Factory]], "tech_levels", "brand_values", "current_prices": Dict[GoodsType, int] },
    "metric": { "my_sell_orders": Dict[GoodsType, int], "my_sold_quantities": Dict[GoodsType, int], "last_revenue", "my_avg_buy_prices": Dict[GoodsType, float] },
    "market": { "economy_index", "sell_orders", "trades" },
}
```

**实现细节**：`set_context` 在基类中为具体方法（非抽象），存储 `self._context`。`productor.factories` 保持与 `ProductorComponent.factories` 相同的 `Dict[FactoryType, List[Factory]]` 格式，确保 `_calc_operating_expense` 按已建成工厂实例计数。`metric.my_avg_buy_prices` 用于采购排序。

### D7: DecisionService 重构

DecisionService 变为轻量编排层：
- `_build_context(company)` 从各 Component 组装 context dict
- `_get_decision_component(company)` 遍历 `_components.values()` 查找 `BaseCompanyDecisionComponent` 子类实例（因为 Entity.get_component 按精确类型匹配，不支持基类查找）
- `plan_phase` / `act_phase` / `calc_loan_needs` 调用组件方法而非自行计算
- 市场数据通过 `set_market_data()` 由 Game 在 `plan_phase` 前传入
- `make_purchase_sort_key` 委托到组件

### D8: 代码审查修复

- `_calc_operating_expense` 修复：从按 FactoryType 计数改为按已建成 Factory 实例计数（与原 DecisionService 一致）
- `decide_loan_needs` 新增 `max_rate` 返回值：`int((1 - risk_appetite) * 15) + 3`
- 旧 `DecisionComponent` 已删除，所有引用迁移至 `BaseCompanyDecisionComponent` 或 `ClassicCompanyDecisionComponent`
- `Company` 实体使用 `ClassicCompanyDecisionComponent`
- Game 在 `plan_phase` 前调用 `DecisionService.set_market_data()` 传递市场数据

AI 覆写 `decide_pricing`、`decide_investment_plan`、`decide_loan_needs`。
`decide_budget_allocation` 和 `make_purchase_sort_key` 继承 Classic 实现不变。

### D5: 同步 API + 内部 async

Base API 全部为同步方法。`AICompanyDecisionComponent.set_context()` 内部使用 `asyncio.run()` 执行 MCPAgentSDK 异步调用。

### D6: MCPAgentSDK 集成方式

- `set_context()` 时构造 prompt（含完整 context JSON），调用 `sdk.run_agent()`
- `validate_fn` 验证返回 JSON 包含 `pricing`、`investment_plan`、`loan_needs` 三个 key 及正确类型
- `max_retries=3` 自动重试验证失败
- 决策结果缓存在 `self._ai_decisions`，后续 API 直接读取

### D7: DecisionService 重构

DecisionService 变为轻量编排层：
- `_build_context(company)` 从各 Component 组装 context dict
- `plan_phase` / `act_phase` / `calc_loan_needs` 调用组件方法而非自行计算
- 市场数据通过 Game 传入 DecisionService

## Risks / Trade-offs

- **AI 性能**：每公司每轮 1 次 subprocess 启动 + LLM 调用。回合制游戏可接受，但多公司场景需考虑并发
- **AI 输出可靠性**：依赖 validate_fn + retry 保证结构正确，但语义合理性无法验证（如定价为负数）
- **测试复杂度**：AI 决策不可确定性测试，需 mock MCPAgentSDK
