# Tasks: resident-decision-spending-flow

## 1. Decision component directory reorganization

- [x] 1.1 Move company decision files to component/decision/company/ and update all import paths  <!-- 非 TDD 任务 -->
  - [x] 1.1.1 执行变更：创建 `component/decision/__init__.py`、`component/decision/company/__init__.py`；将 `component/base_company_decision.py` 迁移为 `component/decision/company/base.py`，`component/classic_company_decision.py` 迁移为 `component/decision/company/classic.py`，`component/ai_company_decision.py` 迁移为 `component/decision/company/ai.py`；删除旧文件；更新所有外部导入路径（`system/decision_service.py`、`system/company_service.py`、`game/game.py`、`system/metric_service.py` 及约 15 个测试文件）
  - [x] 1.1.2 验证无回归（运行：`python -m pytest tests/ -q`，确认 514+ 测试全部通过）
  - [x] 1.1.3 检查：确认所有 `from component.base_company_decision`、`from component.classic_company_decision`、`from component.ai_company_decision` 引用已更新为 `from component.decision.company.base`、`from component.decision.company.classic`、`from component.decision.company.ai`；确认旧文件已删除

- [x] 1.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射（以 OpenSpec 路径为准）：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/resident-decision-spending-flow/specs/*.md` 和 `openspec/changes/resident-decision-spending-flow/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA（或分支基点）
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示（见 SKILL.md "代码审查用户指令"节），停止等待用户输入；用户选择"处理"类操作后，调用 superpowers:receiving-code-review 对每条审查意见做技术验证后再实施；按指令处理完成后继续下一任务组
  - 若仅有 Minor 或无问题：自动继续下一任务组，无需等待用户确认

## 2. Folk decision components

- [x] 2.1 Create BaseFolkDecisionComponent with decide_spending() abstract API  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_folk_decision.py` — 测试 BaseFolkDecisionComponent 是抽象类，不能实例化；测试 decide_spending() 是抽象方法；测试 set_context() 存储上下文
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_folk_decision.py -q`，确认因缺少实现而失败）
  - [x] 2.1.3 写最小实现：`component/decision/folk/base.py` — 实现 BaseFolkDecisionComponent（继承 BaseComponent + ABC），包含 `set_context()` 和抽象方法 `decide_spending() -> Dict[str, Dict]`；创建 `component/decision/folk/__init__.py`
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_folk_decision.py -q`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 Create ClassicFolkDecisionComponent implementing spending logic  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_classic_folk_decision.py` — 测试 decide_spending() 返回每个商品类型的 budget 和 demand；测试 demand 公式为 `population * per_capita * (1 + economy_cycle_index * sensitivity)`；测试 per_capita=0 时 budget=0, demand=0；测试 budget = demand * reference_price * spending_tendency；测试 Folk 的 w_* 属性被正确使用
  - [x] 2.2.2 验证测试失败（运行：`python -m pytest tests/test_classic_folk_decision.py -q`，确认因缺少实现而失败）
  - [x] 2.2.3 写最小实现：`component/decision/folk/classic.py` — 实现 ClassicFolkDecisionComponent，从 Folk 实体读取 population/w_quality/w_brand/w_price/base_demands，使用配置和上下文计算支出计划；注册为 "classic" 决策组件
  - [x] 2.2.4 验证测试通过（运行：`python -m pytest tests/test_classic_folk_decision.py -q`，确认所有测试通过，输出干净）
  - [x] 2.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射（以 OpenSpec 路径为准）：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/resident-decision-spending-flow/specs/*.md` 和 `openspec/changes/resident-decision-spending-flow/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA（或分支基点）
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入；用户选择"处理"类操作后，调用 superpowers:receiving-code-review 对每条审查意见做技术验证后再实施
  - 若仅有 Minor 或无问题：自动继续下一任务组，无需等待用户确认

## 3. Enterprise spending flow to residents

- [x] 3.1 Add spending_flow config to folk.yaml with validation  <!-- 非 TDD 任务 -->
  - [x] 3.1.1 执行变更：在 `config/folk.yaml` 中新增 `spending_flow` 配置节（含 tech/brand/maintenance 的 total_ratio 和 groups 分配）；在 `entity/folk.py` 的 `load_folks()` 中新增校验逻辑，验证每种支出类型的 groups 比例之和为 1.0（容差 0.01）
  - [x] 3.1.2 验证无回归（运行：`python -m pytest tests/test_folk.py tests/test_config.py -q`，确认测试通过）
  - [x] 3.1.3 检查：确认 spending_flow 配置格式正确，校验逻辑覆盖所有支出类型

- [x] 3.2 Implement maintenance cost deduction and spending distribution in act_phase  <!-- TDD 任务 -->
  - [x] 3.2.1 写失败测试：`tests/test_spending_flow.py` — 测试企业 tech 支出按 total_ratio 和 groups 比例分配到各 Folk 组；测试企业 brand 支出按比例分配；测试维护费用从企业现金扣除并按比例分配到 Folk 组；测试 total_ratio=0 时不分流
  - [x] 3.2.2 验证测试失败（运行：`python -m pytest tests/test_spending_flow.py -q`，确认因缺少实现而失败）
  - [x] 3.2.3 写最小实现：`system/decision_service.py` — 在 `act_phase()` 中：品牌投入后按配置比例分流到 Folk 组的 LedgerComponent.cash；科技投入后同理；新增维护费用实际扣款并分流；修改 `act_phase()` 签名接收 folks 参数；更新 `game/game.py` 的 `act_phase()` 调用
  - [x] 3.2.4 验证测试通过（运行：`python -m pytest tests/test_spending_flow.py -q`，确认所有测试通过，输出干净）
  - [x] 3.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射（以 OpenSpec 路径为准）：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/resident-decision-spending-flow/specs/*.md` 和 `openspec/changes/resident-decision-spending-flow/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA（或分支基点）
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入；用户选择"处理"类操作后，调用 superpowers:receiving-code-review 对每条审查意见做技术验证后再实施
  - 若仅有 Minor 或无问题：自动继续下一任务组，无需等待用户确认

## 4. FolkService refactoring to use decision components

- [x] 4.1 Refactor FolkService to use FolkDecisionComponent.decide_spending()  <!-- TDD 任务 -->
  - [x] 4.1.1 写失败测试：`tests/test_folk_service_decision.py` — 测试 FolkService.buy_phase() 调用 Folk 的决策组件获取支出计划；测试购买同时受 demand 和 budget 约束（取 min）；测试 Folk 实体创建时自动附加 ClassicFolkDecisionComponent
  - [x] 4.1.2 验证测试失败（运行：`python -m pytest tests/test_folk_service_decision.py -q`，确认因缺少实现而失败）
  - [x] 4.1.3 写最小实现：修改 `entity/folk.py` 的 Folk.__init__() 附加 ClassicFolkDecisionComponent；修改 `system/folk_service.py` 的 buy_phase() 通过决策组件获取支出计划，购买时取 min(demand, budget允许量)；修改 compute_demands() 委托到决策组件或保留为兼容方法
  - [x] 4.1.4 验证测试通过（运行：`python -m pytest tests/test_folk_service_decision.py tests/test_folk_service.py -q`，确认所有测试通过，输出干净）
  - [x] 4.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 4.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射（以 OpenSpec 路径为准）：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/resident-decision-spending-flow/specs/*.md` 和 `openspec/changes/resident-decision-spending-flow/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA（或分支基点）
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入；用户选择"处理"类操作后，调用 superpowers:receiving-code-review 对每条审查意见做技术验证后再实施
  - 若仅有 Minor 或无问题：自动继续下一任务组，无需等待用户确认

## 5. PreCI 代码规范检查

- [x] 5.1 检测 preci 安装状态（skip_preci: true，跳过）
- [x] 5.2 检测项目是否已 preci 初始化（跳过）
- [x] 5.3 检测 PreCI Server 状态（跳过）
- [x] 5.4 执行代码规范扫描（跳过）
- [x] 5.5 处理扫描结果（跳过）

## 6. Documentation Sync (Required)

- [x] 6.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 6.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 6.3 sync proposal.md: update scope/impact if changed
- [x] 6.4 sync specs/*.md: update requirements if changed
- [x] 6.5 Final review: ensure all OpenSpec docs reflect actual implementation
