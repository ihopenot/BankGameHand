## Why

当前项目已完成经济周期服务（EconomyService），但核心的商品、工厂、生产流程尚未实现。商品和工厂是整个游戏经济系统的基础——公司通过工厂将原料转化为产品，产品在市场上交易。没有这些实体，采购、生产、结算等游戏阶段无法运转。

同时，项目缺少 Entity/Component 基础架构。现有的 LedgerComponent 是独立的类，没有统一的组件挂载机制。需要建立 Entity-Component 体系，为后续的 Company、Bank 等实体提供可组合的组件化架构。

## What Changes

### 新增基础架构
- **Entity 基类** — 提供 `init_component` / `get_component`，维护 `Dict[Type[BaseComponent], BaseComponent]`
- **BaseComponent 基类** — 所有组件的基类，持有 `outer: Entity` 引用

### 新增数据模型
- **GoodsType** — 商品种类定义（name, base_price, bonus_ceiling）
- **Recipe** — 配方定义（input/output 商品种类和数量，原料层 input 为 None）
- **FactoryType** — 工厂类型定义（recipe, base_production, build_cost, maintenance_cost, build_time）
- **GoodsBatch** — 商品批次运行时实例（goods_type, quantity, quality, brand_value）
- **Factory** — 工厂运行时实例（factory_type, build_remaining，生产计算逻辑）

### 新增组件
- **StorageComponent** — 库存管理（`inventory: Dict[GoodsType, List[GoodsBatch]]`）
- **ProductorComponent** — 生产者组件（tech_values, brand_values, factories），依赖 StorageComponent

### 改造
- **LedgerComponent** — 改为继承 BaseComponent
- **Company** — 改为继承 Entity，初始化时挂载 ProductorComponent

### 配置
- **config/goods.yaml** — 三条产业链（电子、纺织、食品）的商品、配方、工厂类型配置

## Impact

- 新增文件：core/entity.py, component/base_component.py, component/storage_component.py, component/productor_component.py, entity/goods.py, entity/factory.py, config/goods.yaml
- 改造文件：component/ledger_component.py, entity/company/company.py
- 现有 53 个测试不应受影响
