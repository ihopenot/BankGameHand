## ADDED Requirements

### Requirement: LoanType 和 RepaymentType 枚举

定义金融关系类型和偿付方式。

#### Scenario: 枚举值完整性
- **WHEN** 引用 LoanType
- **THEN** 可用值为 CORPORATE_LOAN、DEPOSIT、INTERBANK、BOND

#### Scenario: RepaymentType 完整性
- **WHEN** 引用 RepaymentType
- **THEN** 可用值为 EQUAL_PRINCIPAL、INTEREST_FIRST、BULLET

### Requirement: Loan 数据结构

统一表达所有双边金融关系。

#### Scenario: 创建企业贷款
- **WHEN** 创建 Loan(loan_type=CORPORATE_LOAN, principal=10000, rate=500, term=5, repayment_type=EQUAL_PRINCIPAL)
- **THEN** remaining=10000, elapsed=0, accrued_interest=0

#### Scenario: 等额本金结算
- **WHEN** 对 principal=10000, remaining=10000, rate=500, term=5 的 EQUAL_PRINCIPAL 贷款调用 settle()
- **THEN** LoanBill.principal_due=2000, interest_due=500, total_due=2500

#### Scenario: 先息后本非末期结算
- **WHEN** 对 remaining=10000, rate=500, term=5, elapsed=0 的 INTEREST_FIRST 贷款调用 settle()
- **THEN** principal_due=0, interest_due=500, total_due=500

#### Scenario: 先息后本末期结算
- **WHEN** 对 remaining=10000, rate=500, term=5, elapsed=4 的 INTEREST_FIRST 贷款调用 settle()
- **THEN** principal_due=10000, interest_due=500, total_due=10500

#### Scenario: 到期本息非末期结算
- **WHEN** 对 remaining=10000, rate=500, term=5, elapsed=0 的 BULLET 贷款调用 settle()
- **THEN** principal_due=0, interest_due=0, total_due=0（利息累计到 accrued_interest）

#### Scenario: 到期本息末期结算
- **WHEN** 对 remaining=10000, rate=500, term=5, elapsed=4, accrued_interest=2000 的 BULLET 贷款调用 settle()
- **THEN** principal_due=10000, interest_due=2500, total_due=12500

### Requirement: LoanBill 结算账单

#### Scenario: 账单初始状态
- **WHEN** Loan.settle() 生成 LoanBill
- **THEN** total_paid=0，total_due=principal_due+interest_due

#### Scenario: BULLET 非末期账单记录累计利息增量
- **WHEN** 对 remaining=10000, rate=500 的 BULLET 贷款生成非末期账单
- **THEN** LoanBill.accrued_delta=500（本期累计利息增量），total_due=0

#### Scenario: 活期存款账单记录累计利息增量
- **WHEN** 对 term=0, remaining=10000, rate=500 的活期存款生成账单
- **THEN** LoanBill.accrued_delta=500，total_due=0

#### Scenario: 非 BULLET 类型账单无累计利息增量
- **WHEN** 对 EQUAL_PRINCIPAL 或 INTEREST_FIRST 贷款生成账单
- **THEN** LoanBill.accrued_delta=0

### Requirement: LedgerComponent.issue_loan 发放贷款

#### Scenario: 发放企业贷款
- **WHEN** 银行(cash=50000) 向公司(cash=0) 发放 principal=10000 的贷款
- **THEN** 银行 cash=40000, receivables 包含该 Loan；公司 cash=10000, payables 包含该 Loan

### Requirement: LedgerComponent.generate_bills 账单生成

#### Scenario: 生成待付账单
- **WHEN** 实体有 2 笔 payables（1 笔 DEPOSIT，1 笔 CORPORATE_LOAN），调用 generate_bills()
- **THEN** 返回 2 个 LoanBill，按优先级排序 DEPOSIT 在前；存入 self.bills；Loan 状态不变

#### Scenario: 活期存款生成零额账单
- **WHEN** payables 中有 term=0 的活期存款
- **THEN** generate_bills() 为其生成账单，走 BULLET 非末期逻辑：principal_due=0, interest_due=0, total_due=0，利息累计到 Loan.accrued_interest

### Requirement: LedgerComponent.settle_all 结算支付

#### Scenario: 足额支付
- **WHEN** 实体 cash=10000，bills 中有一笔 total_due=2500 的账单
- **THEN** settle_all 后 bill.total_paid=2500，实体 cash=7500，债权人 cash 增加 2500

#### Scenario: 不足额支付
- **WHEN** 实体 cash=1000，bills 中有一笔 total_due=2500 的账单
- **THEN** bill.total_paid=1000，实体 cash=0，按优先偿还利息再偿还本金

#### Scenario: 结算优先级
- **WHEN** 实体有 DEPOSIT 和 CORPORATE_LOAN 两笔账单，cash 不足以全部支付
- **THEN** 先支付 DEPOSIT 账单，剩余 cash 支付 CORPORATE_LOAN

#### Scenario: 到期清除
- **WHEN** 某 Loan 还清（remaining=0）
- **THEN** 从债权人 receivables 和债务人 payables 中移除

#### Scenario: 活期存款利息累计
- **WHEN** payables 中有 term=0、remaining=10000、rate=500 的活期存款，settle_all() 执行
- **THEN** 利息 500 累计到 loan.accrued_interest，不产生现金划转（total_due=0）

### Requirement: LedgerComponent.withdraw 存款取款

#### Scenario: 足额取款含利息
- **WHEN** 活期存款 remaining=5000, accrued_interest=200，吸储方 cash=10000，取款 amount=3000
- **THEN** 返回本金 3000 + 利息 200 = 实际划转 3200；存款方 cash+=3200，吸储方 cash-=3200；loan.remaining=2000, loan.accrued_interest=0

#### Scenario: 受限于吸储方现金
- **WHEN** 活期存款 remaining=5000, accrued_interest=200，吸储方 cash=1000，取款 amount=3000
- **THEN** 优先支付利息 200，剩余 800 为本金归还；返回实际取出本金 800；loan.remaining=4200, loan.accrued_interest=0

#### Scenario: 取完后移除
- **WHEN** 取款使 loan.remaining=0 且 accrued_interest 已结清
- **THEN** Loan 从双方列表移除

### Requirement: LedgerComponent.write_off 坏账核销

#### Scenario: 核销贷款
- **WHEN** 对一笔 remaining=5000 的贷款调用 write_off
- **THEN** 从债权人 receivables 和债务人 payables 中移除，不产生现金流

### Requirement: LedgerComponent 查询方法

#### Scenario: total_receivables
- **WHEN** receivables 中有 remaining=5000 和 remaining=3000 两笔
- **THEN** total_receivables()=8000

#### Scenario: net_financial_assets
- **WHEN** cash=10000, total_receivables=8000, total_payables=5000
- **THEN** net_financial_assets()=13000

#### Scenario: filter_loans
- **WHEN** receivables 有 1 笔 CORPORATE_LOAN，payables 有 1 笔 DEPOSIT
- **THEN** filter_loans(CORPORATE_LOAN) 返回 1 笔，filter_loans(DEPOSIT) 返回 1 笔
