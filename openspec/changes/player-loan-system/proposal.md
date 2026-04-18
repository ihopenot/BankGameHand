## Why

当前游戏中玩家操作阶段（PlayerAct）仅支持"跳过"，没有实质性的玩家决策。企业的投资计划受限于自有现金，缺少贷款融资渠道。游戏需要引入银行角色（由玩家控制），让玩家通过审批贷款、设定利率来参与经济博弈。

## What Changes

1. **新增 Bank 实体**：继承 Entity，拥有 LedgerComponent，由玩家控制，初始资金可配置
2. **新增 BankService**：管理贷款申请收集、银行实体追踪、贷款接受匹配逻辑
3. **增强 Plan 阶段**：企业在制定投资计划时计算贷款需求（计划总额 - 可用预算）
4. **新增贷款申请子阶段**：所有企业提交贷款申请，BankService 收集
5. **增强 PlayerAct 阶段**：玩家审批贷款（设定利率、批准金额、还款方式、期限）
6. **新增贷款接受子阶段**：企业按利率从低到高接受报价，直到满足借款需求
7. **增强终端输出**：显示企业商品定价、银行摘要、活跃贷款、贷款申请

## Impact

- **game.py**：游戏循环从 8 阶段扩展为 10 阶段（新增贷款申请、贷款接受）
- **decision_service.py**：Plan 阶段增加贷款需求计算
- **player_service.py**：PlayerAct 阶段增加贷款审批交互和信息展示
- **core/types.py**：可能新增 LoanApplication 数据类型
- **config/game.yaml**：新增 banks 配置段
- **entity/**：新增 bank.py
- **system/**：新增 bank_service.py
