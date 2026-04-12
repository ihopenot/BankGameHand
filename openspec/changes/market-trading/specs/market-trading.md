## ADDED Requirements

### Requirement: MarketService 撮合引擎

MarketService 接收卖方挂单和买方采购意向，执行逐轮匹配算法，返回成交记录。

#### Scenario: 卖方挂单收集
- **WHEN** CompanyService 调用 `market_service.add_sell_order(order)` 提交挂单
- **THEN** MarketService 将 SellOrder 存入内部列表，可通过 `get_sell_orders(goods_type)` 查询

#### Scenario: 每回合清空挂单
- **WHEN** `market_service.update_phase()` 被调用
- **THEN** 所有已收集的 SellOrder 被清空

#### Scenario: 逐轮匹配 — 供大于求
- **WHEN** 某卖方收到的总订单量 ≤ 其剩余库存
- **THEN** 所有订单全部成交，成交价 = 卖方标价，被满足的买方退出匹配

#### Scenario: 逐轮匹配 — 供小于求
- **WHEN** 某卖方收到的总订单量 > 其剩余库存
- **THEN** 按各订单量等比例分配库存，成交价 = 卖方标价，卖方售罄退出匹配

#### Scenario: 逐轮匹配 — 终止条件
- **WHEN** 无剩余买方，或无剩余卖方，或本轮无任何成交
- **THEN** 匹配结束，返回所有 TradeRecord

#### Scenario: 买方多轮降级选择
- **WHEN** 买方首选卖方售罄后仍有剩余需求
- **THEN** 下一轮买方向偏好列表中排名次高的剩余卖方下单

### Requirement: 公司卖方挂单（sell_phase）

每回合 sell_phase 阶段，所有持有库存的公司向 MarketService 提交卖方挂单。

#### Scenario: 正常挂单
- **WHEN** 公司 StorageComponent 中某商品有库存
- **THEN** 为该商品的每个 GoodsBatch 创建 SellOrder，price 取 ProductorComponent.prices 中的定价，quantity 取 batch.quantity

#### Scenario: 无库存不挂单
- **WHEN** 公司某商品库存为 0
- **THEN** 不为该商品创建 SellOrder

### Requirement: 公司买方采购（buy_phase）

每回合 buy_phase 阶段，下游公司根据工厂原料需求向市场采购。

#### Scenario: 需求计算
- **WHEN** 公司拥有需要原料的工厂
- **THEN** 需求量 = Σ(recipe.input_quantity × base_production) 对所有同类工厂 - 现有该原料库存量，最小为 0

#### Scenario: 偏好排序
- **WHEN** 市场上存在目标商品的多个 SellOrder
- **THEN** 买方按性价比（quality / price）从高到低排序生成偏好列表

#### Scenario: 成交后商品转移
- **WHEN** 匹配产生 TradeRecord
- **THEN** 卖方 SellOrder 关联的 GoodsBatch.quantity 扣减成交量，买方 StorageComponent 增加对应的新 GoodsBatch

#### Scenario: 成交后现金支付
- **WHEN** 买方现金 ≥ 成交总额
- **THEN** 买方 LedgerComponent.cash 扣减，卖方 LedgerComponent.cash 增加

#### Scenario: 成交后赊账
- **WHEN** 买方现金 < 成交总额
- **THEN** 现金全额支付，不足部分创建 TRADE_PAYABLE 类型的 Loan（buyer=debtor, seller=creditor, term=1, BULLET 偿付）

### Requirement: ProductorComponent 定价属性

ProductorComponent 维护各产出商品的当前标价。

#### Scenario: 初始化定价
- **WHEN** ProductorComponent 初始化
- **THEN** prices 字典中各产出商品的价格等于对应 GoodsType.base_price

### Requirement: LoanType.TRADE_PAYABLE

新增贷款类型表示应付账款。

#### Scenario: 优先级
- **WHEN** 结算时存在 TRADE_PAYABLE 类型的 Loan
- **THEN** 其优先级最高（priority 值最小），在所有其他 Loan 类型之前偿还
