## 1. 移除品质对产量的提升 + 产品品质加权混合

- [x] 1.1 修改 `Recipe` 新增 `tech_quality_weight` 属性，移除 `GoodsType.bonus_ceiling`  <!-- TDD 任务：使用 5 步子任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_factory.py` — 测试 Recipe 包含 `tech_quality_weight` 属性；`tests/test_goods.py` — 测试 GoodsType 不再包含 `bonus_ceiling`
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_factory.py tests/test_goods.py -x -q`，确认失败原因是缺少 `tech_quality_weight` / 仍有 `bonus_ceiling`）
  - [x] 1.1.3 写最小实现：修改 `entity/factory.py`（Recipe 新增 `tech_quality_weight: float`，`load_recipes()` 加载该字段）；修改 `entity/goods.py`（GoodsType 移除 `bonus_ceiling`，`load_goods_types()` 不再加载该字段）
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_factory.py tests/test_goods.py -x -q`，确认所有测试通过）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 修改 `Factory.produce()` 移除良品率加成，传递原材料品质  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_factory.py` — 测试产出数量不含品质加成（`base * output_quantity * sufficiency`）；测试返回的 GoodsBatch 携带原材料品质
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_factory.py -x -q`，确认失败原因是仍有 quality_bonus / quality 为 0.0）
  - [x] 1.2.3 写最小实现：修改 `entity/factory.py` — `produce()` 方法删除 `quality_bonus` 计算，产出公式改为 `int(base * recipe.output_quantity * sufficiency)`；返回的 GoodsBatch.quality 设为 `supply.quality`
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_factory.py -x -q`，确认所有测试通过）
  - [x] 1.2.5 重构：整理代码（保持所有测试通过）

- [x] 1.3 修改 `ProductorComponent.produce()` 实现加权混合品质  <!-- TDD 任务 -->
  - [x] 1.3.1 写失败测试：`tests/test_productor_service.py` — 测试有原料输入时品质 = `tech_rank_ratio * tech_quality_weight + material_quality * (1 - tech_quality_weight)`；测试原料层品质 = `tech_rank_ratio`；测试多工厂产出加权平均原材料品质
  - [x] 1.3.2 验证测试失败（运行：`python -m pytest tests/test_productor_service.py -x -q`，确认失败原因是品质计算不符合预期）
  - [x] 1.3.3 写最小实现：修改 `component/productor_component.py` — `produce()` 方法收集每个工厂的产出数量和原材料品质，按产出加权平均后与 tech_rank_ratio 做加权混合
  - [x] 1.3.4 验证测试通过（运行：`python -m pytest tests/test_productor_service.py -x -q`，确认所有测试通过）
  - [x] 1.3.5 重构：整理代码（保持所有测试通过）

- [x] 1.4 更新配置文件  <!-- 非 TDD 任务：使用 3 步子任务 -->
  - [x] 1.4.1 执行变更：修改 `config/goods.yaml` — 移除所有 `bonus_ceiling` 字段；每个配方新增 `tech_quality_weight`（原料层 1.0，中间品 0.6，终端消费品 0.5）；同步修改 `tests/config_integration/goods.yaml`
  - [x] 1.4.2 验证无回归（运行：`python -m pytest -x -q`，确认输出干净）
  - [x] 1.4.3 检查：确认变更范围完整，无遗漏文件或引用

- [x] 1.5 修复所有因 `bonus_ceiling` 移除和 `tech_quality_weight` 新增导致的测试破损  <!-- 非 TDD 任务 -->
  - [x] 1.5.1 执行变更：更新所有引用 `bonus_ceiling` 的测试文件（`tests/test_goods_config.py`, `tests/test_factory.py`, `tests/test_goods.py`, `tests/test_components.py`, `tests/test_productor_service.py`, `tests/test_productor_service_update.py`, `tests/test_integration.py`, `tests/test_review_regressions.py`, `tests/test_market_service.py`, `tests/test_market_match.py`, `tests/test_company_buy_phase.py`, `tests/test_company_buy_settlement.py`, `tests/test_company_sell_phase.py`, `tests/test_bankruptcy_service.py`, `tests/test_productor_prices.py` 等），移除 `bonus_ceiling` 参数，添加 `tech_quality_weight` 到 Recipe 构造处
  - [x] 1.5.2 验证无回归（运行：`python -m pytest -x -q`，确认所有测试通过）
  - [x] 1.5.3 检查：确认变更范围完整，无遗漏文件或引用

- [x] 1.6 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/quality-rework/specs/*.md` 和 `openspec/changes/quality-rework/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → 本任务组所有变更文件
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. 新增购买均价追踪

- [x] 2.1 Folk 新增 `last_avg_buy_prices` 字段并在结算时更新  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_folk.py` — 测试 Folk 有 `last_avg_buy_prices: Dict[GoodsType, float]` 属性（初始为空）；`tests/test_folk_service.py` — 测试结算后 `last_avg_buy_prices` 按成交量加权均价更新
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_folk.py tests/test_folk_service.py -x -q`，确认失败）
  - [x] 2.1.3 写最小实现：修改 `entity/folk.py` — Folk 新增 `last_avg_buy_prices: Dict[GoodsType, float] = {}`；修改 `system/folk_service.py` — `settle_trades()` 或 `buy_phase()` 结束后按成交记录计算并更新加权均价
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_folk.py tests/test_folk_service.py -x -q`，确认通过）
  - [x] 2.1.5 重构：整理代码（保持所有测试通过）

- [x] 2.2 Company（DecisionComponent）新增 `last_avg_buy_prices` 字段并在结算时更新  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_decision_service.py` — 测试 DecisionComponent 有 `last_avg_buy_prices` 属性；测试企业采购结算后加权均价正确更新
  - [x] 2.2.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py -x -q`，确认失败）
  - [x] 2.2.3 写最小实现：修改 `component/decision_component.py` — 新增 `last_avg_buy_prices: Dict[GoodsType, float] = {}`；修改企业采购结算流程，按成交记录更新加权均价
  - [x] 2.2.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py -x -q`，确认通过）
  - [x] 2.2.5 重构：整理代码（保持所有测试通过）

- [x] 2.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 3. 评分改为三维加权混合（品质 + 品牌 + 价格吸引力）+ 重命名

- [x] 3.1 实现价格吸引力 sigmoid 计算和 Folk 三维评分  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_folk_service.py` — 测试 `_score_order` 使用 `w_quality * quality + w_brand * brand_value + w_price * price_attractiveness`；测试 sigmoid 价格吸引力计算（价格低于均价 → 正值，高于均价 → 负值）；测试均价为 0 时使用 base_price 替代
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_folk_service.py -x -q`，确认失败）
  - [x] 3.1.3 写最小实现：修改 `system/folk_service.py` — `_score_order` 新增 `w_price`、`avg_price` 参数；实现 `price_attractiveness = 2 * sigmoid(k * (avg_price - price) / avg_price) - 1`；均价为 0 时用 `order.batch.goods_type.base_price` 替代；公式改为 `w_quality * quality + w_brand * brand + w_price * price_attractiveness`
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_folk_service.py -x -q`，确认通过）
  - [x] 3.1.5 重构：整理代码（保持所有测试通过）

- [x] 3.2 Folk 重命名 `w_value_for_money` → `w_quality` 并新增 `w_price`  <!-- TDD 任务 -->
  - [x] 3.2.1 写失败测试：`tests/test_folk.py` — 测试 Folk 有 `w_quality`、`w_brand`、`w_price` 三个属性
  - [x] 3.2.2 验证测试失败（运行：`python -m pytest tests/test_folk.py -x -q`，确认失败）
  - [x] 3.2.3 写最小实现：修改 `entity/folk.py` — `w_value_for_money` → `w_quality`，新增 `w_price: float`；修改 `config/folk.yaml` — 字段重命名并新增 `w_price`；修改 `load_folks()` 加载新字段
  - [x] 3.2.4 验证测试通过（运行：`python -m pytest tests/test_folk.py -x -q`，确认通过）
  - [x] 3.2.5 重构：整理代码（保持所有测试通过）

- [x] 3.3 修改企业 B2B 采购评分为三维加权混合  <!-- TDD 任务 -->
  - [x] 3.3.1 写失败测试：`tests/test_decision_service.py` — 测试 `calculate_supplier_score` 使用 `w_quality * quality + w_brand * brand_value + w_price * price_attractiveness`；测试 DecisionComponent 新增 `price_sensitivity` 特质
  - [x] 3.3.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py -x -q`，确认失败）
  - [x] 3.3.3 写最小实现：修改 `component/decision_component.py` — 新增 `price_sensitivity: float`（随机初始化 [0,1]）；修改 `system/decision_service.py` — `calculate_supplier_score` 新增 `avg_price` 参数，实现三维加权评分（品牌权重由 `marketing_awareness` 推导，价格权重由 `price_sensitivity` 推导，品质权重 = 1 - 品牌权重 - 价格权重）
  - [x] 3.3.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py -x -q`，确认通过）
  - [x] 3.3.5 重构：整理代码（保持所有测试通过）

- [x] 3.4 更新 UI 表头和剩余引用  <!-- 非 TDD 任务 -->
  - [x] 3.4.1 执行变更：修改 `system/player_service.py` — 表头 "性价比偏好" → "品质偏好"，新增 "价格偏好" 列，引用 `folk.w_value_for_money` → `folk.w_quality`；修改 `config/folk.yaml`、`tests/config_integration/folk.yaml` 同步更新
  - [x] 3.4.2 验证无回归（运行：`python -m pytest -x -q`，确认所有测试通过）
  - [x] 3.4.3 检查：确认变更范围完整，无遗漏文件或引用（全局搜索 `value_for_money` 和 `vfm` 确认无残留）

- [x] 3.5 修复所有因重命名和新字段导致的测试破损  <!-- 非 TDD 任务 -->
  - [x] 3.5.1 执行变更：更新所有引用 `w_value_for_money` 的测试文件（`tests/test_folk.py`, `tests/test_folk_service.py`, `tests/test_player_service.py`, `tests/test_decision_service.py`, `tests/test_integration.py`, `tests/test_review_regressions.py`, `tests/test_company_buy_phase.py`, `tests/test_company_buy_settlement.py`, `tests/test_market_match.py`, `tests/test_bankruptcy_service.py` 等），改用 `w_quality`、`w_price`
  - [x] 3.5.2 验证无回归（运行：`python -m pytest -x -q`，确认所有测试通过）
  - [x] 3.5.3 检查：确认变更范围完整，全局搜索 `value_for_money` 和 `w_vfm` 确认零残留

- [x] 3.6 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 4. PreCI 代码规范检查

- [x] 4.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：执行安装命令，安装完成后继续
  - 若找到：记录可用路径，直接继续
- [x] 4.2 检测项目是否已 preci 初始化
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`，等待完成后继续
- [x] 4.3 检测 PreCI Server 状态
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`，等待服务启动（最多 10 秒）
  - 若启动失败：输出警告但继续扫描流程
- [x] 4.4 执行代码规范扫描
  - 依次执行：`<preci路径> scan --diff` 和 `<preci路径> scan --pre-commit`
  - 合并两次扫描结果，去重后统一处理
  - 仅扫描代码文件
- [x] 4.5 处理扫描结果
  - 若无告警：输出 `PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多 3 次），修正后重新扫描验证

## 5. Documentation Sync (Required)

- [x] 5.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 5.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 5.3 sync proposal.md: update scope/impact if changed
- [x] 5.4 sync specs/*.md: update requirements if changed
- [x] 5.5 Final review: ensure all OpenSpec docs reflect actual implementation
