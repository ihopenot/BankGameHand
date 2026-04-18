## Why

当前游戏结算阶段（`settlement_phase`）只执行简单的账单结算，缺少破产检查和清算流程。Company.md 和 Bank.md 中已设计的破产机制未在代码中实现，导致：

- 无法偿还贷款的公司不会被淘汰，经济模拟缺乏真实性
- 银行坏账无法产生，削弱了玩家的风险管理维度
- 产业链可能因公司大量倒闭而断裂，但没有市场补充机制来防止死局

## What Changes

### 1. 破产标记（LedgerComponent 扩展）

在 `LedgerComponent.settle_all()` 结算过程中，检测当回合是否存在未能全额结算的应付账单（包括贷款还款），如果存在则为该组件打上破产标记。

### 2. 企业破产清算（新建 BankruptcyService）

新建 `BankruptcyService`，在结算完成后读取破产标记，依次对破产公司执行清算：
- 计算清算所得（工厂造价 x 50% + 现有现金）
- 库存直接清空
- 按优先级偿还债务：工资 > 应付账款 > 银行贷款
- 不足部分记为坏账，写入债权方资产负债表
- 销毁公司实体
- 本回合不递归检查连锁破产

### 3. 市场补充机制（BankruptcyService 扩展）

清算完成后检查每种商品的存活生产者数量，低于最低阈值时政府出资创建新公司：
- 获得一个基础工厂
- 获得启动资金
- CEO 特质随机生成
- 无品牌、无科技积累

## Impact

### 受影响的代码

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `component/ledger_component.py` | 修改 | 增加破产标记逻辑 |
| `system/bankruptcy_service.py` | 新增 | 破产清算与市场补充服务 |
| `game/game.py` | 修改 | settlement_phase 中集成 BankruptcyService |
| `config/game.yaml` | 修改 | 添加清算折价率、市场补充阈值等配置 |
| `tests/test_bankruptcy_service.py` | 新增 | 破产清算测试 |
| `tests/test_ledger_bankruptcy.py` | 新增 | 破产标记测试 |
| `tests/test_game_bankruptcy.py` | 新增 | Game 集成测试 |

### 受影响的系统

- **结算系统**：结算后增加破产检查步骤
- **银行系统**：坏账核销影响银行资产负债表
- **公司系统**：破产公司被销毁，影响市场供给
- **市场系统**：生产者数量变化触发市场补充
