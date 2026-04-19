## Context

BankGameHand 使用 Entity-Component-System 架构，当前有 4 个组件：`DecisionComponent`、`LedgerComponent`、`ProductorComponent`、`StorageComponent`。

`DecisionComponent` 承担了两类职责：
1. **决策特质**：6 维 CEO 特质（`business_acumen`、`risk_appetite` 等）和投资计划（`investment_plan`）
2. **观测指标**：`last_sell_orders`、`last_sold_quantities`、`last_revenue`、`last_avg_buy_prices`

这两类职责混合导致了职责不清，且观测指标字段从未被写入，造成价格更新和投资功能失效。

Folk 实体在 `folk.py` 中直接存储了 `last_avg_buy_prices` 属性（非通过组件），Bank 实体无任何指标记录。

## Goals / Non-Goals

**Goals:**
- 创建统一的 `MetricComponent`，负责所有实体的指标追踪和历史记录
- 修复价格更新和投资不生效的 Bug（通过正确写入指标数据）
- 为 Company、Folk、Bank 三种实体提供每轮历史快照
- 保持与现有 ECS 架构一致的设计风格

**Non-Goals:**
- 不实现数据导出功能（CSV/JSON），留给后续 feature
- 不修改 DecisionService 的决策算法本身，只修复数据来源
- 不实现可视化/图表展示
- 不修改 `investment_plan` 的位置，它留在 `DecisionComponent`

## Decisions

1. **MetricComponent 为通用组件**：同一个 `MetricComponent` 类挂载到 Company、Folk、Bank。不同实体的快照内容通过 `RoundSnapshot` 的可选字段区分，而非创建多个子类。

2. **历史全量保留**：游戏最多 20 轮，全量保留不会有内存问题。

3. **字段迁移策略**：从 `DecisionComponent` 移除 `last_sell_orders`、`last_sold_quantities`、`last_revenue`、`last_avg_buy_prices` 四个字段，迁移到 `MetricComponent`。从 `Folk` 实体移除 `last_avg_buy_prices` 属性，迁移到 `MetricComponent`。`DecisionService` 改为从 `MetricComponent` 读取。同时移除了 `DecisionComponent` 对 `entity.goods.GoodsType` 的导入依赖。

4. **MetricService 负责快照采集**：在 `game_loop` 每轮结束（`act_phase` 之后）调用 `MetricService.snapshot_phase()` 采集所有实体的当轮状态。`MetricService.reset_all()` 在每轮开始时重置当轮指标。

5. **指标写入点分散在各服务中**：`last_sell_orders` 在 `CompanyService.sell_phase()` 写入；`last_sold_quantities` 和 `last_revenue` 在 `FolkService.settle_trades()` 和 `CompanyService.settle_trades()` 中写入；`last_avg_buy_prices` 在 `CompanyService._update_avg_buy_prices()` 和 `FolkService._update_avg_buy_prices()` 中写入到 `MetricComponent`。

6. **累计投资计数器在 act_phase 中更新**：`cumulative_brand_spend`、`cumulative_tech_spend`、`cumulative_expansion_spend` 在 `DecisionService.act_phase()` 中实际花钱时累加。`cumulative_revenue` 在 `MetricService.snapshot_phase()` 中累加。

7. **math.exp 溢出保护**：`_price_attractiveness()` 函数在 `DecisionService` 和 `FolkService` 中添加了 x 值 clamp（[-500, 500]），防止价格偏离极大时 `math.exp(-x)` 溢出。这是因为修复指标写入后，价格动态调整功能实际运行，可能产生极端价格差异。

8. **测试隔离改进**：在 `conftest.py` 添加了 `_clear_component_registries` 自动清理 fixture，并在 `test_integration.py` 的 setup/teardown 中添加了 `DecisionComponent.components.clear()` 和 `MetricComponent.components.clear()`，防止跨测试的 class-level 组件列表污染。

## Risks / Trade-offs

- **迁移影响面较大**：需更新所有引用迁移字段的代码和测试。通过 TDD 方式逐步迁移降低风险。
- **MetricComponent 通用化 vs 专用化**：通用组件简单但 `RoundSnapshot` 有较多可选字段。当前实体类型少（3 种），通用方案更合适。
- **快照采集时机**：放在每轮末尾意味着快照反映的是投资执行后的状态。若需要投资前/后对比，需要更精细的时机控制——当前不需要。
