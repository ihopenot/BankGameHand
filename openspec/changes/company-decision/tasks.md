## 1. DecisionComponent — CEO 特质与决策状态组件

- [x] 1.1 实现 DecisionComponent 基础结构（CEO 特质字段 + 决策状态字段）  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_decision_component.py` — 测试 DecisionComponent 创建、5 维特质存储、默认值
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_decision_component.py -x`，确认失败原因是缺少 DecisionComponent）
  - [x] 1.1.3 写最小实现：`component/decision_component.py` — DecisionComponent 继承 BaseComponent，包含 5 维 CEO 特质字段和销售状态追踪字段
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_decision_component.py -x`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 Company 挂载 DecisionComponent + CEO 特质随机生成  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_decision_component.py` — 测试 Company 创建时自动挂载 DecisionComponent、特质随机生成在 [0,1] 范围
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_decision_component.py -x`，确认失败原因是 Company 未挂载 DecisionComponent）
  - [x] 1.2.3 写最小实现：修改 `entity/company/company.py` — init_component(DecisionComponent)，在 DecisionComponent 构造中随机生成特质
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_decision_component.py -x`，确认所有测试通过，输出干净）
  - [x] 1.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/company-decision/specs/company-decision.md` 和 `openspec/changes/company-decision/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `component/decision_component.py`, `entity/company/company.py`, `tests/test_decision_component.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. 决策配置系统 — decision.yaml + 配置加载

- [x] 2.1 创建 decision.yaml 配置文件  <!-- 非 TDD 任务 -->
  - [x] 2.1.1 执行变更：`config/decision.yaml` — 定义所有决策公式系数（基础利润率、涨幅系数、降幅系数、风险系数、利润系数、让利系数、噪声系数、投资阈值、品牌投入基础比例、科技投入基础比例、营销系数、科技系数、基础工资支出等）
  - [x] 2.1.2 验证无回归（运行：`python -m pytest tests/ -x`，确认输出干净）
  - [x] 2.1.3 检查：确认配置项完整覆盖 6 个决策公式所需的所有系数

- [x] 2.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/company-decision/specs/company-decision.md` 和 `openspec/changes/company-decision/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `config/decision.yaml`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 3. DecisionService — 决策一：产品定价

- [x] 3.1 实现产品定价决策逻辑  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_decision_service.py` — 测试库存售罄涨价、库存剩余降价、目标利润率计算、噪声幅度与洞察力反相关
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py::TestPricingDecision -x`，确认失败原因是缺少 DecisionService）
  - [x] 3.1.3 写最小实现：`system/decision_service.py` — DecisionService.decide_pricing()，从 decision.yaml 读取系数，按公式计算新标价并更新 ProductorComponent.prices
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py::TestPricingDecision -x`，确认所有测试通过，输出干净）
  - [x] 3.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/company-decision/specs/company-decision.md` 和 `openspec/changes/company-decision/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/decision_service.py`, `tests/test_decision_service.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 4. DecisionService — 决策三：工资发放 + 决策五：品牌投入 + 决策六：科技投入

- [x] 4.1 实现工资发放决策  <!-- TDD 任务 -->
  - [x] 4.1.1 写失败测试：`tests/test_decision_service.py` — 测试工资总额 = 基础工资支出 × 产能利用率
  - [x] 4.1.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py::TestWageDecision -x`，确认失败原因是缺少 decide_wages 方法）
  - [x] 4.1.3 写最小实现：`system/decision_service.py` — DecisionService.decide_wages()
  - [x] 4.1.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py::TestWageDecision -x`，确认所有测试通过，输出干净）
  - [x] 4.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 4.2 实现品牌投入决策  <!-- TDD 任务 -->
  - [x] 4.2.1 写失败测试：`tests/test_decision_service.py` — 测试品牌支出 = 营收 × 基础比例 × (1 + 营销意识 × 营销系数)，并验证品牌值更新
  - [x] 4.2.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py::TestBrandDecision -x`，确认失败原因是缺少 decide_brand_investment 方法）
  - [x] 4.2.3 写最小实现：`system/decision_service.py` — DecisionService.decide_brand_investment()
  - [x] 4.2.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py::TestBrandDecision -x`，确认所有测试通过，输出干净）
  - [x] 4.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 4.3 实现科技投入决策  <!-- TDD 任务 -->
  - [x] 4.3.1 写失败测试：`tests/test_decision_service.py` — 测试科技支出 = 营收 × 基础比例 × (1 + 科技重视度 × 科技系数)，并验证科技值更新
  - [x] 4.3.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py::TestTechDecision -x`，确认失败原因是缺少 decide_tech_investment 方法）
  - [x] 4.3.3 写最小实现：`system/decision_service.py` — DecisionService.decide_tech_investment()
  - [x] 4.3.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py::TestTechDecision -x`，确认所有测试通过，输出干净）
  - [x] 4.3.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 4.4 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/company-decision/specs/company-decision.md` 和 `openspec/changes/company-decision/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/decision_service.py`, `tests/test_decision_service.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 5. DecisionService — 决策四：采购偏好（修改 CompanyService）

- [x] 5.1 实现采购偏好评分计算 + 修改 CompanyService.buy_phase 排序逻辑  <!-- TDD 任务 -->
  - [x] 5.1.1 写失败测试：`tests/test_decision_service.py` — 测试供应商评分公式（w_性价比 × 性价比 + w_品牌 × 品牌值）、高营销意识偏好品牌、低营销意识偏好性价比；`tests/test_company_service.py` — 测试 buy_phase 使用 CEO 特质排序
  - [x] 5.1.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py::TestPurchasePreference tests/test_company_service.py -x`，确认失败原因是缺少 calculate_purchase_preference 方法）
  - [x] 5.1.3 写最小实现：`system/decision_service.py` — DecisionService.calculate_purchase_preference()；修改 `system/company_service.py` — buy_phase 中调用新的评分函数替代硬编码 sort_key
  - [x] 5.1.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py::TestPurchasePreference tests/test_company_service.py -x`，确认所有测试通过，输出干净）
  - [x] 5.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 5.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/company-decision/specs/company-decision.md` 和 `openspec/changes/company-decision/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/decision_service.py`, `system/company_service.py`, `tests/test_decision_service.py`, `tests/test_company_service.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 6. DecisionService — 决策二：投资扩产 + Game Loop 集成

- [x] 6.1 实现投资扩产决策逻辑  <!-- TDD 任务 -->
  - [x] 6.1.1 写失败测试：`tests/test_decision_service.py` — 测试投资意愿计算、市场前景感知偏差、现金充足时决定建厂、现金不足时放弃
  - [x] 6.1.2 验证测试失败（运行：`python -m pytest tests/test_decision_service.py::TestInvestmentDecision -x`，确认失败原因是缺少 decide_investment 方法）
  - [x] 6.1.3 写最小实现：`system/decision_service.py` — DecisionService.decide_investment()
  - [x] 6.1.4 验证测试通过（运行：`python -m pytest tests/test_decision_service.py::TestInvestmentDecision -x`，确认所有测试通过，输出干净）
  - [x] 6.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 6.2 集成 Game Loop — 填充 plan_phase 和 act_phase  <!-- TDD 任务 -->
  - [x] 6.2.1 写失败测试：`tests/test_game.py` — 测试 plan_phase 调用 DecisionService 执行定价/工资/品牌/科技决策；act_phase 调用投资决策执行建厂
  - [x] 6.2.2 验证测试失败（运行：`python -m pytest tests/test_game.py -x`，确认失败原因是 plan_phase/act_phase 仍为空）
  - [x] 6.2.3 写最小实现：修改 `game/game.py` — plan_phase 中遍历公司执行决策一三五六，act_phase 中遍历公司执行决策二；Game.__init__ 中创建 DecisionService
  - [x] 6.2.4 验证测试通过（运行：`python -m pytest tests/test_game.py -x`，确认所有测试通过，输出干净）
  - [x] 6.2.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 6.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/company-decision/specs/company-decision.md` 和 `openspec/changes/company-decision/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/decision_service.py`, `game/game.py`, `tests/test_decision_service.py`, `tests/test_game.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后追加选项提示，停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 7. PreCI 代码规范检查

- [x] 7.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：执行本技能 "PreCI 代码规范检查规范" 节中的安装命令，安装完成后继续
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
  - 若有告警：自动修正（最多重试 3 次），修正后重新扫描验证
  - 若重试用尽后仍有无法自动修正的告警且 `skip_preci: false`：暂停流程，输出剩余问题列表并等待用户确认

## 8. Documentation Sync (Required)

- [x] 8.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 8.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 8.3 sync proposal.md: update scope/impact if changed
- [x] 8.4 sync specs/*.md: update requirements if changed
- [x] 8.5 Final review: ensure all OpenSpec docs reflect actual implementation
