## 1. Folk 实体与配置加载

- [x] 1.1 创建 Folk 实体类与 load_folks 配置加载  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_folk.py` — 测试 Folk 实体初始化（population、w_value_for_money、w_brand、base_demands）、组件挂载（LedgerComponent、StorageComponent）；测试 load_folks 从 ConfigManager 加载 Folk 列表，验证不同 Folk 的人均基础需求不同
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_folk.py -v`，确认失败原因是缺少 Folk 类）
  - [x] 1.1.3 写最小实现：`entity/folk.py` — Folk(Entity) 类，包含 population、w_value_for_money、w_brand、base_demands 属性，初始化 LedgerComponent 和 StorageComponent；`load_folks(config: ConfigManager, goods_types: Dict[str, GoodsType]) -> List[Folk]` 工厂函数
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_folk.py -v`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 创建 folk.yaml 配置文件  <!-- 非 TDD 任务 -->
  - [x] 1.2.1 执行变更：`config/folk.yaml` — 创建居民配置文件，定义 `folks` 列表，每个条目包含 population、w_value_for_money、w_brand、base_demands（各商品的 per_capita 和 sensitivity）
  - [x] 1.2.2 验证无回归（运行：`python -m pytest tests/ -v`，确认输出干净）
  - [x] 1.2.3 检查：确认配置格式与 ConfigManager 兼容、所有终端消费品（食品/服装/手机）在配置中有定义

- [x] 1.3 创建 FolkService 骨架  <!-- TDD 任务 -->
  - [x] 1.3.1 写失败测试：`tests/test_folk_service.py` — 测试 FolkService 可实例化、持有 Folk 列表
  - [x] 1.3.2 验证测试失败（运行：`python -m pytest tests/test_folk_service.py -v`，确认失败原因是缺少 FolkService）
  - [x] 1.3.3 写最小实现：`system/folk_service.py` — FolkService 类，持有 folks: List[Folk]
  - [x] 1.3.4 验证测试通过（运行：`python -m pytest tests/test_folk_service.py -v`，确认所有测试通过，输出干净）
  - [x] 1.3.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.4 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/folk-purchasing/specs/*.md` 和 `openspec/changes/folk-purchasing/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `entity/folk.py`、`config/folk.yaml`、`system/folk_service.py`、`tests/test_folk.py`、`tests/test_folk_service.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 2. 需求计算

- [x] 2.1 实现 FolkService.compute_demands  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_folk_service.py` — 测试 compute_demands 返回每个 Folk 每种终端消费品的需求量，验证公式：population * per_capita * (1 + economy_cycle_index * sensitivity)；测试 per_capita=0 的商品返回 0；测试不同 Folk 对同一商品的需求量不同
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_folk_service.py::TestComputeDemands -v`，确认失败原因是缺少 compute_demands 方法）
  - [x] 2.1.3 写最小实现：`system/folk_service.py` — compute_demands 方法，接受经济周期指数参数，返回 Dict[Folk, Dict[GoodsType, int]]
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_folk_service.py::TestComputeDemands -v`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/folk-purchasing/specs/*.md` 和 `openspec/changes/folk-purchasing/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/folk_service.py` 中 compute_demands 相关变更、`tests/test_folk_service.py` 中需求计算测试
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 3. 加权均分采购（核心逻辑）

- [x] 3.1 实现 softmax 评分与加权分配  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_folk_service.py` — 测试单个 Folk 单商品场景：给定多个 SellOrder 和 Folk 的评分权重，验证 softmax 权重计算正确、分配量按权重比例分配；测试所有卖方库存充足时一次分配完成
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_folk_service.py::TestWeightedAllocation -v`，确认失败原因是缺少实现）
  - [x] 3.1.3 写最小实现：`system/folk_service.py` — 实现评分计算、softmax 归一化、按权重分配需求量的核心方法
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_folk_service.py::TestWeightedAllocation -v`，确认所有测试通过，输出干净）
  - [x] 3.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.2 实现迭代重分配  <!-- TDD 任务 -->
  - [x] 3.2.1 写失败测试：`tests/test_folk_service.py` — 测试卖方库存不足时的迭代重分配：卖方A库存不足→只成交库存量→剩余需求重新分配给卖方B/C；测试所有卖方售罄后剩余需求记为缺货；测试多轮迭代收敛
  - [x] 3.2.2 验证测试失败（运行：`python -m pytest tests/test_folk_service.py::TestIterativeReallocation -v`，确认失败原因是缺少迭代逻辑）
  - [x] 3.2.3 写最小实现：`system/folk_service.py` — 在分配方法中加入迭代循环：检测库存不足的卖方→收集剩余需求→移除售罄卖方→重新 softmax 分配
  - [x] 3.2.4 验证测试通过（运行：`python -m pytest tests/test_folk_service.py::TestIterativeReallocation -v`，确认所有测试通过，输出干净）
  - [x] 3.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/folk-purchasing/specs/*.md` 和 `openspec/changes/folk-purchasing/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/folk_service.py` 中加权分配和迭代重分配相关变更、`tests/test_folk_service.py` 中对应测试
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 4. 采购结算

- [x] 4.1 实现 FolkService.settle_trades  <!-- TDD 任务 -->
  - [x] 4.1.1 写失败测试：`tests/test_folk_service.py` — 测试商品从卖方 StorageComponent 扣减并入库到 Folk 的 StorageComponent；测试现金从 Folk 的 LedgerComponent 支付到卖方 LedgerComponent
  - [x] 4.1.2 验证测试失败（运行：`python -m pytest tests/test_folk_service.py::TestSettleTrades -v`，确认失败原因是缺少 settle_trades）
  - [x] 4.1.3 写最小实现：`system/folk_service.py` — settle_trades 方法，复用 CompanyService.settle_trades 的商品转移逻辑，但居民不赊账（现金不足部分暂不处理，因为现阶段现金无限）
  - [x] 4.1.4 验证测试通过（运行：`python -m pytest tests/test_folk_service.py::TestSettleTrades -v`，确认所有测试通过，输出干净）
  - [x] 4.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 4.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/folk-purchasing/specs/*.md` 和 `openspec/changes/folk-purchasing/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/folk_service.py` 中 settle_trades 相关变更、`tests/test_folk_service.py` 中结算测试
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 5. 完整采购流程集成

- [x] 5.1 实现 FolkService.buy_phase 完整流程  <!-- TDD 任务 -->
  - [x] 5.1.1 写失败测试：`tests/test_folk_service.py` — 端到端集成测试：创建多个配置不同的 Folk + 多个卖方公司 SellOrder → 调用 buy_phase → 验证各 Folk 按各自偏好权重分配到不同卖方、结算正确、SellOrder.remaining 正确扣减
  - [x] 5.1.2 验证测试失败（运行：`python -m pytest tests/test_folk_service.py::TestBuyPhase -v`，确认失败原因是缺少 buy_phase）
  - [x] 5.1.3 写最小实现：`system/folk_service.py` — buy_phase(market: MarketService, economy_cycle_index: float) 方法，串联 compute_demands → 加权分配 → 结算
  - [x] 5.1.4 验证测试通过（运行：`python -m pytest tests/test_folk_service.py::TestBuyPhase -v`，确认所有测试通过，输出干净）
  - [x] 5.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 5.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/folk-purchasing/specs/*.md` 和 `openspec/changes/folk-purchasing/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/folk_service.py` 中 buy_phase 相关变更、`tests/test_folk_service.py` 中集成测试
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 6. PreCI 代码规范检查

- [x] 6.1 检测 preci 安装状态  <!-- skip_preci: true, 跳过 -->
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：输出警告，跳过 PreCI 检查（配置 skip_preci: true）
  - 若找到：记录可用路径，直接继续
- [x] 6.2 检测项目是否已 preci 初始化  <!-- skip_preci: true, 跳过 -->
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`，等待完成后继续
- [x] 6.3 检测 PreCI Server 状态  <!-- skip_preci: true, 跳过 -->
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`，等待服务启动（最多 10 秒）
  - 若启动失败：输出警告但继续扫描流程
- [x] 6.4 执行代码规范扫描  <!-- skip_preci: true, 跳过 -->
  - 依次执行两个扫描命令：
    1. `<preci路径> scan --diff`（扫描未暂存变更）
    2. `<preci路径> scan --pre-commit`（扫描已暂存变更）
  - 合并两次扫描结果，去重后统一处理
  - 仅扫描代码文件（跳过 .md/.yml/.json/.xml/.txt/.png/.jpg 等非代码文件）
- [x] 6.5 处理扫描结果  <!-- skip_preci: true, 跳过 -->
  - 若无告警：输出 `PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多 3 次重试），修正后重新扫描验证

## 7. Documentation Sync (Required)

- [x] 7.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 7.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 7.3 sync proposal.md: update scope/impact if changed
- [x] 7.4 sync specs/*.md: update requirements if changed
- [x] 7.5 Final review: ensure all OpenSpec docs reflect actual implementation
