## Why

当前企业部门在科研、品牌、维护上的支出是"内部消耗"，资金不会流向居民部门，导致经济循环不完整。同时，居民的购买决策逻辑硬编码在 FolkService 中，无法像企业一样通过决策组件模式灵活配置和扩展。

## What Changes

1. 企业科研、品牌、维护支出按配置比例分流到居民群体，完善经济循环
2. 将决策组件从 `component/` 顶层重组到 `component/decision/` 子包（company/ + folk/）
3. 新增居民决策组件（Base + Classic），实现支出决策 API（预算+需求量）
4. 重构 FolkService，将需求计算逻辑委托给决策组件

## Impact

- **文件迁移**：`component/base_company_decision.py`、`classic_company_decision.py`、`ai_company_decision.py` 移入 `component/decision/company/`
- **导入路径变更**：`system/decision_service.py`、`system/company_service.py`、`game/game.py`、`system/metric_service.py` 及约 15 个测试文件的 import 语句需更新
- **新增文件**：`component/decision/__init__.py`、`component/decision/company/__init__.py`、`component/decision/folk/__init__.py`、`component/decision/folk/base.py`、`component/decision/folk/classic.py`
- **配置变更**：`config/folk.yaml` 新增 `spending_flow` 配置节
- **行为变更**：`DecisionService.act_phase()` 新增维护费用实际扣款和资金分流逻辑；`FolkService.buy_phase()` 通过决策组件获取支出计划
