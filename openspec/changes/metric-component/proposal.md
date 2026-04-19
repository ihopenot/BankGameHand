## Why

当前游戏中，`DecisionComponent` 存储了 `last_sell_orders`、`last_sold_quantities`、`last_revenue`、`last_avg_buy_prices` 等跟踪字段，但**从未有任何代码在游戏运行时写入这些字段**，导致：

1. **价格更新永远不生效** — `decide_pricing()` 读取 `last_sell_orders` 时始终为空字典，`listed == 0` 直接跳过，价格冻结在 `base_price`
2. **品牌/科技投资永远为零** — `_plan_brand()` 和 `_plan_tech()` 基于 `last_revenue`（始终为 0）计算，结果永远为 0

此外，项目缺少统一的历史数据记录机制，无法回溯各实体在每轮的状态变化。

## What Changes

1. **新增 `MetricComponent`** — 统一的指标追踪组件，挂载到 Company、Folk、Bank 三种实体
   - 迁移 `DecisionComponent` 中的观测类字段（`last_sell_orders`、`last_sold_quantities`、`last_revenue`、`last_avg_buy_prices`）
   - 新增每轮快照（`RoundSnapshot`）和累计计数器
2. **修复数据写入缺失** — 在 sell/buy/settle 阶段正确写入销售挂单量、成交量和收入
3. **更新 `DecisionService`** — 从 `MetricComponent` 读取指标数据，而非 `DecisionComponent`
4. **更新 `Company` 实体** — 初始化时挂载 `MetricComponent`
5. **新增 `MetricService`** — 负责每轮结束时采集快照

## Impact

- **组件层**：新增 `component/metric_component.py`；修改 `component/decision_component.py`（移除迁移字段和 GoodsType 依赖）
- **实体层**：修改 `entity/company/company.py`、`entity/folk.py`、`entity/bank.py`（挂载新组件）
- **服务层**：修改 `system/decision_service.py`、`system/company_service.py`、`system/folk_service.py`（指标读写迁移 + math.exp 溢出保护）；新增 `system/metric_service.py`
- **编排层**：修改 `game/game.py`（接入 MetricService 快照/重置阶段）
- **测试层**：新增 `tests/test_metric_component.py`、`tests/test_metric_service.py`；更新 `tests/test_decision_service.py`、`tests/test_decision_component.py`、`tests/test_folk.py`、`tests/test_folk_service.py`、`tests/test_company_sell_phase.py`、`tests/test_company_buy_settlement.py`、`tests/test_integration.py`、`tests/conftest.py`
