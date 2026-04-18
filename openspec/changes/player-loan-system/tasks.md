## 1. Bank 实体与 BankService 基础设施

- [x] 1.1 创建 Bank 实体类  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_bank.py` — 测试 Bank 实体创建、包含 LedgerComponent、初始现金设置
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_bank.py -v`，确认失败原因是缺少 Bank 类）
  - [x] 1.1.3 写最小实现：`entity/bank.py` — Bank 继承 Entity，初始化 LedgerComponent
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_bank.py -v`，确认所有测试通过）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 创建 BankService 服务类  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_bank_service.py` — 测试 BankService 创建银行、追踪银行列表、从配置加载银行
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_bank_service.py -v`，确认失败原因是缺少 BankService 类）
  - [x] 1.2.3 写最小实现：`system/bank_service.py` — BankService 继承 Service，管理银行实体列表，提供 create_bank() 方法
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_bank_service.py -v`，确认所有测试通过）
  - [x] 1.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.3 新增 game.yaml 银行配置  <!-- 非 TDD 任务 -->
  - [x] 1.3.1 执行变更：`config/game.yaml` — 新增 banks 配置段（银行名称、初始资金）
  - [x] 1.3.2 验证无回归（运行：`python -m pytest tests/ -v`，确认所有测试通过）
  - [x] 1.3.3 检查：确认配置格式与现有 companies 配置风格一致

- [x] 1.4 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/player-loan-system/specs/*.md` 和 `openspec/changes/player-loan-system/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. LoanApplication 数据类型与贷款申请收集

- [x] 2.1 定义 LoanApplication 数据类型  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_loan_application.py` — 测试 LoanApplication 创建（申请企业、申请金额）
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_loan_application.py -v`，确认失败原因是缺少 LoanApplication）
  - [x] 2.1.3 写最小实现：`core/types.py` — 新增 LoanApplication dataclass
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_loan_application.py -v`，确认所有测试通过）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 实现 BankService 贷款申请收集功能  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_bank_service.py` — 测试 collect_applications()、clear_applications()、get_applications()
  - [x] 2.2.2 验证测试失败（运行：`python -m pytest tests/test_bank_service.py -v`，确认失败原因是缺少方法）
  - [x] 2.2.3 写最小实现：`system/bank_service.py` — 新增贷款申请收集、清理、查询方法
  - [x] 2.2.4 验证测试通过（运行：`python -m pytest tests/test_bank_service.py -v`，确认所有测试通过）
  - [x] 2.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续

## 3. Plan 阶段增强 — 企业贷款需求计算

- [x] 3.1 在 DecisionService 中计算贷款需求并生成申请  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_decision_service.py` — 测试 plan_phase 后企业生成 LoanApplication（计划总额 > 可用预算时），不生成申请（可用预算充足时）
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py -v`，确认失败原因是缺少贷款需求计算逻辑）
  - [x] 3.1.3 写最小实现：`system/decision_service.py` — plan_phase 结束后计算 loan_need = max(0, plan_total - available_budget)，有需求时创建 LoanApplication
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py -v`，确认所有测试通过）
  - [x] 3.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.2 代码审查

## 4. 贷款审批与接受流程

- [x] 4.1 实现 BankService 贷款报价存储与接受匹配逻辑  <!-- TDD 任务 -->
  - [x] 4.1.1 写失败测试：`tests/test_bank_service.py` — 测试 add_offer()、accept_loans()（按利率排序、部分接受、现金转移）
  - [x] 4.1.2 验证测试失败（运行：`python -m pytest tests/test_bank_service.py -v`，确认失败原因是缺少方法）
  - [x] 4.1.3 写最小实现：`system/bank_service.py` — 新增 LoanOffer 数据类型、add_offer()、accept_loans() 方法（按利率排序接受，部分接受最后一笔，调用 issue_loan 创建贷款）
  - [x] 4.1.4 验证测试通过（运行：`python -m pytest tests/test_bank_service.py -v`，确认所有测试通过）
  - [x] 4.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 4.2 代码审查

## 5. 终端界面增强

- [x] 5.1 企业表格新增商品定价列  <!-- TDD 任务 -->
  - [x] 5.1.1 写失败测试：`tests/test_player_service.py` — 测试 format_company_table 输出包含每种商品的挂牌价格
  - [x] 5.1.2 验证测试失败（运行：`python -m pytest tests/test_player_service.py -v`，确认失败原因是缺少定价列）
  - [x] 5.1.3 写最小实现：`system/player_service.py` — format_company_table 增加定价列
  - [x] 5.1.4 验证测试通过（运行：`python -m pytest tests/test_player_service.py -v`，确认所有测试通过）
  - [x] 5.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 5.2 新增银行摘要、活跃贷款、贷款申请展示  <!-- TDD 任务 -->
  - [x] 5.2.1 写失败测试：`tests/test_player_service.py` — 测试 format_bank_summary、format_active_loans、format_loan_applications 输出格式
  - [x] 5.2.2 验证测试失败（运行：`python -m pytest tests/test_player_service.py -v`，确认失败原因是缺少格式化方法）
  - [x] 5.2.3 写最小实现：`system/player_service.py` — 新增三个格式化方法：银行摘要（名称/现金/贷款总额/利息收入）、活跃贷款表（借款方/贷款方/剩余本金/利率/剩余期限）、贷款申请列表（申请企业/申请金额）
  - [x] 5.2.4 验证测试通过（运行：`python -m pytest tests/test_player_service.py -v`，确认所有测试通过）
  - [x] 5.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 5.3 代码审查

## 6. PlayerAct 阶段增强 — 玩家贷款审批交互

- [x] 6.1 实现玩家贷款审批输入流程  <!-- TDD 任务 -->
  - [x] 6.1.1 写失败测试：`tests/test_player_service.py` — 测试 player_act_phase 展示贷款申请并接收玩家审批输入（利率、金额、还款方式、期限、跳过），校验批准总额不超过银行现金
  - [x] 6.1.2 验证测试失败（运行：`python -m pytest tests/test_player_service.py -v`，确认失败原因是缺少审批交互逻辑）
  - [x] 6.1.3 写最小实现：`system/player_service.py` — player_act_phase 增加贷款审批交互：展示信息 → 逐条审批 → 校验约束
  - [x] 6.1.4 验证测试通过（运行：`python -m pytest tests/test_player_service.py -v`，确认所有测试通过）
  - [x] 6.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 6.2 代码审查

## 7. 游戏循环集成

- [x] 7.1 集成 BankService 到 Game 初始化和游戏循环  <!-- TDD 任务 -->
  - [x] 7.1.1 写失败测试：`tests/test_game.py` — 测试 Game 初始化包含 BankService 和银行实体；游戏循环按 10 阶段顺序执行（含贷款申请、贷款接受阶段）
  - [x] 7.1.2 验证测试失败（运行：`python -m pytest tests/test_game.py -v`，确认失败原因是缺少 BankService 集成）
  - [x] 7.1.3 写最小实现：`game/game.py` — 初始化 BankService 并创建银行；游戏循环新增 loan_application_phase 和 loan_acceptance_phase 调用
  - [x] 7.1.4 验证测试通过（运行：`python -m pytest tests/test_game.py -v`，确认所有测试通过）
  - [x] 7.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 7.2 代码审查

## 8. PreCI 代码规范检查

- [x] 8.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：执行安装命令，安装完成后继续
  - 若找到：记录可用路径，直接继续
- [x] 8.2 检测项目是否已 preci 初始化
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`，等待完成后继续
- [x] 8.3 检测 PreCI Server 状态
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`，等待服务启动（最多 10 秒）
  - 若启动失败：输出警告但继续扫描流程
- [x] 8.4 执行代码规范扫描
  - 依次执行两个扫描命令：
    1. `<preci路径> scan --diff`（扫描未暂存变更）
    2. `<preci路径> scan --pre-commit`（扫描已暂存变更）
  - 合并两次扫描结果，去重后统一处理
  - 仅扫描代码文件
- [x] 8.5 处理扫描结果
  - 若无告警：输出 `✅ PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多 3 次），修正后重新扫描验证

## 9. Documentation Sync (Required)

- [x] 9.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 9.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 9.3 sync proposal.md: update scope/impact if changed
- [x] 9.4 sync specs/*.md: update requirements if changed
- [x] 9.5 Final review: ensure all OpenSpec docs reflect actual implementation
