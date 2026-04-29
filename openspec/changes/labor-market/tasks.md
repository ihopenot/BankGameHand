# Labor Market — Implementation Tasks

## 1. 数据模型变更：FactoryType 与 Folk

- [x] 1.1 FactoryType 新增 labor_demand 并移除 base_production  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_factory.py` — 测试 FactoryType 包含 labor_demand 字段、不包含 base_production 字段
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_factory.py -x -q`，确认失败原因是缺少 labor_demand 或仍存在 base_production）
  - [x] 1.1.3 写最小实现：`entity/factory.py` — FactoryType 添加 labor_demand: int，移除 base_production；`config/goods.yaml` — 每个 factory_type 添加 labor_demand 值、移除 base_production
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_factory.py -x -q`，确认所有测试通过）
  - [x] 1.1.5 重构：整理代码、确认所有引用 base_production 的地方已清理

- [x] 1.2 Folk 新增劳动力供给字段  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_folk.py` — 测试 Folk 包含 labor_participation_rate 和 labor_points_per_capita 字段，测试劳动力供给计算
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_folk.py -x -q`，确认失败原因是缺少新字段）
  - [x] 1.2.3 写最小实现：`entity/folk.py` — Folk 添加 labor_participation_rate: float 和 labor_points_per_capita: float；`config/folk.yaml` — 每个居民组添加配置值
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_folk.py -x -q`，确认所有测试通过）
  - [x] 1.2.5 重构：整理代码、改善命名（保持所有测试通过）

- [ ] 1.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/labor-market/specs/*.md` 和 `openspec/changes/labor-market/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 2. 生产逻辑变更：移除 base_production 使用、引入 staffing_ratio

- [x] 2.1 Factory.produce() 移除 base_production 倍数，引入 staffing_ratio 参数  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_factory.py` — 测试 produce() 接受 staffing_ratio 参数，output = recipe.output_quantity × min(material_ratio, staffing_ratio)
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_factory.py -x -q`，确认失败原因是缺少 staffing_ratio 参数或计算逻辑不对）
  - [x] 2.1.3 写最小实现：`entity/factory.py` — Factory.produce() 添加 staffing_ratio 参数，产量 = output_quantity × min(material_ratio, staffing_ratio)
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_factory.py -x -q`，确认所有测试通过）
  - [x] 2.1.5 重构：整理代码（保持所有测试通过）

- [x] 2.2 ProductorComponent.produce() 适配 staffing_ratio  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_productor_component.py` — 测试 produce/produce_all 正确传递 staffing_ratio 到 Factory
  - [x] 2.2.2 验证测试失败（运行：`python -m pytest tests/test_productor_component.py -x -q`）
  - [x] 2.2.3 写最小实现：`component/productor_component.py` — produce() 和 produce_all() 接受并传递 staffing_ratio
  - [x] 2.2.4 验证测试通过（运行：`python -m pytest tests/test_productor_component.py -x -q`）
  - [x] 2.2.5 重构：整理代码（保持所有测试通过）

- [x] 2.3 ProductorService 适配 staffing_ratio  <!-- TDD 任务 -->
  - [x] 2.3.1 写失败测试：`tests/test_productor_service.py` — 测试 ProductorService 将企业的 staffing_ratio 传递到 ProductorComponent
  - [x] 2.3.2 验证测试失败（运行：`python -m pytest tests/test_productor_service.py -x -q`）
  - [x] 2.3.3 写最小实现：`system/productor_service.py` — 从企业获取 staffing_ratio 并传递给 produce_all()
  - [x] 2.3.4 验证测试通过（运行：`python -m pytest tests/test_productor_service.py -x -q`）
  - [x] 2.3.5 重构：整理代码（保持所有测试通过）

- [ ] 2.4 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 3. 企业工资决策

- [x] 3.1 BaseCompanyDecisionComponent 新增 decide_wage() 抽象方法  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_base_company_decision.py` — 测试 decide_wage() 方法存在且可调用
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_base_company_decision.py -x -q`）
  - [x] 3.1.3 写最小实现：`component/base_company_decision.py` — 添加 decide_wage() 抽象方法
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_base_company_decision.py -x -q`）
  - [x] 3.1.5 重构：整理代码（保持所有测试通过）

- [x] 3.2 ClassicCompanyDecisionComponent 实现 decide_wage() 返回固定 initial_wage  <!-- TDD 任务 -->
  - [x] 3.2.1 写失败测试：`tests/test_classic_company_decision.py` — 测试 decide_wage() 返回 initial_wage 配置值
  - [x] 3.2.2 验证测试失败（运行：`python -m pytest tests/test_classic_company_decision.py -x -q`）
  - [x] 3.2.3 写最小实现：`component/classic_company_decision.py` — 实现 decide_wage() 返回 context 中的 initial_wage；`config/game.yaml` — 每家企业添加 initial_wage 配置
  - [x] 3.2.4 验证测试通过（运行：`python -m pytest tests/test_classic_company_decision.py -x -q`）
  - [x] 3.2.5 重构：整理代码（保持所有测试通过）

- [x] 3.3 DecisionService 集成 wage 决策  <!-- TDD 任务 -->
  - [x] 3.3.1 写失败测试：`tests/test_decision_service.py` — 测试 plan_phase 后企业有 wage 属性
  - [x] 3.3.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py -x -q`）
  - [x] 3.3.3 写最小实现：`system/decision_service.py` — plan_phase 中调用 decide_wage() 并存储到企业
  - [ ] 3.3.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py -x -q`）
  - [ ] 3.3.5 重构：整理代码（保持所有测试通过）

- [ ] 3.4 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 4. 劳动力市场匹配服务

- [x] 4.1 新增 LaborService 核心匹配逻辑  <!-- TDD 任务 -->
  - [x] 4.1.1 写失败测试：`tests/test_labor_service.py` — 测试岗位按工资从高到低匹配、劳动力不足时部分填满、劳动力充足时全满、staffing_ratio 计算正确
  - [x] 4.1.2 验证测试失败（运行：`python -m pytest tests/test_labor_service.py -x -q`，确认失败原因是 LaborService 不存在）
  - [x] 4.1.3 写最小实现：`system/labor_service.py` — 实现 LaborService，match() 方法执行按工资降序的岗位匹配，返回每企业的 staffing_ratio
  - [x] 4.1.4 验证测试通过（运行：`python -m pytest tests/test_labor_service.py -x -q`，确认所有测试通过）
  - [x] 4.1.5 重构：整理代码（保持所有测试通过）

- [x] 4.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 5. 工资支付（负债机制）

- [x] 5.1 生产阶段生成工资负债  <!-- TDD 任务 -->
  - [x] 5.1.1 写失败测试：`tests/test_productor_service.py` — 测试生产完成后企业新增一笔当回合到期的工资负债，金额 = filled_labor_points × wage
  - [x] 5.1.2 验证测试失败（运行：`python -m pytest tests/test_productor_service.py -x -q`）
  - [x] 5.1.3 写最小实现：`system/productor_service.py` — 生产后为企业生成工资负债（复用 LedgerComponent 的负债/bill 机制）
  - [x] 5.1.4 验证测试通过（运行：`python -m pytest tests/test_productor_service.py -x -q`）
  - [x] 5.1.5 重构：整理代码（保持所有测试通过）

- [x] 5.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 6. 游戏循环集成

- [x] 6.1 Game 类重排阶段顺序并集成 LaborService  <!-- TDD 任务 -->
  - [x] 6.1.1 写失败测试：`tests/test_game_loop.py` — 测试新的阶段顺序（Plan → Labor Match → Produce），测试 labor_match_phase 存在并正确调用 LaborService
  - [x] 6.1.2 验证测试失败（运行：`python -m pytest tests/test_game_loop.py -x -q`）
  - [x] 6.1.3 写最小实现：`game/game.py` — 新增 labor_match_phase()，重排 game_loop 阶段顺序：Update → Sell → Buy → Plan → Labor Match → Produce → Loan → Player Act → Settlement → Act → Snapshot
  - [x] 6.1.4 验证测试通过（运行：`python -m pytest tests/test_game_loop.py -x -q`）
  - [x] 6.1.5 重构：整理代码（保持所有测试通过）

- [x] 6.2 修复全量测试中因 base_production 移除和新参数导致的回归  <!-- 非 TDD 任务 -->
  - [x] 6.2.1 执行变更：修复所有因 base_production 移除、staffing_ratio 新参数、阶段顺序变更导致的测试失败
  - [x] 6.2.2 验证无回归（运行：`python -m pytest -x -q`，确认全量测试通过）
  - [x] 6.2.3 检查：确认变更范围完整，无遗漏文件或引用

- [x] 6.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 7. PreCI 代码规范检查

- [x] 7.1 检测 preci 安装状态（skip_preci: true，跳过）
- [x] 7.2 检测项目是否已 preci 初始化（skip_preci: true，跳过）
- [x] 7.3 检测 PreCI Server 状态（skip_preci: true，跳过）
- [x] 7.4 执行代码规范扫描（skip_preci: true，跳过）
- [x] 7.5 处理扫描结果（skip_preci: true，跳过）

## 8. Documentation Sync (Required)

- [x] 8.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 8.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 8.3 sync proposal.md: update scope/impact if changed
- [x] 8.4 sync specs/*.md: update requirements if changed
- [x] 8.5 Final review: ensure all OpenSpec docs reflect actual implementation
