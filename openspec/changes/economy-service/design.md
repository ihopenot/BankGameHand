## Context

BankGameHand 是一个银行经营模拟游戏，经济周期指数是整个经济系统的外生驱动核心。当前 `EconomyService` 只有空壳实现。项目使用 Python，基于 Service 抽象基类的服务架构，ConfigManager 管理 YAML 配置。

核心类型约定：
- `Rate = int`：万分之一基点，如 0.5 对应 5000，-0.3 对应 -3000
- `Radio = float`：0.0~1.0 的比率
- `Money = int`：分为单位

## Goals / Non-Goals

**Goals:**
- 实现可扩展的经济模型架构，支持通过配置切换不同经济模型
- 完成双周期正弦波经济模型（短周期 + 长周期 + 高斯噪声）
- 提供通用注册表基础设施供项目其他模块复用
- Service 基类持有 game 引用，统一所有 Service 访问游戏状态的方式

**Non-Goals:**
- 不实现派生经济指标（标准利率、消费信心、通胀率等）
- 不实现其他经济模型（仅双周期）
- 不修改 game_loop.py 的调用逻辑

## Decisions

1. **注册表模式（Registry Pattern）** 用于经济模型扩展：通过字符串名称注册和查找模型类，便于从 YAML 配置选择模型。注册表放在 `core/registry.py` 作为通用基础设施。
2. **三层模型继承**：`BaseModel`（`core/base_model.py`）作为所有模型的通用基类，定义 `name` 和 `get_state()` 接口；`EconomyModel(BaseModel)`（`system/economy_models/__init__.py`）作为经济周期模型基类，增加 `calculate(t) -> Rate` 接口；`DualCycleModel(EconomyModel)` 为具体实现。
3. **策略委托**：EconomyService 持有 EconomyModel 实例，计算逻辑完全委托给模型，Service 只负责生命周期和状态管理。
3. **配置驱动**：所有模型参数从 `config/economy.yaml` 读取，`phase: null` 时由系统随机生成，支持 `random_seed` 固定种子用于测试复现。
4. **高斯噪声**：使用 `random.gauss(0, σ)` 实现噪声项，σ 从配置读取。
5. **Service 基类修改**：`Service.__init__(self, game)` 保存 game 引用，子类通过 `self.game` 访问当前轮次等游戏状态。
6. **AttrDict 兼容**：`DualCycleModel` 使用 `_get`/`_item` 辅助函数统一访问 `dict` 和 `AttrDict` 对象，因为 `ConfigManager` 返回的嵌套配置是 `AttrDict` 类型，不支持 `.get()` 方法。
7. **模型注册表实例位于 `economy_service.py` 模块级别**：`economy_model_registry` 在模块加载时创建并注册 `DualCycleModel`，EconomyService 初始化时直接使用。

## Risks / Trade-offs

- **Service 基类签名变更**：所有现有 Service 子类（CompanyService、MarketService 等）的构造函数需要适配。当前这些都是空壳，影响可控。
- **Rate 精度**：经济指数从 float 转为 Rate (int) 会丢失精度（万分之一），对游戏模拟足够但需注意累计误差。模型内部计算使用 float，仅最终输出转换为 Rate。
- **噪声可预测性**：固定 random_seed 时噪声序列完全确定，测试友好但需确保生产环境不固定种子。
