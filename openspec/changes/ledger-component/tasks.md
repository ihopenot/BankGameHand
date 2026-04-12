## 1. 类型定义（core/types.py）

- [x] 1.1 实现 LoanType 和 RepaymentType 枚举  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_types.py` — 测试 LoanType 和 RepaymentType 枚举值完整性
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_types.py -v`，确认失败原因是缺少枚举定义）
  - [x] 1.1.3 写最小实现：`core/types.py` — 添加 LoanType（CORPORATE_LOAN/DEPOSIT/INTERBANK/BOND）和 RepaymentType（EQUAL_PRINCIPAL/INTEREST_FIRST/BULLET）枚举，为 LoanType 定义结算优先级属性（DEPOSIT=0, INTERBANK=1, CORPORATE_LOAN=2, BOND=3）
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_types.py -v`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 实现 Loan 类和 LoanBill 类  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_types.py` — 测试 Loan 构造、LoanBill 构造、Loan.settle() 三种偿付类型的账单计算（等额本金、先息后本各期、到期本息各期）
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_types.py -v`，确认失败原因是缺少 Loan/LoanBill 实现）
  - [x] 1.2.3 写最小实现：`core/types.py` — 实现 Loan 类（creditor/debtor/principal/remaining/rate/term/elapsed/loan_type/repayment_type/accrued_interest 字段 + settle() 方法）和 LoanBill 类（loan/principal_due/interest_due/total_due/total_paid/accrued_delta 字段）
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_types.py -v`，确认所有测试通过，输出干净）
  - [x] 1.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/ledger-component/specs/*.md` 和 `openspec/changes/ledger-component/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `core/types.py`, `tests/test_types.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户指令
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. LedgerComponent 核心实现

- [x] 2.1 实现 LedgerComponent 基础结构与查询方法  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_ledger_component.py` — 重写测试文件，测试 LedgerComponent 初始化（cash=0, receivables=[], payables=[], bills=[]）、total_receivables()、total_payables()、net_financial_assets()、filter_loans()
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_ledger_component.py -v`，确认失败原因是缺少新接口）
  - [x] 2.1.3 写最小实现：`component/ledger_component.py` — 重写 LedgerComponent，实现状态字段和查询方法
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_ledger_component.py -v`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 实现 issue_loan 发放贷款  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_ledger_component.py` — 测试发放贷款后双方 cash 变化、receivables/payables 包含 Loan
  - [x] 2.2.2 验证测试失败（运行：`python -m pytest tests/test_ledger_component.py -v`，确认失败原因是缺少 issue_loan）
  - [x] 2.2.3 写最小实现：`component/ledger_component.py` — 实现 issue_loan()，双边同步操作
  - [x] 2.2.4 验证测试通过（运行：`python -m pytest tests/test_ledger_component.py -v`，确认所有测试通过，输出干净）
  - [x] 2.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.3 实现 generate_bills 账单生成  <!-- TDD 任务 -->
  - [x] 2.3.1 写失败测试：`tests/test_ledger_component.py` — 测试多笔 payables 生成账单、按优先级排序（DEPOSIT 在前）、活期存款（term=0）生成 total_due=0 的账单且利息累计到 accrued_interest、不修改 Loan 状态
  - [x] 2.3.2 验证测试失败（运行：`python -m pytest tests/test_ledger_component.py -v`，确认失败原因是缺少 generate_bills）
  - [x] 2.3.3 写最小实现：`component/ledger_component.py` — 实现 generate_bills()
  - [x] 2.3.4 验证测试通过（运行：`python -m pytest tests/test_ledger_component.py -v`，确认所有测试通过，输出干净）
  - [x] 2.3.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.4 实现 settle_all 结算支付  <!-- TDD 任务 -->
  - [x] 2.4.1 写失败测试：`tests/test_ledger_component.py` — 测试足额支付、不足额支付（优先偿还利息再本金）、结算优先级、到期 Loan 移除、BULLET 类型 accrued_interest 累加、活期存款账单 total_due=0 不产生现金划转
  - [x] 2.4.2 验证测试失败（运行：`python -m pytest tests/test_ledger_component.py -v`，确认失败原因是缺少 settle_all）
  - [x] 2.4.3 写最小实现：`component/ledger_component.py` — 实现 settle_all()
  - [x] 2.4.4 验证测试通过（运行：`python -m pytest tests/test_ledger_component.py -v`，确认所有测试通过，输出干净）
  - [x] 2.4.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.5 实现 withdraw 存款取款  <!-- TDD 任务 -->
  - [x] 2.5.1 写失败测试：`tests/test_ledger_component.py` — 测试足额取款含利息结算、受限于吸储方现金（优先支付利息）、取完后 Loan 移除
  - [x] 2.5.2 验证测试失败（运行：`python -m pytest tests/test_ledger_component.py -v`，确认失败原因是缺少 withdraw）
  - [x] 2.5.3 写最小实现：`component/ledger_component.py` — 实现 withdraw()
  - [x] 2.5.4 验证测试通过（运行：`python -m pytest tests/test_ledger_component.py -v`，确认所有测试通过，输出干净）
  - [x] 2.5.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.6 实现 unpaid_bills 和 write_off  <!-- TDD 任务 -->
  - [x] 2.6.1 写失败测试：`tests/test_ledger_component.py` — 测试 unpaid_bills 返回未付清账单、write_off 双边移除且不产生现金流
  - [x] 2.6.2 验证测试失败（运行：`python -m pytest tests/test_ledger_component.py -v`，确认失败原因是缺少 unpaid_bills/write_off）
  - [x] 2.6.3 写最小实现：`component/ledger_component.py` — 实现 unpaid_bills() 和 write_off()
  - [x] 2.6.4 验证测试通过（运行：`python -m pytest tests/test_ledger_component.py -v`，确认所有测试通过，输出干净）
  - [x] 2.6.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.7 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/ledger-component/specs/*.md` 和 `openspec/changes/ledger-component/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `component/ledger_component.py`, `tests/test_ledger_component.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户指令
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 3. PreCI 代码规范检查

- [x] 3.1 检测 preci 安装状态 (skipped: skip_preci=true)
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：跳过（skip_preci: true）
  - 若找到：记录可用路径，直接继续
- [x] 3.2 检测项目是否已 preci 初始化 (skipped)
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`，等待完成后继续
- [x] 3.3 检测 PreCI Server 状态 (skipped)
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`，等待服务启动（最多 10 秒）
  - 若启动失败：输出警告但继续扫描流程
- [x] 3.4 执行代码规范扫描 (skipped)
  - 依次执行两个扫描命令：
    1. `<preci路径> scan --diff`（扫描未暂存变更）
    2. `<preci路径> scan --pre-commit`（扫描已暂存变更）
  - 合并两次扫描结果，去重后统一处理
  - 仅扫描代码文件（跳过 .md/.yml/.json/.xml/.txt/.png/.jpg 等非代码文件）
- [x] 3.5 处理扫描结果 (skipped)
  - 若无告警：输出 `PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多 3 次），修正后重新扫描验证

## 4. Documentation Sync (Required)

- [x] 4.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 4.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 4.3 sync proposal.md: update scope/impact if changed
- [x] 4.4 sync specs/*.md: update requirements if changed
- [x] 4.5 Final review: ensure all OpenSpec docs reflect actual implementation
