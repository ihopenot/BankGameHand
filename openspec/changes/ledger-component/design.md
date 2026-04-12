## Context

GameDesign 中 EconomyEntryComponent 定义了经济实体的资产负债表、Transaction 函数等完整体系。本次聚焦其中的**金融能力**子集——贷款、存款、利息计算、结算、坏账核销，不涉及三大表和 Transaction 函数。

当前代码中 `Loan` 是空类，`LedgerComponent` 只有 `cash: int`、`loans: List[Loan]`、`deposit: List[Loan]` 三个字段，无任何业务逻辑。

项目使用 ECS 架构（Entity-Component-System），LedgerComponent 作为通用组件挂载到所有经济实体上。

## Goals / Non-Goals

**Goals:**
- 实现通用的金融能力组件，不按实体类型区分，所有经济实体共用
- 用统一的 Loan 数据结构表达所有双边金融关系（贷款、存款、拆借、债券）
- 支持三种偿付类型：等额本金、先息后本、到期本息
- 账单生成与支付分离：generate_bills → settle_all → unpaid_bills 三步流程
- 结算优先级：DEPOSIT → INTERBANK → CORPORATE_LOAN → BOND

**Non-Goals:**
- 不实现资产负债表、现金流量表、利润表（三大表）
- 不实现 Transaction 函数（通用资产交换接口）
- 不实现清算/破产逻辑（由上层 Service 负责）
- 不实现银行特有的业务流程（审批、报价等，由 BankService 负责）

## Decisions

1. **统一 Loan 模型**：贷款、存款、拆借、债券本质上都是"一方借钱给另一方，约定利率和期限"，用同一个 Loan 类 + LoanType 枚举区分。存款中居民是债权人、银行是债务人。

2. **偿付类型内聚到 Loan**：Loan.settle() 根据 RepaymentType 计算本期账单返回 LoanBill，LedgerComponent 做编排不关心偿付细节。

3. **三步结算流程**：generate_bills() 只算账不动状态 → settle_all() 执行现金划转 → unpaid_bills() 检查违约。上层 Service 可在步骤 1 和 2 之间插入玩家决策。

4. **活期存款走 BULLET 逻辑**：term=0 表示活期，走 BULLET 非末期结算逻辑（永远不到期），每回合利息累计到 accrued_interest，generate_bills 生成 total_due=0 的账单。取款通过 withdraw() 操作，取款时一并结清 accrued_interest。

5. **双边同步**：issue_loan、settle_all、withdraw、write_off 同时操作债权人和债务人的 LedgerComponent，保证一致性。

6. **违约检测与清算分离**：unpaid_bills() 只返回未付清账单，不执行清算操作，清算逻辑由上层 Service 决定。

## Risks / Trade-offs

- **双边同步一致性**：Loan 同时存在于双方的列表中，任何操作必须同步更新双方，需要谨慎处理引用关系
- **Money 精度**：使用 int（分）和 Rate（万分比），除法会有舍入，需要统一舍入策略（向下取整）
- **withdraw 调用约束**：withdraw() 必须在债务方（吸储方）的 LedgerComponent 上调用，已通过 assert 防御
- **活期存款 elapsed 不递增**：term=0 的活期存款没有到期概念，settle_all 中跳过 elapsed 递增
