## 1. 破产标记（LedgerComponent 扩展）

- [x] 1.1 在 LedgerComponent 中增加破产标记字段和检测逻辑  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_ledger_bankruptcy.py` — 测试 settle_all() 在有未全额结算账单时设置 `is_bankrupt = True`；所有账单正常结算时 `is_bankrupt = False`
  - [x] 1.1.2 验证测试失败（运行：`PYTHONPATH=. pytest tests/test_ledger_bankruptcy.py -x`，确认失败原因是缺少 `is_bankrupt` 属性或逻辑）
  - [x] 1.1.3 写最小实现：`component/ledger_component.py` — 在 `__init__` 中添加 `self.is_bankrupt: bool = False`，在 `settle_all()` 结尾检查是否存在 `total_paid < total_due` 的账单并设置标记
  - [x] 1.1.4 验证测试通过（运行：`PYTHONPATH=. pytest tests/test_ledger_bankruptcy.py -x`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/bankruptcy-and-market-replenishment/specs/*.md` 和 `openspec/changes/bankruptcy-and-market-replenishment/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. 破产清算服务（BankruptcyService）

- [x] 2.1 实现 BankruptcyService.process_bankruptcies() — 清算资产计算与优先级偿还  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_bankruptcy_service.py` — 测试破产公司的清算所得计算（工厂 build_cost × 50% + 现金）、库存清空、按优先级偿还（工资→应付账款→银行贷款）、坏账核销、公司销毁
  - [x] 2.1.2 验证测试失败（运行：`PYTHONPATH=. pytest tests/test_bankruptcy_service.py -x`，确认失败原因是缺少 BankruptcyService）
  - [x] 2.1.3 写最小实现：`system/bankruptcy_service.py` — 实现 `process_bankruptcies()` 方法：遍历所有 `is_bankrupt=True` 的 LedgerComponent 对应公司，计算清算所得，按优先级偿还，坏账核销（调用 `LedgerComponent.write_off()`），最后 `Entity.destroy()`
  - [x] 2.1.4 验证测试通过（运行：`PYTHONPATH=. pytest tests/test_bankruptcy_service.py -x`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 3. 市场补充机制

- [x] 3.1 实现 BankruptcyService.replenish_market() — 检查存活生产者并创建新公司  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_bankruptcy_service.py`（追加）— 测试某商品生产者数量低于阈值时创建新公司（验证新公司有基础工厂、启动资金、随机 CEO 特质、无品牌/科技），高于阈值时不创建
  - [x] 3.1.2 验证测试失败（运行：`PYTHONPATH=. pytest tests/test_bankruptcy_service.py -x -k replenish`，确认失败原因是缺少 `replenish_market` 方法）
  - [x] 3.1.3 写最小实现：`system/bankruptcy_service.py` — 实现 `replenish_market()` 方法：遍历所有 GoodsType，统计每种商品的存活生产者数量，低于阈值时通过 CompanyService.create_company() 创建新公司
  - [x] 3.1.4 验证测试通过（运行：`PYTHONPATH=. pytest tests/test_bankruptcy_service.py -x -k replenish`，确认所有测试通过，输出干净）
  - [x] 3.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.2 添加破产清算和市场补充相关配置  <!-- 非 TDD 任务 -->
  - [x] 3.2.1 执行变更：`config/game.yaml` — 添加 `bankruptcy` 配置节：`liquidation_factory_rate: 0.5`（工厂折价率）、`min_producers_per_goods: 2`（最低生产者阈值）、`new_company_initial_cash: 100000`（新公司启动资金）
  - [x] 3.2.2 验证无回归（运行：`PYTHONPATH=. pytest -x`，确认输出干净）
  - [x] 3.2.3 检查：确认变更范围完整，无遗漏文件或引用

- [x] 3.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 4. Game 集成

- [x] 4.1 在 Game.settlement_phase() 中集成 BankruptcyService  <!-- TDD 任务 -->
  - [x] 4.1.1 写失败测试：`tests/test_game_bankruptcy.py` — 测试 settlement_phase 执行后：破产公司被清算销毁、债权方收到偿还或坏账、市场补充创建新公司
  - [x] 4.1.2 验证测试失败（运行：`PYTHONPATH=. pytest tests/test_game_bankruptcy.py -x`，确认失败原因是缺少集成逻辑）
  - [x] 4.1.3 写最小实现：`game/game.py` — 在 `__init__` 中创建 BankruptcyService 实例，在 `settlement_phase()` 中先调用 `ledger_service.settle_all()`，再调用 `bankruptcy_service.process_bankruptcies()`，最后调用 `bankruptcy_service.replenish_market()`
  - [x] 4.1.4 验证测试通过（运行：`PYTHONPATH=. pytest tests/test_game_bankruptcy.py -x`，确认所有测试通过，输出干净）
  - [x] 4.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 4.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 5. PreCI 代码规范检查

- [x] 5.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：执行安装命令，安装完成后继续
  - 若找到：记录可用路径，直接继续
- [x] 5.2 检测项目是否已 preci 初始化
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`，等待完成后继续
- [x] 5.3 检测 PreCI Server 状态
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`，等待服务启动（最多 10 秒）
  - 若启动失败：输出警告但继续扫描流程
- [x] 5.4 执行代码规范扫描
  - 依次执行两个扫描命令：
    1. `<preci路径> scan --diff`（扫描未暂存变更）
    2. `<preci路径> scan --pre-commit`（扫描已暂存变更）
  - 合并两次扫描结果，去重后统一处理
  - 仅扫描代码文件（跳过 .md/.yml/.json/.xml/.txt/.png/.jpg 等非代码文件）
- [x] 5.5 处理扫描结果
  - 若无告警：输出 `✅ PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多 3 次重试），修正后重新扫描验证

## 6. Documentation Sync (Required)

- [x] 6.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 6.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 6.3 sync proposal.md: update scope/impact if changed
- [x] 6.4 sync specs/*.md: update requirements if changed
- [x] 6.5 Final review: ensure all OpenSpec docs reflect actual implementation
