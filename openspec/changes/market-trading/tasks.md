## 1. MarketService 数据结构与撮合引擎

- [x] 1.1 实现 SellOrder、BuyIntent、TradeRecord 数据结构和 MarketService 类  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_market_service.py` — 测试 SellOrder 创建、MarketService.add_sell_order/get_sell_orders/clear
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_market_service.py -v`，确认失败原因是缺少模块）
  - [x] 1.1.3 写最小实现：`system/market_service.py` — SellOrder、BuyIntent、TradeRecord 数据类 + MarketService 的 add/get/clear 方法
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_market_service.py -v`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 实现逐轮匹配算法 MarketService.match()  <!-- TDD 任务 -->
  - [x] 1.2.1 写失败测试：`tests/test_market_match.py` — 测试供大于求全部成交、供小于求等比分配、多轮降级选择、终止条件（无买方/无卖方/无成交）
  - [x] 1.2.2 验证测试失败（运行：`python -m pytest tests/test_market_match.py -v`，确认失败原因是 match 方法未实现）
  - [x] 1.2.3 写最小实现：`system/market_service.py` — MarketService.match(buy_intents) 逐轮匹配算法
  - [x] 1.2.4 验证测试通过（运行：`python -m pytest tests/test_market_match.py -v`，确认所有测试通过，输出干净）
  - [x] 1.2.5 重构

- [x] 1.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/market-trading/specs/*.md` 和 `openspec/changes/market-trading/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `system/market_service.py`、`tests/test_market_service.py`、`tests/test_market_match.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. LoanType.TRADE_PAYABLE 与 Company 初始化

- [x] 2.1 新增 LoanType.TRADE_PAYABLE 并更新优先级  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_trade_payable.py` — 测试 TRADE_PAYABLE 类型存在、优先级最高（数值最小）、Loan 创建和结算
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_trade_payable.py -v`，确认失败原因是 TRADE_PAYABLE 不存在）
  - [x] 2.1.3 写最小实现：`core/types.py` — 在 LoanType 枚举中新增 TRADE_PAYABLE，在 _LOAN_TYPE_PRIORITY 中设置最高优先级
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_trade_payable.py -v`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码（保持所有测试通过）

- [x] 2.2 Company 初始化 LedgerComponent  <!-- TDD 任务 -->
  - [x] 2.2.1 写失败测试：`tests/test_company_ledger.py` — 测试 Company 实例拥有 LedgerComponent
  - [x] 2.2.2 验证测试失败（运行：`python -m pytest tests/test_company_ledger.py -v`，确认失败原因是 Company 未初始化 LedgerComponent）
  - [x] 2.2.3 写最小实现：`entity/company/company.py` — 在 Company.__init__ 中增加 `self.init_component(LedgerComponent)`
  - [x] 2.2.4 验证测试通过（运行：`python -m pytest tests/test_company_ledger.py -v`，确认所有测试通过，输出干净）
  - [x] 2.2.5 重构：整理代码（保持所有测试通过）

- [x] 2.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更，占位符映射：
    - `{PLAN_OR_REQUIREMENTS}` → `openspec/changes/market-trading/specs/*.md` 和 `openspec/changes/market-trading/tasks.md`
    - `{WHAT_WAS_IMPLEMENTED}` → `core/types.py`、`entity/company/company.py`、`tests/test_trade_payable.py`、`tests/test_company_ledger.py`
    - `{BASE_SHA}` → 任务组开始前的 commit SHA
    - `{HEAD_SHA}` → 当前 HEAD
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 3. ProductorComponent 定价属性

- [x] 3.1 在 ProductorComponent 中新增 prices 属性  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_productor_prices.py` — 测试 ProductorComponent.prices 存在、初始值等于各产出 GoodsType.base_price
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_productor_prices.py -v`，确认失败原因是 prices 属性不存在）
  - [x] 3.1.3 写最小实现：`component/productor_component.py` — 新增 `self.prices: Dict[GoodsType, Money] = {}`，在工厂注册时初始化对应产出的 base_price
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_productor_prices.py -v`，确认所有测试通过，输出干净）
  - [x] 3.1.5 重构：整理代码（保持所有测试通过）

- [x] 3.2 代码审查

## 4. CompanyService.sell_phase 实现

- [x] 4.1 实现 CompanyService.sell_phase  <!-- TDD 任务 -->
  - [x] 4.1.1 写失败测试：`tests/test_company_sell_phase.py` — 测试遍历公司库存生成 SellOrder、标价取自 ProductorComponent.prices、空库存不挂单、多 batch 独立挂单
  - [x] 4.1.2 验证测试失败（运行：`python -m pytest tests/test_company_sell_phase.py -v`，确认失败原因是 sell_phase 未实现）
  - [x] 4.1.3 写最小实现：`system/company_service.py` — CompanyService.sell_phase(market_service)
  - [x] 4.1.4 验证测试通过（运行：`python -m pytest tests/test_company_sell_phase.py -v`，确认所有测试通过，输出干净）
  - [x] 4.1.5 重构：整理代码（保持所有测试通过）

- [x] 4.2 代码审查

## 5. CompanyService.buy_phase 实现

- [x] 5.1 实现需求计算和偏好排序逻辑  <!-- TDD 任务 -->
  - [x] 5.1.1 写失败测试：`tests/test_company_buy_phase.py` — 测试需求量计算（工厂满产需求 - 现有库存）、偏好按性价比排序、需求量为 0 时不生成 BuyIntent
  - [x] 5.1.2 验证测试失败（运行：`python -m pytest tests/test_company_buy_phase.py -v`，确认失败原因是 buy_phase 未实现）
  - [x] 5.1.3 写最小实现：`system/company_service.py` — CompanyService.buy_phase(market_service) 的需求计算和偏好排序部分
  - [x] 5.1.4 验证测试通过（运行：`python -m pytest tests/test_company_buy_phase.py -v`，确认所有测试通过，输出干净）
  - [x] 5.1.5 重构：整理代码（保持所有测试通过）

- [x] 5.2 实现成交后的商品转移和支付/赊账处理  <!-- TDD 任务 -->
  - [x] 5.2.1 写失败测试：`tests/test_company_buy_settlement.py` — 测试成交后商品入买方库存、卖方 batch 扣减、现金充足时全额支付、现金不足时创建 TRADE_PAYABLE Loan
  - [x] 5.2.2 验证测试失败（运行：`python -m pytest tests/test_company_buy_settlement.py -v`，确认失败原因是结算逻辑未实现）
  - [x] 5.2.3 写最小实现：`system/company_service.py` — 成交处理逻辑（商品转移 + 现金支付/赊账）
  - [x] 5.2.4 验证测试通过（运行：`python -m pytest tests/test_company_buy_settlement.py -v`，确认所有测试通过，输出干净）
  - [x] 5.2.5 重构：整理代码（保持所有测试通过）

- [x] 5.3 代码审查

## 6. PreCI 代码规范检查

- [x] 6.1 检测 preci 安装状态
  - 按以下优先级检测：① `~/PreCI/preci`（优先）→ ② `command -v preci`（PATH）
  - 若均未找到：执行安装命令，安装完成后继续
  - 若找到：记录可用路径，直接继续
- [x] 6.2 检测项目是否已 preci 初始化
  - 检查 `.preci/`、`build.yml`、`.codecc/` 任一存在即为已初始化
  - 若未初始化：执行 `preci init`，等待完成后继续
- [x] 6.3 检测 PreCI Server 状态
  - 执行 `<preci路径> server status` 检查服务是否启动
  - 若未启动：执行 `<preci路径> server start`，等待服务启动（最多 10 秒）
  - 若启动失败：输出警告但继续扫描流程
- [x] 6.4 执行代码规范扫描
  - 依次执行两个扫描命令：
    1. `<preci路径> scan --diff`（扫描未暂存变更）
    2. `<preci路径> scan --pre-commit`（扫描已暂存变更）
  - 合并两次扫描结果，去重后统一处理
  - 仅扫描代码文件（跳过 .md/.yml/.json/.xml/.txt/.png/.jpg 等非代码文件）
- [x] 6.5 处理扫描结果
  - 若无告警：输出 `✅ PreCI 检查通过`，继续 Documentation Sync
  - 若有告警：自动修正（最多 3 次重试），修正后重新扫描验证
  - 若重试用尽后仍有无法自动修正的告警：暂停流程，输出剩余问题列表及选项，等待用户确认

## 7. Documentation Sync (Required)

- [x] 7.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 7.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 7.3 sync proposal.md: update scope/impact if changed
- [x] 7.4 sync specs/*.md: update requirements if changed
- [x] 7.5 Final review: ensure all OpenSpec docs reflect actual implementation
