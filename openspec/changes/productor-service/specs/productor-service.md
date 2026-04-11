## ADDED Requirements

### Requirement: BaseComponent 实例追踪

每个 BaseComponent 子类维护一个 `components` 类变量，自动追踪该类的所有实例。

#### Scenario: 组件创建时自动注册
- **WHEN** 创建一个 BaseComponent 子类的实例
- **THEN** 该实例自动被添加到对应子类的 `components` 列表中

#### Scenario: 子类之间实例隔离
- **WHEN** 分别创建 StorageComponent 和 ProductorComponent 的实例
- **THEN** `StorageComponent.components` 只包含 StorageComponent 实例，`ProductorComponent.components` 只包含 ProductorComponent 实例

#### Scenario: 父类不收集子类实例
- **WHEN** 创建任意 BaseComponent 子类实例
- **THEN** `BaseComponent.components` 不包含该实例（每个子类有独立的 `components` 列表）

### Requirement: Entity 注销机制

Entity 提供 `destroy()` 方法，注销所有已注册组件，防止内存泄漏。

#### Scenario: destroy 清理所有组件注册
- **WHEN** 对一个持有 ProductorComponent（及其依赖的 StorageComponent）的 Entity 调用 `destroy()`
- **THEN** 对应组件从各自子类的 `components` 列表中移除，Entity 的 `_components` 注册表被清空

#### Scenario: destroy 后组件不可访问
- **WHEN** Entity 已调用 `destroy()`
- **THEN** 对该 Entity 调用 `get_component()` 返回 `None`

#### Scenario: destroy 幂等
- **WHEN** 对同一 Entity 连续调用两次 `destroy()`
- **THEN** 第二次调用不报错，无副作用

### Requirement: ProductorService

独立 Service，通过 BaseComponent.components 遍历所有 ProductorComponent 实例执行生产相关 phase。

#### Scenario: update_phase 更新全局 max_tech
- **WHEN** 存在多个公司各自持有 ProductorComponent，且各自有不同的 tech_values
- **THEN** ProductorService.update_phase() 调用后，ProductorComponent.max_tech 反映所有公司中每个 recipe 的最大科技值

#### Scenario: product_phase 执行所有公司的生产
- **WHEN** 存在多个公司各自持有工厂和原料
- **THEN** ProductorService.product_phase() 调用后，每个公司的生产流程被执行，产出存入各自的 StorageComponent

#### Scenario: 无 ProductorComponent 时 phase 无副作用
- **WHEN** ProductorComponent.components 为空列表
- **THEN** ProductorService.update_phase() 和 product_phase() 正常返回，无异常
