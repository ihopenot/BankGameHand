## Why

当前企业决策系统将所有逻辑硬编码在 `DecisionService` 中，CEO 特质存储在 `DecisionComponent` 中。
这种结构无法支持不同的决策策略（如 AI 驱动的决策），且决策逻辑与状态分离在不同层级。

需要将决策封装为可替换的组件，支持经典公式驱动和 AI 驱动两种决策模式。

## What Changes

1. **新建 `BaseCompanyDecisionComponent` 抽象基类** — 合并原 `DecisionComponent`（CEO 特质）与决策 API，定义 `set_context()` + 5 个决策方法
2. **迁移 `ClassicCompanyDecisionComponent`** — 将 `DecisionService` 中的公式逻辑迁移为组件方法
3. **新增 `AICompanyDecisionComponent`** — 继承 Classic，覆写定价/投资计划/贷款需求 3 个决策，通过 MCPAgentSDK 调用 LLM
4. **重构 `DecisionService`** — 变为轻量编排层，负责组装 context dict 并调用组件方法
5. **删除 `DecisionComponent`** — CEO 特质合并入基类

## Impact

- **删除文件**: `component/decision_component.py`
- **新增文件**: `component/base_company_decision.py`, `component/classic_company_decision.py`, `component/ai_company_decision.py`
- **重写文件**: `system/decision_service.py`
- **修改文件**: `entity/company/company.py`, `game/game.py`, `system/company_service.py`
- **新增依赖**: `mcp-agent-sdk`（AI 决策模块）
- **测试文件**: `tests/test_decision_component.py`, `tests/test_decision_service.py` 需重写
- **影响的调用方**: 所有引用 `DecisionComponent` 的代码需迁移至 `BaseCompanyDecisionComponent`
