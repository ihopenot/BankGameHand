## 1. AICompanyDecisionComponent Session 池与两阶段调用

- [x] 1.1 新增 session 池、prepare_session、prepare_next_sessions、cleanup_sessions 方法  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_ai_session_prepare.py` — 测试 prepare_session 创建并存入 session、prepare_next_sessions 批量 prepare、cleanup_sessions 关闭所有 session
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_ai_session_prepare.py -x -q`，确认失败原因是缺少功能）
  - [x] 1.1.3 写最小实现：`component/ai_company_decision.py` — 新增 `_sessions: Dict[str, AgentSession]` 类属性、`prepare_session`、`prepare_next_sessions`、`cleanup_sessions` 方法
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_ai_session_prepare.py -x -q`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 重构 _call_ai 为 _query_ai，使用 do_query 并保留 run_agent 回退  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_ai_session_prepare.py` — 测试 _query_ai 从 session 池取 session 调用 do_query、session 不存在时回退 run_agent、do_query 后 session 从池中移除
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_ai_session_prepare.py -x -q`，确认失败原因是缺少功能）
  - [x] 1.2.3 写最小实现：`component/ai_company_decision.py` — 将 `_call_ai` 重命名为 `_query_ai`，优先使用 prepared session + do_query，无 session 时回退 run_agent；更新 set_context 调用
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_ai_session_prepare.py -x -q`，确认所有测试通过，输出干净）
  - [x] 1.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射（以 OpenSpec 路径为准）：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/ai-session-prepare/specs/*.md` 和 `openspec/changes/ai-session-prepare/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA（或分支基点）
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入；用户选择"处理"类操作后，调用 superpowers:receiving-code-review 对每条审查意见做技术验证后再实施
  - 若仅有 Minor 或无问题：自动继续下一任务组，无需等待用户确认

## 2. DecisionService 并行化与 prepare_next_round

- [x] 2.1 新增 prepare_next_round 方法，修改 plan_phase 为并行调用  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_decision_service_parallel.py` — 测试 prepare_next_round 为所有 AI 公司 prepare session、plan_phase 并行调用所有 AI 决策、plan_phase 完成后自动 prepare 下一轮
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_decision_service_parallel.py -x -q`，确认失败原因是缺少功能）
  - [x] 2.1.3 写最小实现：`system/decision_service.py` — 新增 `prepare_next_round(companies)` 方法；修改 `plan_phase` 使用 asyncio.gather 并行调用 AI 决策，完成后调用 prepare_next_round
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_decision_service_parallel.py -x -q`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射（以 OpenSpec 路径为准）：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/ai-session-prepare/specs/*.md` 和 `openspec/changes/ai-session-prepare/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA（或分支基点）
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入；用户选择"处理"类操作后，调用 superpowers:receiving-code-review 对每条审查意见做技术验证后再实施
  - 若仅有 Minor 或无问题：自动继续下一任务组，无需等待用户确认

## 3. Game 循环集成

- [x] 3.1 在 game.py 中集成首次预热和游戏结束清理  <!-- 非 TDD 任务 -->
  - [x] 3.1.1 执行变更：`game/game.py` — 在 game_loop 开始前调用 decision_service.prepare_next_round(companies)；在 game_loop 结束后调用 AICompanyDecisionComponent.cleanup_sessions() 和 SDK shutdown
  - [x] 3.1.2 验证无回归（运行：`python -m pytest -x -q`，确认输出干净）
  - [x] 3.1.3 检查：确认变更范围完整，无遗漏文件或引用

- [x] 3.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射（以 OpenSpec 路径为准）：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/ai-session-prepare/specs/*.md` 和 `openspec/changes/ai-session-prepare/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA（或分支基点）
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入；用户选择"处理"类操作后，调用 superpowers:receiving-code-review 对每条审查意见做技术验证后再实施
  - 若仅有 Minor 或无问题：自动继续下一任务组，无需等待用户确认

## 4. PreCI 代码规范检查

- [x] 4.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：执行本技能 "PreCI 代码规范检查规范" 节中的安装命令，安装完成后继续
  - 若找到：记录可用路径，直接继续
- [x] 4.2 检测项目是否已 preci 初始化
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`，等待完成后继续
- [x] 4.3 检测 PreCI Server 状态
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`，等待服务启动（最多 10 秒）
  - 若启动失败：输出警告但继续扫描流程
- [x] 4.4 执行代码规范扫描
  - 依次执行两个扫描命令：
    1. `<preci路径> scan --diff`（扫描未暂存变更）
    2. `<preci路径> scan --pre-commit`（扫描已暂存变更）
  - 合并两次扫描结果，去重后统一处理
  - 仅扫描代码文件（跳过 .md/.yml/.json/.xml/.txt/.png/.jpg 等非代码文件）
- [x] 4.5 处理扫描结果
  - 若无告警：输出 `✅ PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多重试次数由配置 `max_auto_fix_rounds` 决定，默认 3 次），修正后重新扫描验证
  - **若重试用尽后仍有无法自动修正的告警且 `skip_preci: false`**：暂停流程，输出剩余问题列表及选项，等待用户确认

## 5. Documentation Sync (Required)

- [x] 5.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 5.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 5.3 sync proposal.md: update scope/impact if changed
- [x] 5.4 sync specs/*.md: update requirements if changed
- [x] 5.5 Final review: ensure all OpenSpec docs reflect actual implementation
