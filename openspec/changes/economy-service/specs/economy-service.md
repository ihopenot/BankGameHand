## ADDED Requirements

### Requirement: 通用注册表

提供通用的类注册表机制，支持按字符串名称注册类并实例化对象。

#### Scenario: 注册并创建实例
- **WHEN** 使用 `register(name, cls)` 注册一个类后调用 `create(name, **kwargs)`
- **THEN** 返回该类的实例，kwargs 传递给构造函数

#### Scenario: 装饰器注册
- **WHEN** 使用 `@registry.register("name")` 装饰一个类
- **THEN** 该类被注册到注册表中，装饰器返回原始类不做修改

#### Scenario: 创建未注册的模型
- **WHEN** 调用 `create(name)` 且 name 未注册
- **THEN** 抛出 `KeyError` 异常

#### Scenario: 查询可用模型
- **WHEN** 调用 `available()`
- **THEN** 返回所有已注册名称的列表

### Requirement: 模型基类

定义所有模型（经济模型、未来其他模型）的通用抽象基类。

#### Scenario: BaseModel 接口
- **WHEN** 实现 `BaseModel` 抽象基类
- **THEN** 必须提供 `name` 抽象属性（返回模型标识符字符串）和 `get_state() -> dict` 抽象方法（返回内部状态）

#### Scenario: BaseModel 不可直接实例化
- **WHEN** 尝试直接实例化 `BaseModel`
- **THEN** 抛出 `TypeError`

### Requirement: 经济周期模型抽象接口

定义经济周期模型的标准接口，继承自 BaseModel。

#### Scenario: EconomyModel 接口
- **WHEN** 实现 `EconomyModel(BaseModel)` 抽象基类
- **THEN** 除继承 `name` 和 `get_state()` 外，还必须提供 `calculate(t: int) -> Rate` 抽象方法（返回经济周期指数）

#### Scenario: EconomyModel 不可直接实例化
- **WHEN** 尝试直接实例化 `EconomyModel`
- **THEN** 抛出 `TypeError`

### Requirement: 双周期正弦波经济模型

实现设计文档中的双周期经济模型，公式：`economy_index(t) = clamp(A1*sin(2π*t/T1+φ1) + A2*sin(2π*t/T2+φ2) + noise(t), -1.0, +1.0)`

#### Scenario: 正常计算
- **WHEN** 调用 `calculate(t)` 传入轮次 t
- **THEN** 返回 Rate 类型的经济周期指数，值域为 [-10000, +10000]（对应 -1.0 到 +1.0）

#### Scenario: 结果钳制
- **WHEN** 双周期叠加加噪声后原始值超出 [-1.0, +1.0]
- **THEN** 结果被 clamp 到 [-1.0, +1.0] 范围内再转换为 Rate

#### Scenario: 相位随机生成
- **WHEN** 配置中 `phase: null`
- **THEN** 模型初始化时随机生成 [0, 2π) 范围的相位值

#### Scenario: 相位指定
- **WHEN** 配置中 `phase` 为具体数值
- **THEN** 使用配置指定的相位值

#### Scenario: 固定随机种子
- **WHEN** 配置中 `random_seed` 为具体数值
- **THEN** 使用该种子初始化随机数生成器，确保结果可复现

#### Scenario: 状态查询
- **WHEN** 调用 `get_state()`
- **THEN** 返回包含当前轮次、原始浮点值、短周期分量、长周期分量、噪声值的字典

### Requirement: EconomyService 实现

EconomyService 从配置加载经济模型并在每轮更新经济周期指数。

#### Scenario: 服务初始化
- **WHEN** EconomyService 初始化时
- **THEN** 从 ConfigManager 读取 economy 配置，通过注册表按模型名称创建模型实例

#### Scenario: 更新经济周期
- **WHEN** 调用 `update_pahse()` 时
- **THEN** 通过 `self.game.round` 获取当前轮次，调用模型计算并更新 `economy_index`

### Requirement: Service 基类持有 Game 引用

所有 Service 子类通过基类持有对 Game 对象的引用。

#### Scenario: Service 构造
- **WHEN** 创建 Service 子类实例时传入 game 对象
- **THEN** 可通过 `self.game` 访问游戏状态（如 `self.game.round`）
