## 1. 创建 MetricComponent 和 RoundSnapshot

- [x] 1.1 创建 MetricComponent 基础结构  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_metric_component.py` — 测试 MetricComponent 继承 BaseComponent；包含 `last_sell_orders: Dict[GoodsType, int]`（初始空）、`last_sold_quantities: Dict[GoodsType, int]`（初始空）、`last_revenue: int`（初始 0）、`last_avg_buy_prices: Dict[GoodsType, float]`（初始空）；包含累计计数器 `cumulative_revenue`、`cumulative_brand_spend`、`cumulative_tech_spend`、`cumulative_expansion_spend`（初始 0）；包含 `round_history: List[RoundSnapshot]`（初始空）
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认失败原因是缺少模块）
  - [x] 1.1.3 写最小实现：创建 `component/metric_component.py` — MetricComponent 类继承 BaseComponent，包含所有上述字段
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认所有测试通过）
  - [x] 1.1.5 重构：整理代码、改善命名（保持所有测试通过）

- [x] 1.2 创建 RoundSnapshot 数据结构  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_metric_component.py` — 测试 RoundSnapshot 是 dataclass，包含 `round_number: int`、`cash: int`、`revenue: int`（默认 0）、`sell_orders: Dict[GoodsType, int]`（默认空）、`sold_quantities: Dict[GoodsType, int]`（默认空）、`prices: Dict[GoodsType, int]`（默认空）、`brand_values: Dict[GoodsType, int]`（默认空）、`tech_values: Dict[Recipe, int]`（默认空）、`investment_plan: Dict[str, int]`（默认空）、`actual_investment: Dict[str, int]`（默认空）；测试 MetricComponent.add_snapshot() 能添加快照到 round_history
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认失败原因是缺少 RoundSnapshot）
  - [x] 1.2.3 写最小实现：在 `component/metric_component.py` 中添加 RoundSnapshot dataclass 和 MetricComponent.add_snapshot() 方法
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认所有测试通过）
  - [x] 1.2.5 重构：整理代码（保持所有测试通过）

- [x] 1.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/metric-component/specs/*.md` 和 `openspec/changes/metric-component/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `component/metric_component.py`、`tests/test_metric_component.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. 挂载 MetricComponent 到实体

- [x] 2.1 Company 实体挂载 MetricComponent  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_metric_component.py` — 测试 Company 实例可通过 `get_component(MetricComponent)` 获取 MetricComponent
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认失败原因是 Company 未挂载 MetricComponent）
  - [x] 2.1.3 写最小实现：修改 `entity/company/company.py` — 在 `__init__` 中 `init_component(MetricComponent)`
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认所有测试通过）
  - [x] 2.1.5 重构：确认无冗余 import（保持所有测试通过）

- [x] 2.2 Folk 实体挂载 MetricComponent  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_metric_component.py` — 测试 Folk 实例可通过 `get_component(MetricComponent)` 获取 MetricComponent
  - [x] 2.2.2 验证测试失败（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认失败）
  - [x] 2.2.3 写最小实现：修改 `entity/folk.py` — 在 Folk.__init__ 中 `init_component(MetricComponent)`
  - [x] 2.2.4 验证测试通过（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认所有测试通过）
  - [x] 2.2.5 重构：整理 import（保持所有测试通过）

- [x] 2.3 Bank 实体挂载 MetricComponent  <!-- TDD 任务 -->
  - [x] 2.3.1 写失败测试：`tests/test_metric_component.py` — 测试 Bank 实例可通过 `get_component(MetricComponent)` 获取 MetricComponent
  - [x] 2.3.2 验证测试失败（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认失败）
  - [x] 2.3.3 写最小实现：修改 `entity/bank.py` — 在 Bank.__init__ 中 `init_component(MetricComponent)`
  - [x] 2.3.4 验证测试通过（运行：`python -m pytest tests/test_metric_component.py -x -q`，确认所有测试通过）
  - [x] 2.3.5 重构：整理 import（保持所有测试通过）

- [x] 2.4 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/metric-component/specs/*.md` 和 `openspec/changes/metric-component/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `entity/company/company.py`、`entity/folk.py`、`entity/bank.py`、`tests/test_metric_component.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 3. 修复 Bug：接入销售指标写入

- [x] 3.1 sell_phase 写入 last_sell_orders  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_company_service.py` — 测试 sell_phase 执行后，每个 Company 的 MetricComponent.last_sell_orders 记录了对应 GoodsType 的挂单总量
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_company_service.py -x -q -k test_sell_phase_updates_sell_orders`，确认失败）
  - [x] 3.1.3 写最小实现：修改 `system/company_service.py` — 在 sell_phase() 中，遍历挂单时累计写入 MetricComponent.last_sell_orders；每轮开始时重置为空
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_company_service.py -x -q -k test_sell_phase_updates_sell_orders`，确认通过）
  - [x] 3.1.5 重构：整理代码（保持所有测试通过）

- [x] 3.2 trade 结算写入 last_sold_quantities 和 last_revenue（居民购买）  <!-- TDD 任务 -->
  - [x] 3.2.1 写失败测试：`tests/test_folk_service.py` — 测试居民购买后，卖方 Company 的 MetricComponent.last_sold_quantities 和 last_revenue 正确累加
  - [x] 3.2.2 验证测试失败（运行：`python -m pytest tests/test_folk_service.py -x -q -k test_folk_buy_updates_seller_metrics`，确认失败）
  - [x] 3.2.3 写最小实现：修改 `system/folk_service.py` — 在 settle_trades() 中，对每笔 trade 更新卖方 MetricComponent 的 last_sold_quantities 和 last_revenue
  - [x] 3.2.4 验证测试通过（运行：`python -m pytest tests/test_folk_service.py -x -q -k test_folk_buy_updates_seller_metrics`，确认通过）
  - [x] 3.2.5 重构：整理代码（保持所有测试通过）

- [x] 3.3 trade 结算写入 last_sold_quantities 和 last_revenue（企业间购买）  <!-- TDD 任务 -->
  - [x] 3.3.1 写失败测试：`tests/test_company_service.py` — 测试企业间交易后，卖方 MetricComponent.last_sold_quantities 和 last_revenue 正确累加
  - [x] 3.3.2 验证测试失败（运行：`python -m pytest tests/test_company_service.py -x -q -k test_settle_trades_updates_seller_metrics`，确认失败）
  - [x] 3.3.3 写最小实现：修改 `system/company_service.py` — 在 settle_trades() 中更新卖方 MetricComponent 的 last_sold_quantities 和 last_revenue
  - [x] 3.3.4 验证测试通过（运行：`python -m pytest tests/test_company_service.py -x -q -k test_settle_trades_updates_seller_metrics`，确认通过）
  - [x] 3.3.5 重构：整理代码（保持所有测试通过）

- [x] 3.4 每轮开始时重置当轮指标  <!-- TDD 任务 -->
  - [x] 3.4.1 写失败测试：`tests/test_metric_component.py` — 测试 MetricComponent.reset_round() 方法将 last_sell_orders、last_sold_quantities、last_revenue 重置为空/零
  - [x] 3.4.2 验证测试失败（运行：`python -m pytest tests/test_metric_component.py -x -q -k test_reset_round`，确认失败）
  - [x] 3.4.3 写最小实现：在 `component/metric_component.py` 添加 reset_round() 方法；在 `game/game.py` 的 update_phase() 开头调用所有 MetricComponent 的 reset_round()
  - [x] 3.4.4 验证测试通过（运行：`python -m pytest tests/test_metric_component.py -x -q -k test_reset_round`，确认通过）
  - [x] 3.4.5 重构：整理代码（保持所有测试通过）

- [x] 3.5 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/metric-component/specs/*.md` 和 `openspec/changes/metric-component/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/company_service.py`、`system/folk_service.py`、`component/metric_component.py`、`game/game.py`、相关测试文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 4. 迁移 DecisionComponent 和 Folk 的字段到 MetricComponent

- [x] 4.1 DecisionService 改为从 MetricComponent 读取指标  <!-- TDD 任务 -->
  - [x] 4.1.1 写失败测试：`tests/test_decision_service.py` — 测试 decide_pricing() 从 MetricComponent 读取 last_sell_orders/last_sold_quantities；测试 _plan_brand()/_plan_tech() 从 MetricComponent 读取 last_revenue；测试 make_purchase_sort_key() 从 MetricComponent 读取 last_avg_buy_prices
  - [x] 4.1.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py -x -q`，确认失败原因是 DecisionService 仍读取 DecisionComponent）
  - [x] 4.1.3 写最小实现：修改 `system/decision_service.py` — decide_pricing()、_plan_brand()、_plan_tech()、make_purchase_sort_key() 改为从 MetricComponent 获取对应字段
  - [x] 4.1.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py -x -q`，确认所有测试通过）
  - [x] 4.1.5 重构：整理代码（保持所有测试通过）

- [x] 4.2 从 DecisionComponent 移除迁移字段  <!-- 非 TDD 任务 -->
  - [x] 4.2.1 执行变更：修改 `component/decision_component.py` — 移除 `last_sell_orders`、`last_sold_quantities`、`last_revenue`、`last_avg_buy_prices` 字段
  - [x] 4.2.2 验证无回归（运行：`python -m pytest tests/ -x -q`，确认所有测试通过）
  - [x] 4.2.3 检查：确认无其他文件仍引用 DecisionComponent 的这些已移除字段

- [x] 4.3 CompanyService._update_avg_buy_prices 改写到 MetricComponent  <!-- TDD 任务 -->
  - [x] 4.3.1 写失败测试：`tests/test_company_service.py` — 测试企业采购结算后，买方的 MetricComponent.last_avg_buy_prices 按成交量加权正确更新
  - [x] 4.3.2 验证测试失败（运行：`python -m pytest tests/test_company_service.py -x -q -k test_update_avg_buy_prices_metric`，确认失败）
  - [x] 4.3.3 写最小实现：修改 `system/company_service.py` — _update_avg_buy_prices() 改为写入 MetricComponent 而非 DecisionComponent
  - [x] 4.3.4 验证测试通过（运行：`python -m pytest tests/test_company_service.py -x -q -k test_update_avg_buy_prices_metric`，确认通过）
  - [x] 4.3.5 重构：整理代码（保持所有测试通过）

- [x] 4.4 从 Folk 迁移 last_avg_buy_prices 到 MetricComponent  <!-- TDD 任务 -->
  - [x] 4.4.1 写失败测试：`tests/test_folk_service.py` — 测试 buy_phase 后 Folk 的 MetricComponent.last_avg_buy_prices 正确更新；`tests/test_folk.py` — 测试 Folk 不再有直接的 last_avg_buy_prices 属性
  - [x] 4.4.2 验证测试失败（运行：`python -m pytest tests/test_folk_service.py tests/test_folk.py -x -q`，确认失败）
  - [x] 4.4.3 写最小实现：修改 `entity/folk.py` — 移除 `last_avg_buy_prices` 属性；修改 `system/folk_service.py` — allocate_and_trade() 和 _update_avg_buy_prices() 改为读写 MetricComponent
  - [x] 4.4.4 验证测试通过（运行：`python -m pytest tests/test_folk_service.py tests/test_folk.py -x -q`，确认通过）
  - [x] 4.4.5 重构：整理代码（保持所有测试通过）

- [x] 4.5 更新现有测试中对旧字段的引用  <!-- 非 TDD 任务 -->
  - [x] 4.5.1 执行变更：更新 `tests/test_decision_service.py`、`tests/test_decision_component.py`、`tests/test_folk.py`、`tests/test_folk_service.py` — 所有对 `dc.last_sell_orders`、`dc.last_sold_quantities`、`dc.last_revenue`、`dc.last_avg_buy_prices`、`folk.last_avg_buy_prices` 的引用改为通过 MetricComponent
  - [x] 4.5.2 验证无回归（运行：`python -m pytest tests/ -x -q`，确认所有测试通过）
  - [x] 4.5.3 检查：grep 确认无任何残留的旧字段引用

- [x] 4.6 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/metric-component/specs/*.md` 和 `openspec/changes/metric-component/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/decision_service.py`、`component/decision_component.py`、`system/company_service.py`、`entity/folk.py`、`system/folk_service.py`、所有更新的测试文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 5. 创建 MetricService 和快照阶段

- [x] 5.1 创建 MetricService 及 snapshot_phase  <!-- TDD 任务 -->
  - [x] 5.1.1 写失败测试：`tests/test_metric_service.py` — 测试 MetricService.snapshot_phase() 为每个 Company 生成 RoundSnapshot（包含 round_number、cash、revenue、sell_orders、sold_quantities、prices、brand_values、tech_values、investment_plan）并追加到 round_history；测试为 Folk 和 Bank 生成快照（包含 round_number、cash）
  - [x] 5.1.2 验证测试失败（运行：`python -m pytest tests/test_metric_service.py -x -q`，确认失败原因是缺少模块）
  - [x] 5.1.3 写最小实现：创建 `system/metric_service.py` — MetricService 类包含 snapshot_phase() 方法，遍历所有 MetricComponent 实例采集快照
  - [x] 5.1.4 验证测试通过（运行：`python -m pytest tests/test_metric_service.py -x -q`，确认所有测试通过）
  - [x] 5.1.5 重构：整理代码（保持所有测试通过）

- [x] 5.2 接入 Game 循环  <!-- TDD 任务 -->
  - [x] 5.2.1 写失败测试：`tests/test_game_integration.py` — 测试 game_loop 运行一轮后，Company 的 MetricComponent.round_history 长度为 1 且 RoundSnapshot.round_number == 1
  - [x] 5.2.2 验证测试失败（运行：`python -m pytest tests/test_game_integration.py -x -q -k test_metric_snapshot_after_round`，确认失败）
  - [x] 5.2.3 写最小实现：修改 `game/game.py` — 初始化 MetricService，在 game_loop 每轮末尾（act_phase 之后）调用 metric_service.snapshot_phase()
  - [x] 5.2.4 验证测试通过（运行：`python -m pytest tests/test_game_integration.py -x -q -k test_metric_snapshot_after_round`，确认通过）
  - [x] 5.2.5 重构：整理代码（保持所有测试通过）

- [x] 5.3 累计计数器更新  <!-- TDD 任务 -->
  - [x] 5.3.1 写失败测试：`tests/test_metric_service.py` — 测试 snapshot_phase() 执行后，MetricComponent 的 cumulative_revenue 累加了当轮 last_revenue；测试多轮后累计值正确
  - [x] 5.3.2 验证测试失败（运行：`python -m pytest tests/test_metric_service.py -x -q -k test_cumulative`，确认失败）
  - [x] 5.3.3 写最小实现：在 MetricService.snapshot_phase() 中，累加 cumulative_revenue += last_revenue；在 DecisionService.act_phase() 中累加 cumulative_brand_spend、cumulative_tech_spend、cumulative_expansion_spend 到 MetricComponent
  - [x] 5.3.4 验证测试通过（运行：`python -m pytest tests/test_metric_service.py -x -q -k test_cumulative`，确认通过）
  - [x] 5.3.5 重构：整理代码（保持所有测试通过）

- [x] 5.4 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/metric-component/specs/*.md` 和 `openspec/changes/metric-component/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/metric_service.py`、`game/game.py`、`system/decision_service.py`、相关测试文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 6. 端到端集成验证

- [x] 6.1 端到端测试：价格更新和投资生效  <!-- TDD 任务 -->
  - [x] 6.1.1 写失败测试：`tests/test_integration.py` — 测试运行 2 轮完整 game_loop 后：(a) Company 的 ProductorComponent.prices 不全等于 base_price（价格更新生效）；(b) 至少有一个 Company 的 MetricComponent.cumulative_brand_spend > 0 或 cumulative_tech_spend > 0（投资生效）
  - [x] 6.1.2 验证测试失败（运行：`python -m pytest tests/test_integration.py -x -q -k test_price_and_investment_work`，确认失败）
  - [x] 6.1.3 写最小实现：如果测试失败不是因为功能缺失而是集成问题，定位并修复连接问题
  - [x] 6.1.4 验证测试通过（运行：`python -m pytest tests/test_integration.py -x -q -k test_price_and_investment_work`，确认通过）
  - [x] 6.1.5 重构：整理代码（保持所有测试通过）

- [x] 6.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/metric-component/specs/*.md` 和 `openspec/changes/metric-component/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `tests/test_integration.py` 及任何集成修复文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 7. PreCI 代码规范检查

- [x] 7.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：执行安装命令，安装完成后继续
  - 若找到：记录可用路径，直接继续
- [x] 7.2 检测项目是否已 preci 初始化
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`，等待完成后继续
- [x] 7.3 检测 PreCI Server 状态
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`，等待服务启动（最多 10 秒）
  - 若启动失败：输出警告但继续扫描流程
- [x] 7.4 执行代码规范扫描
  - 依次执行两个扫描命令：
    1. `<preci路径> scan --diff`（扫描未暂存变更）
    2. `<preci路径> scan --pre-commit`（扫描已暂存变更）
  - 合并两次扫描结果，去重后统一处理
  - 仅扫描代码文件（跳过 .md/.yml/.json/.xml/.txt/.png/.jpg 等非代码文件）
- [x] 7.5 处理扫描结果
  - 若无告警：输出 `✅ PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多 3 次重试），修正后重新扫描验证

## 8. Documentation Sync (Required)

- [x] 8.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 8.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 8.3 sync proposal.md: update scope/impact if changed
- [x] 8.4 sync specs/*.md: update requirements if changed
- [x] 8.5 Final review: ensure all OpenSpec docs reflect actual implementation
