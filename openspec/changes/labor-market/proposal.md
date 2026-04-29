## Why

当前经济模拟中，工厂生产只受原材料供给约束，缺少劳动力要素。企业无需雇佣工人、支付工资，生产与居民之间缺少劳动收入这一关键经济循环环节。这导致模拟缺乏劳动力市场竞争、工资博弈等核心经济动态。

## What Changes

- **劳动力市场系统**：新增 `LaborService`，实现岗位发布、劳动力匹配（按工资从高到低填满岗位）
- **工厂劳动力需求**：`FactoryType` 新增 `labor_demand` 字段，生产效率受 staffing_ratio 约束
- **移除 base_production**：工厂基础产量直接使用 1 倍（`recipe.output_quantity`）
- **企业工资决策**：决策组件新增 `decide_wage()` 方法，Classic 实现固定返回 `initial_wage`
- **工资支付**：生产阶段生成当回合到期负债，结算阶段统一扣款
- **居民劳动力供给**：`Folk` 新增 `labor_participation_rate` 和 `labor_points_per_capita` 配置
- **游戏循环调整**：Plan 阶段前移，新增 Labor Match 阶段（Plan → Labor Match → Produce）

## Impact

- **entity/factory.py**：`FactoryType` 新增 `labor_demand`、移除 `base_production`；`Factory.produce()` 逻辑变更
- **entity/folk.py**：新增劳动力相关字段和 `labor_supply` 属性
- **component/base_company_decision.py**：新增 `decide_wage()` 抽象方法
- **component/classic_company_decision.py**：实现固定工资决策
- **component/productor_component.py**：生产逻辑适配 staffing_ratio，require_goods base 改为 1
- **component/ai_company_decision.py**：序列化工厂信息字段从 base_production 改为 labor_demand
- **system/labor_service.py**：新增劳动力市场匹配服务
- **system/decision_service.py**：集成工资决策，_build_context 添加 initial_wage
- **system/productor_service.py**：product_phase 传递 staffing_ratio，生成工资负债
- **system/company_service.py**：buy_phase 需求公式移除 base_production 乘数，create_company 添加 initial_wage 参数
- **game/game.py**：游戏循环阶段重排，新增 labor_match_phase，集成 LaborService
- **config/goods.yaml**：工厂类型新增 labor_demand、移除 base_production
- **config/folk.yaml**：居民组新增劳动力参数
- **config/game.yaml**：企业新增 initial_wage
