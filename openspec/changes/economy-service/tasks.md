## 1. 基础设施

- [x] 1.1 实现通用注册表 `core/registry.py`  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_registry.py`
  - [x] 1.1.2 验证测试失败（运行：`pytest tests/test_registry.py -v`，确认失败原因是缺少 Registry 类）
  - [x] 1.1.3 写最小实现：`core/registry.py`
  - [x] 1.1.4 验证测试通过（运行：`pytest tests/test_registry.py -v`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 实现模型通用基类 `core/base_model.py`  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_base_model.py`（测试 ABC 不可直接实例化、子类必须实现 name 和 get_state）
  - [x] 1.2.2 验证测试失败（运行：`pytest tests/test_base_model.py -v`，确认失败原因是缺少 BaseModel）
  - [x] 1.2.3 写最小实现：`core/base_model.py`
  - [x] 1.2.4 验证测试通过（运行：`pytest tests/test_base_model.py -v`，确认所有测试通过，输出干净）
  - [x] 1.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.3 修改 Service 基类持有 game 引用 `system/service.py`  <!-- 非 TDD 任务 -->
  - [x] 1.3.1 执行变更：`system/service.py`
  - [x] 1.3.2 验证无回归（运行：`pytest -v`，确认输出干净）
  - [x] 1.3.3 检查：确认变更范围完整，无遗漏文件或引用

- [x] 1.4 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/economy-service/specs/*.md` 和 `openspec/changes/economy-service/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `core/registry.py`, `core/base_model.py`, `system/service.py`, `tests/test_registry.py`, `tests/test_base_model.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 2. 经济模型框架与双周期实现

- [x] 2.1 实现经济模型抽象基类 `system/economy_models/__init__.py`  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_economy_models.py`（测试 ABC 不可直接实例化、子类必须实现接口）
  - [x] 2.1.2 验证测试失败（运行：`pytest tests/test_economy_models.py -v`，确认失败原因是缺少 EconomyModel）
  - [x] 2.1.3 写最小实现：`system/economy_models/__init__.py`
  - [x] 2.1.4 验证测试通过（运行：`pytest tests/test_economy_models.py -v`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 实现双周期正弦波模型 `system/economy_models/dual_cycle_model.py`  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_dual_cycle_model.py`（测试正常计算、clamp、相位随机/指定、固定种子复现、get_state）
  - [x] 2.2.2 验证测试失败（运行：`pytest tests/test_dual_cycle_model.py -v`，确认失败原因是缺少 DualCycleModel）
  - [x] 2.2.3 写最小实现：`system/economy_models/dual_cycle_model.py`
  - [x] 2.2.4 验证测试通过（运行：`pytest tests/test_dual_cycle_model.py -v`，确认所有测试通过，输出干净）
  - [x] 2.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/economy-service/specs/*.md` 和 `openspec/changes/economy-service/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/economy_models/__init__.py`, `system/economy_models/dual_cycle_model.py`, `tests/test_economy_models.py`, `tests/test_dual_cycle_model.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 3. EconomyService 集成

- [x] 3.1 创建经济配置文件 `config/economy.yaml`  <!-- 非 TDD 任务 -->
  - [x] 3.1.1 执行变更：`config/economy.yaml`
  - [x] 3.1.2 验证无回归（运行：`pytest -v`，确认输出干净）
  - [x] 3.1.3 检查：确认配置结构与 design.md 一致

- [x] 3.2 实现 EconomyService `system/economy_service.py`  <!-- TDD 任务 -->
  - [x] 3.2.1 写失败测试：`tests/test_economy_service.py`（测试初始化加载模型、update_pahse 更新 economy_index）
  - [x] 3.2.2 验证测试失败（运行：`pytest tests/test_economy_service.py -v`，确认失败原因是 EconomyService 未实现）
  - [x] 3.2.3 写最小实现：`system/economy_service.py`
  - [x] 3.2.4 验证测试通过（运行：`pytest tests/test_economy_service.py -v`，确认所有测试通过，输出干净）
  - [x] 3.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/economy-service/specs/*.md` 和 `openspec/changes/economy-service/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `config/economy.yaml`, `system/economy_service.py`, `tests/test_economy_service.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD

## 5. PreCI 代码规范检查

- [x] 5.1 检测 preci 安装状态
- [x] 5.2 检测项目是否已 preci 初始化
- [x] 5.3 检测 PreCI Server 状态
- [x] 5.4 执行代码规范扫描
- [x] 5.5 处理扫描结果

## 6. Documentation Sync (Required)

- [x] 6.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 6.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 6.3 sync proposal.md: update scope/impact if changed
- [x] 6.4 sync specs/*.md: update requirements if changed
- [x] 6.5 Final review: ensure all OpenSpec docs reflect actual implementation
