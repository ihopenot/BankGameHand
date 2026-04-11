## ADDED Requirements

### Requirement: Entity-Component 基础架构

Entity 基类提供组件化挂载机制，BaseComponent 基类持有 outer 引用。

#### Scenario: 初始化组件
- **WHEN** 调用 `entity.init_component(SomeComponent)`
- **THEN** 创建 SomeComponent 实例（outer=entity），存入 entity 的组件字典

#### Scenario: 重复初始化同类型组件
- **WHEN** 调用 `entity.init_component(SomeComponent)` 且该类型已存在
- **THEN** 跳过创建，返回已有实例

#### Scenario: 获取组件
- **WHEN** 调用 `entity.get_component(SomeComponent)` 且该类型已初始化
- **THEN** 返回对应的组件实例

#### Scenario: 获取不存在的组件
- **WHEN** 调用 `entity.get_component(SomeComponent)` 且该类型未初始化
- **THEN** 抛出异常

#### Scenario: 组件依赖拉起
- **WHEN** ComponentA 的 `__init__` 中调用 `outer.init_component(ComponentB)`
- **THEN** ComponentB 被自动创建并挂载到同一 Entity 上，ComponentA 可通过 `outer.get_component(ComponentB)` 获取引用

### Requirement: GoodsType 商品种类定义

静态配置数据，定义商品的基本属性。

#### Scenario: 创建商品种类
- **WHEN** 创建 GoodsType(name="芯片", base_price=5000, bonus_ceiling=0.8)
- **THEN** 商品种类具有 name、base_price(Money)、bonus_ceiling(Radio) 属性

### Requirement: Recipe 配方定义

定义输入输出转化关系，供应链由 Recipe 链条隐式形成。

#### Scenario: 创建中间品配方
- **WHEN** 创建 Recipe(input_goods_type=硅, input_quantity=200, output_goods_type=芯片, output_quantity=100)
- **THEN** 配方定义了从硅到芯片的转化关系和数量比

#### Scenario: 创建原料配方
- **WHEN** 创建 Recipe(input_goods_type=None, input_quantity=0, output_goods_type=硅, output_quantity=100)
- **THEN** 配方无需输入，直接产出原料

### Requirement: FactoryType 工厂类型定义

定义工厂的产能和经济属性。

#### Scenario: 创建工厂类型
- **WHEN** 创建 FactoryType(recipe=芯片配方, base_production=10, build_cost=100000, maintenance_cost=5000, build_time=3)
- **THEN** 工厂类型关联配方，具有产能、造价、维护成本、建造时间属性

### Requirement: GoodsBatch 商品批次

运行时实例，代表一批具体的商品。

#### Scenario: 创建商品批次
- **WHEN** 工厂生产出一批商品
- **THEN** 生成 GoodsBatch(goods_type, quantity, quality(Radio), brand_value)

### Requirement: Factory 工厂实例与生产计算

工厂运行时实例，包含建造状态和生产逻辑。

#### Scenario: 工厂在建
- **WHEN** Factory 的 build_remaining > 0
- **THEN** `is_built` 返回 False，无法生产

#### Scenario: 建造进度推进
- **WHEN** 调用 `tick_build()` 且 build_remaining > 0
- **THEN** build_remaining 减 1

#### Scenario: 正常生产（非原料层）
- **WHEN** 工厂已建成，提供输入原料批次和 tech_rank_ratio
- **THEN** 产出量 = base_production × output_quantity × 原料充足率 × 良品率加成
- **AND** 良品率加成 = 1 + 原料品质 × bonus_ceiling
- **AND** 产出品质 = tech_rank_ratio（由 ProductorComponent 计算并贴到产出上）

#### Scenario: 原料层生产
- **WHEN** 工厂配方的 input_goods_type 为 None
- **THEN** 产出量 = base_production × output_quantity（不受原料充足率影响）
- **AND** 产出品质 = tech_rank_ratio（由 ProductorComponent 计算并贴到产出上）

#### Scenario: 原料不足时减产
- **WHEN** 实际采购量 < 满产需求量（recipe.input_quantity × base_production）
- **THEN** 原料充足率 = 实际采购量 / 满产需求量，产出按比例减少

### Requirement: StorageComponent 库存组件

管理实体的商品库存。

#### Scenario: 存入商品批次
- **WHEN** 向 StorageComponent 存入 GoodsBatch
- **THEN** 批次按 GoodsType 分组存入 inventory

#### Scenario: 查询库存
- **WHEN** 查询某 GoodsType 的库存
- **THEN** 返回该类型的所有 GoodsBatch 列表

### Requirement: ProductorComponent 生产者组件

管理公司的生产能力，依赖 StorageComponent。

#### Scenario: 初始化时拉起依赖
- **WHEN** ProductorComponent 被 init_component 创建
- **THEN** 自动调用 outer.init_component(StorageComponent)，并保存 storage 引用

#### Scenario: 科技值按 Recipe 独立
- **WHEN** 公司在不同 Recipe 上投入科技
- **THEN** tech_values 按 Recipe 独立记录

#### Scenario: 品牌值按 GoodsType 独立
- **WHEN** 公司在不同商品上投入品牌
- **THEN** brand_values 按 GoodsType 独立记录

### Requirement: LedgerComponent 改造

继承 BaseComponent，保留原有字段。

#### Scenario: 创建 LedgerComponent
- **WHEN** 通过 entity.init_component(LedgerComponent) 创建
- **THEN** 具有 outer 引用，同时保留 cash、loans、deposit 字段

### Requirement: Company 实体

继承 Entity，组合 ProductorComponent 和 StorageComponent。

#### Scenario: 创建 Company
- **WHEN** 创建 Company 实例
- **THEN** 自动初始化 ProductorComponent（进而拉起 StorageComponent）
- **AND** 可通过 get_component 获取两个组件

### Requirement: 商品配置加载

从 YAML 配置文件加载三条产业链的商品、配方、工厂类型。

#### Scenario: 加载配置
- **WHEN** 读取 config/goods.yaml
- **THEN** 能获取三条产业链（电子、纺织、食品）的完整配置
- **AND** 包含 9 种 GoodsType、9 个 Recipe、9 个 FactoryType
