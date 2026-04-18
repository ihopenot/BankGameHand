## Context

BankGameHand 是一个回合制经济模拟策略游戏，采用 ECS + Service 层架构。当前已实现完整的经济周期、市场交易、生产系统、居民消费和财务结算，但企业 AI 决策系统（game.py 的 plan_phase 和 act_phase）尚为空 stub。

设计文档 `docs/GameDesign/Company.md` 定义了 5 维 CEO 特质和企业决策的完整公式。本次实现将这些设计落地为代码。

## Goals / Non-Goals

**Goals:**
- 实现完整的 CEO 特质体系（5 维特质，随机生成或配置加载）
- 实现企业决策系统：定价、投资计划、采购偏好、品牌投入、科技投入
- plan_phase 生成投资计划表（不扣钱），act_phase 按预算执行投资
- 保留金机制：CEO 保守倾向影响投资预算
- 所有决策系数配置化（decision.yaml）

**Non-Goals:**
- 工资发放决策（暂不实现）
- 贷款申请流程（属于后续的银行玩家操作系统）
- 破产清算机制（属于独立的 openspec change）
- Warmup 阶段的自动运行
- 政府干预系统

## Decisions

1. **新增 DecisionComponent 而非扩展 Company 类**：遵循项目 ECS 模式，CEO 特质、投资计划表和决策状态作为独立组件挂载
2. **新增 DecisionService 而非在 CompanyService 中实现**：每个 Service 职责单一，DecisionService 专注决策逻辑编排
3. **plan_phase 只生成计划不扣钱**：plan_phase 计算三个投资方向（扩产/品牌/科技）的计划金额，存入 DecisionComponent.investment_plan；act_phase 根据预算执行
4. **保留金机制**：`reserved = operating_expense × (1 + (1 - risk_appetite) × reserve_coeff)`，经营开销当前仅含已建成工厂的 maintenance_cost
5. **投资预算分配**：budget = cash - reserved。预算充足时全额执行；不足时按计划比例分配。扩产不够建厂则回流
6. **采购偏好修改方式**：在 CompanyService.buy_phase 中添加 `decision_service=None` 可选参数，保持向后兼容
7. **噪声实现**：使用 Python random 模块生成高斯噪声
8. **品牌/科技投入均分策略**：品牌支出按产出商品类型均分，科技支出按配方均分
9. **供需比暂用占位值 0.8**：待后续集成 MarketService 统计

## Risks / Trade-offs

- **公式平衡性**：系数需要大量 playtest 调优。缓解：系数全部配置化
- **保留金可能过于保守**：reserve_coeff=2.0 时保守 CEO 保留三倍开销，可能导致长期不投资。缓解：系数可调
- **扩产回流可能浪费分配额**：按比例分配后扩产份额不够建厂时，该资金回流而非重分配给品牌/科技。这是有意的简化设计
