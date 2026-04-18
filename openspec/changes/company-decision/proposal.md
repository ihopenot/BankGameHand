## Why

游戏主循环中 `plan_phase()` 和 `act_phase()` 当前为空 stub，企业 AI 决策系统尚未实现。设计文档 (`docs/GameDesign/Company.md`) 定义了完整的 CEO 特质体系和企业决策，是游戏核心玩法的关键支撑——没有企业决策，公司无法自主定价、扩产、投资研发，经济模拟缺乏动态博弈。

## What Changes

新增 CEO 特质体系和企业决策系统：

1. **DecisionComponent** — 存储 5 维 CEO 特质（商业洞察力、风险偏好、利润追求、营销意识、科技重视度）、投资计划表（investment_plan）及决策中间状态
2. **DecisionService** — 编排决策逻辑：
   - plan_phase：产品定价 + 生成投资计划表（扩产/品牌/科技三个方向的计划金额）
   - act_phase：计算保留金 → 确定投资预算 → 按计划执行或按比例分配 → 未花完回流
   - 采购偏好：CEO 营销意识影响供应商评分权重
3. **decision.yaml** — 所有决策公式系数配置化
4. **现有文件修改** — Company 挂载 DecisionComponent、game.py 编排 plan/act_phase、company_service.py 使用特质计算采购偏好

## Impact

- **新增文件**: `component/decision_component.py`, `system/decision_service.py`, `config/decision.yaml`
- **修改文件**: `entity/company/company.py`, `game/game.py`, `system/company_service.py`
- **测试文件**: `tests/test_decision_component.py`, `tests/test_decision_service.py`
- **不影响**: LedgerComponent、ProductorComponent、MarketService、FolkService 等核心组件的内部逻辑不变
- **依赖方向**: DecisionService 依赖 ProductorComponent（读取工厂/库存/价格）和 LedgerComponent（读取现金），不引入循环依赖
