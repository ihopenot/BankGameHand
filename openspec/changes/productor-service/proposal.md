## Why

当前项目缺少 Service 层对生产流程的编排能力。ProductorComponent 已实现单个实体的生产逻辑，但没有 Service 负责在每回合遍历所有生产者执行 update_phase（更新全局 max_tech）和 product_phase（执行生产）。同时 BaseComponent 没有全局实例追踪机制，无法高效遍历某类组件的所有实例。

## What Changes

1. **BaseComponent 添加 `components` 类变量**：每个子类自动维护实例列表，组件创建时自动注册
2. **Entity 添加 `destroy()` 方法**：注销所有组件引用，防止内存泄漏
3. **新增 ProductorService**：独立 Service，实现 `update_phase`（遍历所有 ProductorComponent 调用 `update_max_tech()`）和 `product_phase`（遍历所有 ProductorComponent 调用 `produce_all()`）
4. **集成测试**：覆盖 ProductorService 的两个 phase 和 Entity.destroy() 的清理逻辑

## Impact

- `component/base_component.py` — 添加 `__init_subclass__` 和 `components` 类变量
- `core/entity.py` — 添加 `destroy()` 方法
- `system/productor_service.py` — 新增文件
- `tests/test_integration.py` — 新增测试用例
- `tests/test_components.py` / `tests/test_entity.py` — 新增组件注册/注销测试
