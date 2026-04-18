## ADDED Requirements

### Requirement: bankruptcy-marking

LedgerComponent 在结算过程中检测破产条件并打标记。

#### Scenario: unsettled-bills-trigger-bankruptcy

- **WHEN** 当回合结算时存在未能全额结算的应付账单（包括贷款还款）
- **THEN** 该 LedgerComponent 被标记为破产（`is_bankrupt = True`）

#### Scenario: all-bills-settled-no-bankruptcy

- **WHEN** 当回合所有应付账单均已全额结算
- **THEN** 该 LedgerComponent 不被标记为破产（`is_bankrupt = False`）

### Requirement: bankruptcy-liquidation

BankruptcyService 对所有被标记破产的公司执行清算。

#### Scenario: liquidation-asset-calculation

- **WHEN** 一家公司被标记为破产
- **THEN** 计算清算所得 = 所有工厂造价之和 x 50% + 现有现金

#### Scenario: inventory-cleared

- **WHEN** 一家公司被标记为破产
- **THEN** 该公司所有库存直接清空，不计入清算所得

#### Scenario: repayment-priority-wages-first

- **WHEN** 清算所得不足以偿还所有债务
- **THEN** 按优先级偿还：优先级1 工资（欠薪） → 优先级2 应付账款（上游供应商货款） → 优先级3 银行贷款
- **THEN** 每个优先级内按比例分配（如有多个同级债权人）

#### Scenario: bad-debt-writeoff

- **WHEN** 清算所得不足以偿还某优先级的全部债务
- **THEN** 该优先级及更低优先级的未偿还部分记为坏账
- **THEN** 坏账写入对应债权方（银行或供应商公司）的资产负债表

#### Scenario: company-destroyed-after-liquidation

- **WHEN** 清算流程完成
- **THEN** 调用 `Entity.destroy()` 销毁该公司实体，从所有组件追踪列表中移除

#### Scenario: no-recursive-cascade

- **WHEN** 本回合有公司破产清算产生坏账
- **THEN** 本回合不重新检查其他公司是否因坏账触发破产
- **THEN** 受波及的公司如果因此无法偿债，在下一回合结算时自然满足破产条件

### Requirement: market-replenishment

清算完成后检查市场供给，不足时政府出资创建新公司。

#### Scenario: producer-below-threshold

- **WHEN** 某种商品的存活生产者数量 < 最低阈值（可配置，默认 2）
- **THEN** 政府出资成立新公司：
  - 获得一个该商品对应的基础工厂（最低等级）
  - 获得启动资金（可配置）
  - CEO 特质随机生成
  - 无品牌值、无科技积累

#### Scenario: producer-above-threshold

- **WHEN** 某种商品的存活生产者数量 >= 最低阈值
- **THEN** 不创建新公司

### Requirement: settlement-integration

Game.settlement_phase() 集成破产清算和市场补充流程。

#### Scenario: settlement-then-bankruptcy-then-replenishment

- **WHEN** 执行 settlement_phase
- **THEN** 先执行 LedgerService.settle_all()（含破产标记）
- **THEN** 再执行 BankruptcyService.process_bankruptcies()（清算）
- **THEN** 最后执行 BankruptcyService.replenish_market()（市场补充）
