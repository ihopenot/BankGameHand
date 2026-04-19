## Why

当前产品品质仅由科技排名决定，原材料品质只影响产出数量（良品率加成），消费者评分使用 `quality / price`（性价比）。这导致：
1. 原材料品质对产品品质没有影响，不符合现实逻辑
2. 良品率加成机制使高品质原料只增加产量，设计意图不够直观
3. 消费者评分中品质被价格稀释，高品质产品在低价竞争中没有优势

## What Changes

1. **移除品质对产量的提升**：删除 `quality_bonus` 良品率加成机制，产出数量不再受原材料品质影响
2. **产品品质与原材料品质关联**：采用加权混合公式 `tech_rank_ratio * tech_weight + material_quality * (1 - tech_weight)`，权重在配方（Recipe）级别配置
3. **评分三维加权混合（品质 + 品牌 + 价格吸引力）**：评分公式从 `quality / price` 改为 `w_quality * quality + w_brand * brand_value + w_price * price_attractiveness`，其中价格吸引力用 sigmoid 函数基于上一轮自身采购均价计算（范围 [-1, 1]），均价为 0 时用 `base_price` 替代。重命名 `w_value_for_money` → `w_quality`。
4. **新增购买均价追踪**：Folk 和 Company 需记录每种商品的上一轮采购均价，用于评分中的价格吸引力计算

## Impact

- `entity/factory.py` — 移除 `quality_bonus`，`factory.produce()` 返回原材料品质；`Recipe` 新增 `tech_quality_weight`
- `entity/goods.py` — 移除 `GoodsType.bonus_ceiling`
- `component/productor_component.py` — 品质计算改为加权混合
- `system/folk_service.py` — 评分公式改为三维加权混合，新增价格吸引力 sigmoid 计算
- `system/decision_service.py` — B2B 采购评分同步改为三维加权混合
- `entity/folk.py` — `w_value_for_money` → `w_quality`，新增 `w_price`，新增 `last_avg_buy_prices` 追踪
- `component/decision_component.py` — 新增 `last_avg_buy_prices` 追踪（企业侧）
- `system/player_service.py` — 表头重命名，新增价格偏好列
- `config/goods.yaml` — 移除 `bonus_ceiling`，配方新增 `tech_quality_weight`
- `config/folk.yaml` — `w_value_for_money` → `w_quality`，新增 `w_price`
- 所有相关测试文件同步更新
