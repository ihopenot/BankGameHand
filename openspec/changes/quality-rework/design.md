## Context

BankGameHand 是一个银行经营模拟游戏。当前产品品质仅由科技排名（tech_rank_ratio）决定，原材料品质只通过良品率加成影响产出数量。消费者和企业采购评分使用 `quality / price` 作为性价比指标。

用户希望：
1. 移除品质对产量的提升（良品率加成）
2. 产品品质与原材料品质关联（加权混合）
3. 消费者/企业评分改为品质+品牌+价格吸引力三维加权混合
4. 新增上轮购买均价追踪机制

## Goals / Non-Goals

**Goals:**
- 产品品质 = 科技排名与原材料品质的加权混合
- 权重在配方级别可配置（`tech_quality_weight`）
- 产出数量不再受原材料品质影响
- 评分公式改为三维加权混合：品质 + 品牌 + 价格吸引力
- 价格吸引力用 sigmoid 函数映射到 [-1, 1]，基于自身上轮采购均价
- Folk 和 Company 追踪每种商品的上轮采购均价
- 统一重命名 `value_for_money` 为 `quality`，新增 `w_price` 权重

**Non-Goals:**
- 不改变科技投资和品牌投资的机制
- 不改变 softmax 分配逻辑
- 不改变原料层（无输入）的产出逻辑

## Decisions

1. **加权混合公式**：`output_quality = tech_rank_ratio * tech_quality_weight + avg_material_quality * (1 - tech_quality_weight)`。选择加权混合而非乘法混合，因为允许灵活配置两个因素的相对重要性。

2. **权重配置层级**：配置在 Recipe（配方）上，而非 GoodsType 或全局。因为不同产业链的配方对科技和原材料的依赖程度不同（如芯片制造重科技，食品生产重原料）。

3. **多工厂品质聚合**：同一 FactoryType 下多个工厂各自取料，原材料品质按各工厂产出数量加权平均。选择产出加权而非简单平均，因为产出多的工厂对最终品质影响应更大。

4. **factory.produce() 传递品质**：让 `factory.produce()` 将原材料品质（`supply.quality`）写入返回的 GoodsBatch，由 `ProductorComponent.produce()` 收集后计算最终品质。

5. **移除 bonus_ceiling**：`GoodsType.bonus_ceiling` 字段随良品率机制一并移除，简化数据模型。

6. **评分三维加权混合**：`quality / price` → `w_quality * quality + w_brand * brand + w_price * price_attractiveness`。价格通过 sigmoid 函数映射为吸引力值，与品质和品牌并列参与加权评分。

7. **价格吸引力 sigmoid 公式**：`price_attractiveness = 2 * sigmoid(k * (avg_price - price) / avg_price) - 1`。当价格低于均价时吸引力为正，高于均价时为负。k 为陡峭度参数（可后续调参）。均价为 0 时用 `base_price` 替代。

8. **购买均价追踪**：Folk 新增 `last_avg_buy_prices: Dict[GoodsType, float]`；Company 的 `DecisionComponent` 新增 `last_avg_buy_prices: Dict[GoodsType, float]`。每轮结算后按成交量加权更新，未购买的商品保持上轮值。

9. **三维权重配置**：Folk 配置 `w_quality`、`w_brand`、`w_price` 三个独立权重。B2B 企业同样独立配置价格敏感度（`DecisionComponent` 新增 `price_sensitivity` 特质）。

## Risks / Trade-offs

- 移除 `bonus_ceiling` 后，`GoodsType` 构造函数签名变化，所有创建 `GoodsType` 的代码和测试需同步更新
- 评分引入价格吸引力后，sigmoid 的陡峭度参数 k 需要调参以平衡价格敏感度
- 首轮无历史均价时使用 base_price 替代，可能导致首轮评分偏差
- `w_value_for_money` → `w_quality` 是全局重命名，需确保所有引用（代码、配置、测试、openspec 文档）都同步更新
