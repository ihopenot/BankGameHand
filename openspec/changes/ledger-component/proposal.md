## Why

当前 LedgerComponent 只有 `cash`、`loans`、`deposit` 三个空字段和空的 `Loan` 类，无法支撑 GameDesign 中描述的金融业务流程（企业贷款、居民存款、政府债券、银行间拆借、利息计算、还款结算、坏账核销等）。所有经济实体（银行、公司、居民）都需要通用的金融能力组件来管理债权/债务关系。

## What Changes

- 重新设计 `Loan` 类：包含债权人/债务人引用、本金、剩余本金、利率、期限、偿付类型等完整字段，支持 `settle()` 方法按偿付类型生成结算账单
- 新增 `LoanType` 枚举（企业贷款、居民存款、银行间拆借、政府债券）
- 新增 `RepaymentType` 枚举（等额本金、先息后本、到期本息）
- 新增 `LoanBill` 数据类：结算账单，包含应付本金、应付利息、实付总额
- 重写 `LedgerComponent`：管理 `cash`/`receivables`/`payables`/`bills`，提供 `issue_loan`/`generate_bills`/`settle_all`/`withdraw`/`write_off`/`unpaid_bills` 等接口
- 结算优先级：DEPOSIT → INTERBANK → CORPORATE_LOAN → BOND

## Impact

- `core/types.py`：重写 `Loan` 类，新增 `LoanType`、`RepaymentType`、`LoanBill`
- `component/ledger_component.py`：完全重写
- `tests/test_ledger_component.py`：完全重写，覆盖所有金融操作场景
- 不影响现有的 `StorageComponent`、`ProductorComponent`、`Entity` 等模块
