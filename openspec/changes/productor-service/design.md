## Context

BankGameHand 使用 ECS 架构，组件通过 Entity 注册和访问。当前 BaseComponent 没有全局实例追踪，ProductorComponent 已有类变量 `max_tech` 用于跨实体比较。Service 层已有 EconomyService 作为范例，其他 Service 仍为 stub。Game 的 `product_phase` 通过 `company_service.product_phase()` 调用，但尚无实际生产编排。

## Goals / Non-Goals

**Goals:**
- 在 BaseComponent 层实现通用的实例追踪机制（`components` 类变量 + `__init_subclass__`）
- 为 Entity 实现 `destroy()` 方法，确保组件注销和内存安全
- 实现 ProductorService 作为独立 Service，编排所有 ProductorComponent 的 update_phase 和 product_phase
- 所有接口使用严格类型注释

**Non-Goals:**
- 不实现科技值增长逻辑（仅遍历调用 `update_max_tech()`）
- 不修改 Game 类的 phase 调用方式（ProductorService 不接入 Game 主循环）
- 不实现其他 Service（MarketService、FolkService 等）

## Decisions

1. **`__init_subclass__` 钩子**：在 BaseComponent 中使用 `__init_subclass__` 为每个子类自动创建独立的 `components: ClassVar[List[BaseComponent]]` 列表。这比要求每个子类手动声明更安全，避免遗漏。
2. **注册/注销位置**：`__init__` 中自动注册到 `type(self).components`；Entity.`destroy()` 中遍历组件并调用 `type(comp).components.remove(comp)`，然后清空 `_components` 字典。
3. **ProductorService 作为独立 Service**：不依赖 CompanyService，直接通过 `ProductorComponent.components` 获取所有实例。这保持了松耦合，且与 `max_tech` 类变量的全局模式一致。
4. **严格类型标注**：所有函数签名（参数+返回值）、类变量、实例变量均添加完整类型注释。
5. **`get_component` 返回 `Optional[T]`**：原实现在组件不存在时抛 `KeyError`，改为返回 `None`，配合 `destroy()` 后的查询语义更合理。既有代码均在确认初始化后调用，运行时行为无变化。

## Risks / Trade-offs

- **全局状态**：`components` 类变量是全局可变状态，测试中需要在 setup/teardown 清理。与已有的 `max_tech` 全局类变量面临相同问题，测试套件已有清理先例。
- **弱引用 vs 强引用**：当前选择强引用（`List`），依赖 `destroy()` 手动清理。如果将来实体生命周期管理更复杂，可考虑 `WeakSet`，但当前阶段强引用 + 显式 destroy 更直观。
