## 1. BaseComponent 实例追踪 + Entity 注销

- [x] 1.1 BaseComponent 添加 `components` 类变量和 `__init_subclass__` 自动注册  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_entity.py` — 测试子类创建后 `SubComponent.components` 包含实例；测试不同子类的 `components` 互相隔离；测试 `BaseComponent.components` 不收集子类实例
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_entity.py -q`，确认失败原因是 BaseComponent 无 `components` 属性或列表为空）
  - [x] 1.1.3 写最小实现：`component/base_component.py` — 添加 `components: ClassVar[List[Self]]`，`__init_subclass__` 钩子初始化子类列表，`__init__` 中注册
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_entity.py -q`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 Entity 添加 `destroy()` 方法  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_entity.py` — 测试 `destroy()` 后组件从对应子类 `components` 中移除；测试 `destroy()` 后 `get_component()` 返回 `None`；测试 `destroy()` 幂等性
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_entity.py -q`，确认失败原因是 Entity 无 `destroy` 方法）
  - [x] 1.2.3 写最小实现：`core/entity.py` — 添加 `destroy()` 方法，遍历 `_components` 执行注销并清空
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_entity.py -q`，确认所有测试通过，输出干净）
  - [x] 1.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/productor-service/specs/*.md` 和 `openspec/changes/productor-service/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `component/base_component.py`、`core/entity.py`、`tests/test_entity.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 2. ProductorService 实现

- [x] 2.1 创建 ProductorService，实现 `update_phase` 和 `product_phase`  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_productor_service.py` — 测试 `update_phase()` 遍历所有 ProductorComponent 更新 max_tech；测试 `product_phase()` 遍历所有 ProductorComponent 执行 produce_all；测试无 ProductorComponent 时两个 phase 无异常
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_productor_service.py -q`，确认失败原因是模块不存在）
  - [x] 2.1.3 写最小实现：`system/productor_service.py` — 继承 Service，实现 `update_phase` 和 `product_phase`，其余 phase 为空
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_productor_service.py -q`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/productor-service/specs/*.md` 和 `openspec/changes/productor-service/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/productor_service.py`、`tests/test_productor_service.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 3. 集成测试

- [x] 3.1 在集成测试中添加 ProductorService 测试用例  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_integration.py` — 测试 Game 完整循环中 ProductorService 的 update_phase 和 product_phase 被正确调用；测试多公司场景下生产流程端到端正确
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_integration.py -q`，确认失败原因是 _GameForTest 未集成 ProductorService）
  - [x] 3.1.3 写最小实现：`tests/test_integration.py` — 更新 `_GameForTest` 集成 ProductorService，添加测试场景
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_integration.py -q`，确认所有测试通过，输出干净）
  - [x] 3.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/productor-service/specs/*.md` 和 `openspec/changes/productor-service/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `tests/test_integration.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 4. PreCI 代码规范检查

- [x] 4.1 检测 preci 安装状态
- [x] 4.2 检测项目是否已 preci 初始化
- [x] 4.3 检测 PreCI Server 状态
- [x] 4.4 执行代码规范扫描
- [x] 4.5 处理扫描结果

## 5. Documentation Sync (Required)

- [x] 5.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 5.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 5.3 sync proposal.md: update scope/impact if changed
- [x] 5.4 sync specs/*.md: update requirements if changed
- [x] 5.5 Final review: ensure all OpenSpec docs reflect actual implementation
