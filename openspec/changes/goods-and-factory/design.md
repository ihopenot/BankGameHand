## Context

BankGameHand 是一个银行模拟游戏，采用 Service 架构 + 8 阶段主循环。目前已实现：
- ConfigManager（YAML 配置加载）
- Registry（泛型注册模式）
- BaseModel（模型抽象基类）
- EconomyService + DualCycleModel（经济周期）
- Service 基类（8 阶段抽象方法）
- Game 主循环骨架

商品和工厂是游戏设计文档（docs/GameDesign/Goods.md, Factory.md）中定义的核心实体，需要实现为代码。同时需要建立 Entity-Component 架构来支撑实体的组件化组合。

## Goals / Non-Goals

**Goals:**
- 建立 Entity/BaseComponent 基础架构，提供组件挂载、依赖拉起机制
- 实现 GoodsType、Recipe、FactoryType 静态配置数据模型
- 实现 GoodsBatch、Factory 运行时实例
- 实现工厂生产计算逻辑（产出量、产出品质、原料层特殊处理）
- 实现 StorageComponent（库存）和 ProductorComponent（科技值、品牌值、工厂列表）
- 改造 LedgerComponent 继承 BaseComponent
- 改造 Company 继承 Entity，挂载 ProductorComponent
- 提供 YAML 配置（三条产业链）

**Non-Goals:**
- 不实现采购匹配算法（MarketService）
- 不实现公司决策 AI（CompanyService 的 plan_phase）
- 不实现品牌衰减/投入机制的回合更新逻辑
- 不实现科技投入/累积的回合更新逻辑
- 不实现 EconomyEntryComponent（资产负债表）

## Decisions

1. **Entity-Component 架构**：Entity 维护 `Dict[Type[BaseComponent], BaseComponent]`，通过 `init_component` 创建组件（已存在则跳过），`get_component` 获取组件。组件通过 `outer` 引用访问所属实体。组件可在 `__init__` 中通过 `outer.init_component` 拉起依赖组件。

2. **数据模型分层**：GoodsType（纯商品定义）→ Recipe（转化关系）→ FactoryType（产能和经济属性）。供应链关系由 Recipe 链条隐式定义，GoodsType 本身不包含供应链信息。

3. **生产公式**：
   - 产出量 = base_production × output_quantity × 原料充足率 × 良品率加成
   - 良品率加成 = 1 + 原料品质 × bonus_ceiling
   - 产出品质 = tech_rank_ratio（Radio 0~1，由 ProductorComponent 计算并贴到产出上）
   - 原料层：无需输入，直接按 base_production × output_quantity 生产

4. **Factory 建造状态**：`build_remaining > 0` 表示在建，每回合递减；`== 0` 表示已建成可生产。

5. **ProductorComponent 依赖 StorageComponent**：实例化时自动通过 `outer.init_component(StorageComponent)` 拉起，并保存引用。

6. **类型注释**：ProductorComponent 使用具体类型做 dict key — `Dict[Recipe, int]`, `Dict[GoodsType, int]`。

7. **配置加载函数**：`load_goods_types`、`load_recipes`、`load_factory_types` 分别定义在 `entity/goods.py` 和 `entity/factory.py` 中，接受 ConfigManager 参数，返回 `Dict[str, T]` 字典。三者存在依赖链：goods_types → recipes → factory_types。

8. **BaseComponent 使用 TYPE_CHECKING 避免循环导入**：`BaseComponent` 中 `Entity` 类型仅用于类型标注，通过 `TYPE_CHECKING` 条件导入避免循环依赖。

9. **StorageComponent 使用 defaultdict**：inventory 使用 `defaultdict(list)` 简化按 GoodsType 分组的批次管理。

## Risks / Trade-offs

- Entity-Component 体系是新增架构，后续所有实体都将基于此。设计需稳定，但当前范围足够小（仅 Company 使用），风险可控。
- 生产计算中的 `tech_rank_ratio` 需要跨公司比较（同类商品最高科技值），当前由 `ProductorComponent.produce` 根据 `max_tech` 类变量计算，各公司通过 `update_max_tech()` 更新全局排名。
- 配置数据（goods.yaml）的结构需要与 ConfigManager 兼容，使用 AttrDict 访问。
