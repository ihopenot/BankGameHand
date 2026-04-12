## ADDED Requirements

### Requirement: 玩家操作阶段经济数据展示

在每回合的 `player_act` 阶段，向玩家展示当前宏观经济数据和所有公司的财务概览。

#### Scenario: 展示宏观经济信息

- **WHEN** 进入 player_act 阶段
- **THEN** 展示当前回合数/总回合数、经济指数（economy_index 转为小数比率）

#### Scenario: 展示公司财务概览

- **WHEN** 进入 player_act 阶段
- **THEN** 以纯文本表格展示每家公司的：公司名、工厂类型、现金余额、库存（类型和数量）、应收款总额、应付款总额

### Requirement: 玩家跳过回合操作

玩家在查看经济数据后，可以选择跳过当前回合。

#### Scenario: 输入 skip 跳过回合

- **WHEN** 玩家输入 `skip`
- **THEN** 结束 player_act 阶段，继续后续游戏流程

#### Scenario: 直接回车跳过回合

- **WHEN** 玩家直接按回车（空输入）
- **THEN** 等同于 `skip`，结束 player_act 阶段

#### Scenario: 输入无法识别的命令

- **WHEN** 玩家输入非 `skip` 且非空的内容
- **THEN** 提示"无法识别的命令，请输入 skip 或直接回车跳过回合"，重新等待输入
