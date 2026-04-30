## Context

BankGameHand 是一个银行经济模拟游戏，采用 ECS 架构。企业决策通过 `BaseCompanyDecisionComponent` 模式实现，但居民（Folk）的购买逻辑硬编码在 `FolkService` 中。当前企业的科研、品牌、维护支出是"内部消耗"，资金不会流向居民部门，经济循环不完整。

## Goals / Non-Goals

**Goals:**
- 将决策组件从 `component/` 顶层重组到 `component/decision/` 子包（company/ + folk/）
- 新增居民决策组件（Base + Classic），实现 `decide_spending()` 支出决策 API
- 企业科研、品牌、维护支出按配置比例分流到各 Folk 组
- 维护费用从企业实际扣款并流入居民
- 重构 FolkService，将需求计算委托给决策组件

**Non-Goals:**
- 不实现居民 AI 决策组件（后续扩展）
- 不实现居民贷款或储蓄决策
- 不改变企业决策组件的现有 API 和行为
- 不实现工资/薪酬机制（本次仅处理企业支出分流）

## Decisions

1. **决策组件放 component/decision/ 子包**：按 sector 分子目录（company/、folk/），注册表机制各自独立。企业注册表保留在 company/base.py 中，居民注册表在 folk/base.py 中。

2. **居民决策器附加到 Folk 实体**：与企业决策器附加到 Company 实体模式一致，遵循 ECS 模式。不创建独立的"居民部门"实体。

3. **居民决策器不定义新特质**：直接使用 Folk 实体已有的 `w_quality`、`w_brand`、`w_price` 等属性，避免重复定义。

4. **decide_spending() 输出预算+需求量**：返回 `{goods_type_name: {"budget": int, "demand": int}}`，购买时同时受预算和需求量约束。

5. **支出分流配置放 folk.yaml**：由居民侧定义如何接收企业支出，不放在企业配置中。加载时校验各组分配比例之和为 1。

6. **act_phase 同步分流**：在企业执行投资时同步计算并分配资金到 Folk 组，不新增游戏阶段。

7. **维护费用实际扣款**：当前维护成本仅用于计算预留金，本次新增实际扣款逻辑，扣款金额同时按比例分流给居民。

8. **spending_tendency 不引入 economy context**：spec 提到 spending_tendency "derived from w_* weights and economy context"，但实现中 economy_cycle_index 仅通过 demand 公式间接影响预算。直接将 economy context 加入 spending_tendency 会导致双重计算。spending_tendency = w_quality + w_brand + w_price，保持语义清晰。

9. **economy_cycle_index 默认值 0.0**：表示无经济周期影响（中性），而非 1.0（繁荣）。

## Risks / Trade-offs

- **导入路径变更范围大**：约 15+ 个文件需要更新 import 路径，迁移期间可能遗漏。通过运行全量测试检测。
- **维护扣款可能影响企业现金流**：新增维护费用实际扣款后，企业现金会更紧张，可能增加破产概率。需通过集成测试验证。
- **决策组件双重约束**：预算和需求量同时约束购买，可能导致某些场景下两者不一致（如预算不足但需求高）。购买逻辑取 `min(预算允许量, 需求量)`。
