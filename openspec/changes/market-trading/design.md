## Context

游戏采用 Entity-Component 架构，公司（Company）持有 ProductorComponent（生产）、StorageComponent（库存）和 LedgerComponent（账本）。生产系统已实现：ProductorComponent 从库存取料、通过工厂生产、将产出存入库存。但生产出的商品无法卖出，下游公司也无法采购原料——缺少 sell_phase 和 buy_phase 的市场撮合层。

游戏主循环（game.py）已定义调用顺序：
- `update_phase` → `sell_phase` → `buy_phase` → `product_phase` → ...
- `sell_phase` 由 CompanyService 驱动，向 MarketService 提交挂单
- `buy_phase` 分两轮：居民先买终端品、公司后买原料/中间品（本次只实现公司部分）

现有的 MarketService 和 CompanyService 都是空壳/骨架。

## Goals / Non-Goals

**Goals:**
- 实现完整的公司间商品买卖流程（挂单 → 匹配 → 成交 → 商品转移 → 支付/赊账）
- 实现 MarketService 逐轮匹配算法（按 MainLoop.md 设计文档规范）
- 支持赊账机制（现金不足时创建应付账款）
- 在 ProductorComponent 中维护商品定价

**Non-Goals:**
- 不实现居民三层采购（Folk/FolkService）
- 不实现 CEO 特质和动态定价决策
- 不实现品牌权重差异（采购偏好暂时只看性价比）
- 不实现库存仓储成本扣减
- 不实现居民收入/预算约束

## Decisions

### D1: SellOrder 直接引用 GoodsBatch

SellOrder 持有对 StorageComponent 中 GoodsBatch 对象的引用，匹配成交时直接扣减 batch.quantity。避免数据冗余和同步问题。settle_trades 按 TradeRecord 从卖方库存扣减并向买方入库新 GoodsBatch。

### D2: 定价存储在 ProductorComponent

在 ProductorComponent 中新增 `prices: Dict[GoodsType, Money]`，初始值取 `goods_type.base_price`。为后续实现 CEO 定价决策预留扩展点。sell_phase 从此属性读取标价。

### D3: MarketService 为无状态撮合引擎

MarketService 不继承 Service 基类（它不参与游戏各阶段的完整生命周期），而是作为工具类被 CompanyService 调用。每回合在 update_phase 时清空挂单。

### D4: 分开两轮匹配

居民和公司的采购分为两次独立匹配调用。因为居民只买终端消费品、公司只买原料/中间品，商品种类不重叠，分开匹配不影响结果。符合 game.py 的调用结构。

### D5: 赊账使用 LoanType.TRADE_PAYABLE

新增 Loan 类型 `TRADE_PAYABLE`，优先级最高（结算时最先偿还）。成交时现金不足部分创建 Loan，term=1、BULLET 偿付。

### D6: 采购偏好只按性价比排序

暂不实现品牌权重差异。所有买方统一使用 `quality / price` 作为供应商评分。简化首版实现，品牌权重留待 CEO 特质实现时引入。

## Risks / Trade-offs

- **简化定价**：所有公司使用 base_price 固定标价，不同公司的同类商品价格相同，可能导致匹配结果过于均匀。后续需要实现 CEO 定价决策来引入差异化。
- **无品牌权重**：买方纯看性价比，品牌值在采购中无效果。这是有意简化，但意味着高品牌投入暂时无回报。
- **SellOrder 引用 batch**：直接引用意味着匹配过程会修改 StorageComponent 内部状态。如果匹配需要回滚或重试，需要特殊处理。当前设计中匹配是一次性的，不存在此问题。
