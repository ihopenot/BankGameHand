## 1. 游戏配置与初始化

- [x] 1.1 新增 `config/game.yaml` 游戏初始化配置  <!-- 非 TDD 任务 -->
  - [x] 1.1.1 执行变更：`config/game.yaml`（定义每种工厂类型的公司数量、初始资金、总回合数等）
  - [x] 1.1.2 验证无回归（运行：`pytest tests/ -x`，确认输出干净）
  - [x] 1.1.3 检查：确认配置结构能被 ConfigManager 正确加载

- [x] 1.2 实现 Game.__init__ 完整初始化逻辑  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_game_init.py`（验证 Game 初始化后 companies、folks、services 正确创建）
  - [x] 1.2.2 验证测试失败（运行：`pytest tests/test_game_init.py -x`，确认失败原因是缺少功能）
  - [x] 1.2.3 写最小实现：`game/game.py`（加载配置→创建 GoodsType/Recipe/FactoryType→创建公司→创建居民→初始化 services）
  - [x] 1.2.4 验证测试通过（运行：`pytest tests/test_game_init.py -x`，确认所有测试通过，输出干净）
  - [x] 1.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/game-loop-init/specs/*.md` 和 `openspec/changes/game-loop-init/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `config/game.yaml`、`game/game.py`、`tests/test_game_init.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 2. ProductorService 补全与 game_loop 接通

- [x] 2.1 ProductorService.update_phase 补充工厂建造推进逻辑  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_productor_service_update.py`（验证 update_phase 推进工厂建造进度）
  - [x] 2.1.2 验证测试失败（运行：`pytest tests/test_productor_service_update.py -x`，确认失败原因是缺少功能）
  - [x] 2.1.3 写最小实现：`system/productor_service.py`（在 update_phase 中遍历所有 ProductorComponent 的工厂调用 tick_build）
  - [x] 2.1.4 验证测试通过（运行：`pytest tests/test_productor_service_update.py -x`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码（保持所有测试通过）

- [x] 2.2 完善 Game.game_loop 各阶段调用  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_game_loop.py`（验证 game_loop 能完整运行若干回合无异常，各阶段按正确顺序调用）
  - [x] 2.2.2 验证测试失败（运行：`pytest tests/test_game_loop.py -x`，确认失败原因是缺少功能）
  - [x] 2.2.3 写最小实现：`game/game.py`（完善 update_phase、sell_phase、buy_phase、product_phase、settlement_phase、跳过 plan_phase/player_act/act_phase）
  - [x] 2.2.4 验证测试通过（运行：`pytest tests/test_game_loop.py -x`，确认所有测试通过，输出干净）
  - [x] 2.2.5 重构：整理代码（保持所有测试通过）

- [x] 2.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/game-loop-init/specs/*.md` 和 `openspec/changes/game-loop-init/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/productor_service.py`、`game/game.py`、`tests/test_productor_service_update.py`、`tests/test_game_loop.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 3. 入口脚本

- [x] 3.1 新增 `main.py` 入口脚本  <!-- 非 TDD 任务 -->
  - [x] 3.1.1 执行变更：`main.py`（实例化 Game 并调用 game_loop，添加基础日志输出）
  - [x] 3.1.2 验证无回归（运行：`python main.py`，确认游戏能自动运行完整循环无异常）
  - [x] 3.1.3 检查：确认入口脚本正确导入、初始化、运行

- [x] 3.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/game-loop-init/specs/*.md` 和 `openspec/changes/game-loop-init/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `main.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 4. PreCI 代码规范检查

- [x] 4.1 检测 preci 安装状态
- [x] 4.2 检测项目是否已 preci 初始化
- [x] 4.3 检测 PreCI Server 状态
- [x] 4.4 执行代码规范扫描
- [x] 4.5 处理扫描结果

## 5. Documentation Sync (Required)

- [x] 5.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 5.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`
- [x] 5.3 sync proposal.md: update scope/impact if changed
- [x] 5.4 sync specs/*.md: update requirements if changed
- [x] 5.5 Final review: ensure all OpenSpec docs reflect actual implementation
