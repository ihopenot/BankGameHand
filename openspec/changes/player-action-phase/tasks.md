## 1. 实现 PlayerService 核心逻辑

- [x] 1.1 实现经济数据展示功能  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_player_service.py` — 测试 `format_economy_summary()` 返回包含回合数和经济指数的格式化字符串
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_player_service.py -v`，确认失败原因是模块不存在）
  - [x] 1.1.3 写最小实现：`system/player_service.py` — 实现 `PlayerService` 类及 `format_economy_summary()` 方法
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_player_service.py -v`，确认所有测试通过）
  - [x] 1.1.5 重构：整理代码、改善命名（保持所有测试通过）

- [x] 1.2 实现公司财务概览展示功能  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_player_service.py` — 测试 `format_company_table()` 返回包含公司名、工厂类型、现金、库存、应收款、应付款的表格字符串
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_player_service.py -v`，确认失败原因是方法不存在）
  - [x] 1.2.3 写最小实现：`system/player_service.py` — 实现 `format_company_table()` 方法
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_player_service.py -v`，确认所有测试通过）
  - [x] 1.2.5 重构：整理代码（保持所有测试通过）

- [x] 1.3 实现玩家输入处理（跳过回合）  <!-- TDD 任务 -->
  - [x] 1.3.1 写失败测试：`tests/test_player_service.py` — 测试 `player_act_phase()` 在输入 `skip`/空字符串时正常返回，输入无效命令时提示重新输入
  - [x] 1.3.2 验证测试失败（运行：`python -m pytest tests/test_player_service.py -v`，确认失败原因是方法不存在）
  - [x] 1.3.3 写最小实现：`system/player_service.py` — 实现 `player_act_phase()` 方法，整合展示 + 输入循环
  - [x] 1.3.4 验证测试通过（运行：`python -m pytest tests/test_player_service.py -v`，确认所有测试通过）
  - [x] 1.3.5 重构：整理代码（保持所有测试通过）

- [x] 1.4 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/player-action-phase/specs/*.md` 和 `openspec/changes/player-action-phase/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/player_service.py`、`tests/test_player_service.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. 集成到游戏主循环

- [x] 2.1 修改 Game 类集成 PlayerService  <!-- 非 TDD 任务 -->
  - [x] 2.1.1 执行变更：`game/game.py` — 导入 PlayerService，在 `__init__` 中初始化，在 `player_act()` 中调用 `player_service.player_act_phase()`
  - [x] 2.1.2 验证无回归（运行：`python -m pytest tests/ -v`，确认所有 291+ 测试通过，输出干净）
  - [x] 2.1.3 检查：确认 `game/game.py` 的变更范围完整，PlayerService 正确接收所需依赖

- [x] 2.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试
  - 调用 superpowers:requesting-code-review 审查本任务组变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/player-action-phase/specs/*.md` 和 `openspec/changes/player-action-phase/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `game/game.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续

## 3. PreCI 代码规范检查

- [x] 3.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：提示安装或跳过
- [x] 3.2 检测项目是否已 preci 初始化
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
- [x] 3.3 检测 PreCI Server 状态
  - 执行 `<preci路径> server status` 检查服务是否启动
- [x] 3.4 执行代码规范扫描
  - 依次执行 `scan --diff` 和 `scan --pre-commit`
- [x] 3.5 处理扫描结果
  - 无告警则继续；有告警则自动修正（最多 3 次重试）

## 4. Documentation Sync (Required)

- [x] 4.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 4.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 4.3 sync proposal.md: update scope/impact if changed
- [x] 4.4 sync specs/*.md: update requirements if changed
- [x] 4.5 Final review: ensure all OpenSpec docs reflect actual implementation
