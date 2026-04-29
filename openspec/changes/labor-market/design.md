## Context

BankGameHand 是一个回合制经济模拟策略游戏，包含三条完整供应链（电子、纺织、食品）、19 家 AI 企业、3 个居民组和银行系统。当前生产系统仅受原材料约束，缺少劳动力要素。本次变更引入劳动力市场，使生产同时受劳动力和原材料双重约束。

现有架构采用 Entity-Component-System 模式：Entity 持有 Component，Service 层处理业务逻辑，Game 类编排回合循环。

## Goals / Non-Goals

**Goals:**
- 新增劳动力市场匹配系统（LaborService）
- 工厂生产受劳动力 staffing_ratio 约束
- 企业决策器支持工资定价（初版固定工资）
- 工资以负债形式在结算阶段统一支付
- 移除 base_production，简化产量计算

**Non-Goals:**
- 不改变居民消费逻辑（消费需求不与工资收入挂钩）
- 不实现动态工资调整策略（Classic 决策固定返回 initial_wage）
- 不实现劳动力技能/专业化分工
- 不实现失业保险或社会保障

## Decisions

1. **生产约束取最小值**：`output = recipe.output_quantity × min(material_ratio, staffing_ratio)`，木桶效应更符合真实生产逻辑
2. **企业统一工资**：一家企业所有工厂的工人拿同样工资，与现有企业级决策架构一致
3. **劳动力全局池匹配**：所有居民组的劳动力汇总为一个池，按企业工资从高到低填满岗位
4. **工资作为当回合负债**：生产阶段生成负债，结算阶段扣款，复用现有 LedgerComponent 的 bill 机制
5. **Plan 阶段前移**：Plan（含工资决策）在 Labor Match 之前，确保企业先定工资再匹配
6. **移除 base_production**：所有工厂基础产量倍数统一为 1，简化模型
7. **labor_supply 返回 int**：虽然计算中间值为 float，但最终取整返回 int，与 labor_demand 的 int 类型一致，避免浮点比较问题
8. **Folk labor_participation_rate 范围 [0, 1]**：不添加构造器验证，由配置保证正确性（与现有 w_quality 等权重字段风格一致）
9. **ProductorComponent.produce() 的 require_goods 使用 base=1**：移除 base_production 后，require_goods 的 base 参数从 recipe.input_quantity 改为 1，允许取部分原料（不强制整除），支持更细粒度的充足率计算
10. **company_service.buy_phase 需求公式**：从 `input_quantity * base_production * built_count` 改为 `input_quantity * built_count`，每台工厂需要 recipe.input_quantity 的原料
11. **WorkTree 路径**: `D:/work/BankGameHand/.worktrees/labor-market`，分支 `feature/labor-market`
12. **filled_labor_points 由 labor_match_phase 设置**：Game 在 labor_match_phase 中计算每企业的实际填满劳动力点数并存储到 company.filled_labor_points，供 product_phase 的工资负债计算使用
13. **folks_for_wage 绑定到第一个居民组**：工资负债的 creditor 使用 folk 列表中的第一个居民组，简化实现；所有居民组共享工资收入（通过 LedgerComponent 进行财务记录）

## Risks / Trade-offs

- **移除 base_production 是破坏性变更**：所有现有工厂配置和测试中引用 base_production 的地方都需要修改，但简化了长期维护
- **固定工资缺乏动态性**：初版中企业无法根据市场调整工资，劳动力市场竞争有限，但降低了初版复杂度
- **工资不影响消费**：工资支付但不影响居民购买力，经济循环不完整，但避免了本次变更范围过大
