## 1. 创建 BaseCompanyDecisionComponent 抽象基类

- [x] 1.1 创建抽象基类，定义 CEO 特质属性和 5 个决策 API  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_base_company_decision.py` — 测试基类不能直接实例化，测试子类必须实现所有抽象方法
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_base_company_decision.py -v`，确认失败原因是缺少模块）
  - [x] 1.1.3 写最小实现：`component/base_company_decision.py` — 含 CEO 特质、investment_plan、set_context、5 个 abstractmethod
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_base_company_decision.py -v`，确认所有测试通过）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/company-decision-refactor/specs/*.md` 和 `openspec/changes/company-decision-refactor/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. 迁移 ClassicCompanyDecisionComponent

- [x] 2.1 创建 ClassicCompanyDecisionComponent，迁移定价决策逻辑  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_classic_company_decision.py` — 测试 set_context + decide_pricing 返回正确结果
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_classic_company_decision.py -v`，确认失败原因是缺少模块）
  - [x] 2.1.3 写最小实现：`component/classic_company_decision.py` — 实现 set_context 和 decide_pricing
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_classic_company_decision.py -v`，确认所有测试通过）
  - [x] 2.1.5 重构：整理代码（保持所有测试通过）

- [x] 2.2 迁移投资计划决策逻辑  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_classic_company_decision.py` — 测试 decide_investment_plan 返回正确结构和计算
  - [x] 2.2.2 验证测试失败（运行：`python -m pytest tests/test_classic_company_decision.py -v`，确认新测试失败）
  - [x] 2.2.3 写最小实现：`component/classic_company_decision.py` — 实现 decide_investment_plan（含 _plan_expansion, _plan_brand, _plan_tech）
  - [x] 2.2.4 验证测试通过（运行：`python -m pytest tests/test_classic_company_decision.py -v`，确认所有测试通过）
  - [x] 2.2.5 重构：整理代码（保持所有测试通过）

- [x] 2.3 迁移预算分配、采购排序、贷款需求决策逻辑  <!-- TDD 任务 -->
  - [x] 2.3.1 写失败测试：`tests/test_classic_company_decision.py` — 测试 decide_budget_allocation, make_purchase_sort_key, decide_loan_needs
  - [x] 2.3.2 验证测试失败（运行：`python -m pytest tests/test_classic_company_decision.py -v`，确认新测试失败）
  - [x] 2.3.3 写最小实现：`component/classic_company_decision.py` — 实现剩余 3 个决策方法
  - [x] 2.3.4 验证测试通过（运行：`python -m pytest tests/test_classic_company_decision.py -v`，确认所有测试通过）
  - [x] 2.3.5 重构：整理代码（保持所有测试通过）

- [x] 2.4 代码审查
  - （同 1.2 审查格式）

## 3. 重构 DecisionService 为编排层

- [x] 3.1 重写 DecisionService，委托决策到组件  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_decision_service_refactored.py` — 测试 DecisionService 调用组件的 set_context + 各决策方法
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_decision_service_refactored.py -v`，确认失败）
  - [x] 3.1.3 写最小实现：`system/decision_service.py` — 重写为编排层（_build_context + 委托调用）
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_decision_service_refactored.py -v`，确认所有测试通过）
  - [x] 3.1.5 重构：整理代码（保持所有测试通过）

- [x] 3.2 代码审查
  - （同 1.2 审查格式）

## 4. 更新 Company 实体和引用迁移

- [x] 4.1 更新 Company 实体，替换 DecisionComponent 为新组件  <!-- 非 TDD 任务 -->
  - [x] 4.1.1 执行变更：`entity/company/company.py` — 替换 `init_component(DecisionComponent)` 为 `init_component(ClassicCompanyDecisionComponent)`，增加 decision_type 参数支持
  - [x] 4.1.2 验证无回归（运行：`python -m pytest tests/ -v`，确认所有测试通过）
  - [x] 4.1.3 检查：确认 company.py 中无残留 DecisionComponent 引用

- [x] 4.2 迁移所有 DecisionComponent 引用  <!-- 非 TDD 任务 -->
  - [x] 4.2.1 执行变更：`system/decision_service.py`, `system/company_service.py`, `game/game.py` 及所有引用 DecisionComponent 的文件 — 全部迁移到 BaseCompanyDecisionComponent
  - [x] 4.2.2 验证无回归（运行：`python -m pytest tests/ -v`，确认所有测试通过）
  - [x] 4.2.3 检查：`grep -r "DecisionComponent" --include="*.py"` 确认无残留旧引用（除测试外）

- [x] 4.3 删除旧 DecisionComponent 文件  <!-- 非 TDD 任务 -->
  - [x] 4.3.1 执行变更：删除 `component/decision_component.py`
  - [x] 4.3.2 验证无回归（运行：`python -m pytest tests/ -v`，确认所有测试通过）
  - [x] 4.3.3 检查：确认无 import 指向已删除文件

- [x] 4.4 更新现有测试文件  <!-- 非 TDD 任务 -->
  - [x] 4.4.1 执行变更：`tests/test_decision_component.py`, `tests/test_decision_service.py` 及其他引用旧组件的测试 — 迁移到新组件
  - [x] 4.4.2 验证无回归（运行：`python -m pytest tests/ -v`，确认所有测试通过）
  - [x] 4.4.3 检查：确认所有测试使用新组件类名

- [x] 4.5 代码审查
  - （同 1.2 审查格式）

## 5. 实现 AICompanyDecisionComponent

- [x] 5.1 实现 AI 决策组件核心逻辑  <!-- TDD 任务 -->
  - [x] 5.1.1 写失败测试：`tests/test_ai_company_decision.py` — 测试 set_context 调用 MCPAgentSDK（mock），验证 validate_fn 逻辑，测试缓存读取
  - [x] 5.1.2 验证测试失败（运行：`python -m pytest tests/test_ai_company_decision.py -v`，确认失败）
  - [x] 5.1.3 写最小实现：`component/ai_company_decision.py` — 实现 set_context（asyncio.run + MCPAgentSDK）、validate_fn、3 个覆写决策方法
  - [x] 5.1.4 验证测试通过（运行：`python -m pytest tests/test_ai_company_decision.py -v`，确认所有测试通过）
  - [x] 5.1.5 重构：整理代码（保持所有测试通过）

- [x] 5.2 实现 AI prompt 模板和 JSON schema 验证  <!-- TDD 任务 -->
  - [x] 5.2.1 写失败测试：`tests/test_ai_company_decision.py` — 测试 prompt 包含完整 context、测试各类非法 JSON 被 validate_fn 拒绝
  - [x] 5.2.2 验证测试失败（运行：`python -m pytest tests/test_ai_company_decision.py -v`，确认新测试失败）
  - [x] 5.2.3 写最小实现：`component/ai_company_decision.py` — 完善 prompt 模板和 validate_fn 边界检查
  - [x] 5.2.4 验证测试通过（运行：`python -m pytest tests/test_ai_company_decision.py -v`，确认所有测试通过）
  - [x] 5.2.5 重构：整理代码（保持所有测试通过）

- [x] 5.3 代码审查
  - （同 1.2 审查格式）

## 6. Game 集成与市场数据传递

- [x] 6.1 更新 Game 向 DecisionService 传递市场数据  <!-- TDD 任务 -->
  - [x] 6.1.1 写失败测试：`tests/test_game_decision_integration.py` — 测试 game loop 中 DecisionService 收到正确的市场数据
  - [x] 6.1.2 验证测试失败（运行：`python -m pytest tests/test_game_decision_integration.py -v`，确认失败）
  - [x] 6.1.3 写最小实现：`game/game.py` — 在 plan_phase 和相关阶段传递市场 sell_orders 和 trades 给 DecisionService
  - [x] 6.1.4 验证测试通过（运行：`python -m pytest tests/test_game_decision_integration.py -v`，确认所有测试通过）
  - [x] 6.1.5 重构：整理代码（保持所有测试通过）

- [x] 6.2 全量集成测试验证  <!-- 非 TDD 任务 -->
  - [x] 6.2.1 执行变更：运行完整测试套件 `python -m pytest tests/ -v`
  - [x] 6.2.2 验证无回归（确认 450+ 测试通过，无新增失败）
  - [x] 6.2.3 检查：确认游戏循环端到端流程完整

- [x] 6.3 代码审查
  - （同 1.2 审查格式）

## 7. PreCI 代码规范检查

- [x] 7.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：跳过（skip_preci: true）
  - 若找到：记录可用路径，直接继续
- [x] 7.2 检测项目是否已 preci 初始化
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`
- [x] 7.3 检测 PreCI Server 状态
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`
- [x] 7.4 执行代码规范扫描
  - 依次执行 `<preci路径> scan --diff` 和 `<preci路径> scan --pre-commit`
  - 合并两次扫描结果，去重后统一处理
- [x] 7.5 处理扫描结果
  - 若无告警：输出 `PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多 3 次），修正后重新扫描验证

## 8. Documentation Sync (Required)

- [x] 8.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 8.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`
- [x] 8.3 sync proposal.md: update scope/impact if changed
- [x] 8.4 sync specs/*.md: update requirements if changed
- [x] 8.5 Final review: ensure all OpenSpec docs reflect actual implementation
