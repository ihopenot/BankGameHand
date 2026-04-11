## 1. Entity/Component 基础架构

- [x] 1.1 实现 BaseComponent 和 Entity 基类  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_entity.py` — 测试 Entity 的 init_component、get_component、重复初始化跳过、获取不存在组件抛异常、组件依赖拉起
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest ./tests/test_entity.py`，确认失败原因是缺少功能）
  - [x] 1.1.3 写最小实现：`component/base_component.py`（BaseComponent）、`core/entity.py`（Entity）
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest ./tests/test_entity.py`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 改造 LedgerComponent 继承 BaseComponent  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_ledger_component.py` — 测试 LedgerComponent 继承 BaseComponent、通过 Entity 挂载、outer 引用正确
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest ./tests/test_ledger_component.py`，确认失败原因是缺少功能）
  - [x] 1.2.3 写最小实现：修改 `component/ledger_component.py`
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest ./tests/test_ledger_component.py`，确认所有测试通过，输出干净）
  - [x] 1.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/goods-and-factory/specs/*.md` 和 `openspec/changes/goods-and-factory/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `core/entity.py`, `component/base_component.py`, `component/ledger_component.py`, `tests/test_entity.py`, `tests/test_ledger_component.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 2. 商品数据模型（GoodsType + GoodsBatch）

- [x] 2.1 实现 GoodsType 和 GoodsBatch  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_goods.py` — 测试 GoodsType 属性（name, base_price, bonus_ceiling）、GoodsBatch 属性（goods_type, quantity, quality, brand_value）
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest ./tests/test_goods.py`，确认失败原因是缺少功能）
  - [x] 2.1.3 写最小实现：`entity/goods.py`
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest ./tests/test_goods.py`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 3. Recipe 和 FactoryType 数据模型

- [x] 3.1 实现 Recipe 和 FactoryType  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_factory.py` — 测试 Recipe 属性（input/output goods_type 和 quantity，原料层 input 为 None）、FactoryType 属性（recipe, base_production, build_cost, maintenance_cost, build_time）
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest ./tests/test_factory.py`，确认失败原因是缺少功能）
  - [x] 3.1.3 写最小实现：`entity/factory.py`
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest ./tests/test_factory.py`，确认所有测试通过，输出干净）
  - [x] 3.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 4. Factory 实例与生产计算

- [x] 4.1 实现 Factory 运行时实例（建造状态 + 生产逻辑）  <!-- TDD 任务 -->
  - [x] 4.1.1 写失败测试：`tests/test_factory.py`（追加）— 测试 Factory 建造状态（is_built, tick_build）、正常生产（产出量公式、良品率加成）、原料层生产、原料不足减产、产出品质计算
  - [x] 4.1.2 验证测试失败（运行：`python -m pytest ./tests/test_factory.py`，确认失败原因是缺少功能）
  - [x] 4.1.3 写最小实现：`entity/factory.py`（追加 Factory 类）
  - [x] 4.1.4 验证测试通过（运行：`python -m pytest ./tests/test_factory.py`，确认所有测试通过，输出干净）
  - [x] 4.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 4.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 5. StorageComponent 和 ProductorComponent

- [x] 5.1 实现 StorageComponent  <!-- TDD 任务 -->
  - [x] 5.1.1 写失败测试：`tests/test_components.py` — 测试 StorageComponent 存入批次、按 GoodsType 查询库存
  - [x] 5.1.2 验证测试失败（运行：`python -m pytest ./tests/test_components.py`，确认失败原因是缺少功能）
  - [x] 5.1.3 写最小实现：`component/storage_component.py`
  - [x] 5.1.4 验证测试通过（运行：`python -m pytest ./tests/test_components.py`，确认所有测试通过，输出干净）
  - [x] 5.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 5.2 实现 ProductorComponent  <!-- TDD 任务 -->
  - [x] 5.2.1 写失败测试：`tests/test_components.py`（追加）— 测试初始化时自动拉起 StorageComponent、tech_values 按 Recipe 独立、brand_values 按 GoodsType 独立、factories 列表、storage 引用正确
  - [x] 5.2.2 验证测试失败（运行：`python -m pytest ./tests/test_components.py`，确认失败原因是缺少功能）
  - [x] 5.2.3 写最小实现：`component/productor_component.py`
  - [x] 5.2.4 验证测试通过（运行：`python -m pytest ./tests/test_components.py`，确认所有测试通过，输出干净）
  - [x] 5.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 5.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 6. Company 实体改造

- [x] 6.1 改造 Company 继承 Entity，挂载组件  <!-- TDD 任务 -->
  - [x] 6.1.1 写失败测试：`tests/test_company.py` — 测试 Company 继承 Entity、创建时自动初始化 ProductorComponent 和 StorageComponent、可通过 get_component 获取两个组件
  - [x] 6.1.2 验证测试失败（运行：`python -m pytest ./tests/test_company.py`，确认失败原因是缺少功能）
  - [x] 6.1.3 写最小实现：修改 `entity/company/company.py`
  - [x] 6.1.4 验证测试通过（运行：`python -m pytest ./tests/test_company.py`，确认所有测试通过，输出干净）
  - [x] 6.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 6.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 7. 商品配置（YAML）

- [x] 7.1 创建 goods.yaml 配置文件  <!-- 非 TDD 任务 -->
  - [x] 7.1.1 执行变更：`config/goods.yaml` — 定义三条产业链（电子、纺织、食品）的 GoodsType、Recipe、FactoryType
  - [x] 7.1.2 验证无回归（运行：`python -m pytest ./tests`，确认输出干净）
  - [x] 7.1.3 检查：确认变更范围完整，三条产业链各 3 种商品、3 个配方、3 个工厂类型

- [x] 7.2 实现配置加载逻辑  <!-- TDD 任务 -->
  - [x] 7.2.1 写失败测试：`tests/test_goods_config.py` — 测试从 goods.yaml 加载 GoodsType、Recipe、FactoryType 实例
  - [x] 7.2.2 验证测试失败（运行：`python -m pytest ./tests/test_goods_config.py`，确认失败原因是缺少功能）
  - [x] 7.2.3 写最小实现：在 `entity/goods.py` 或 `entity/factory.py` 中添加配置加载函数
  - [x] 7.2.4 验证测试通过（运行：`python -m pytest ./tests/test_goods_config.py`，确认所有测试通过，输出干净）
  - [x] 7.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 7.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更

## 8. PreCI 代码规范检查

- [x] 8.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：跳过（非内网环境）
  - 若找到：记录可用路径，直接继续
- [x] 8.2 检测项目是否已 preci 初始化
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`
- [x] 8.3 检测 PreCI Server 状态
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`
- [x] 8.4 执行代码规范扫描
  - 依次执行：`<preci路径> scan --diff` 和 `<preci路径> scan --pre-commit`
  - 仅扫描代码文件
- [x] 8.5 处理扫描结果
  - 若无告警：输出 `PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多 3 次重试）

## 9. Documentation Sync (Required)

- [x] 9.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 9.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 9.3 sync proposal.md: update scope/impact if changed
- [x] 9.4 sync specs/*.md: update requirements if changed
- [x] 9.5 Final review: ensure all OpenSpec docs reflect actual implementation
