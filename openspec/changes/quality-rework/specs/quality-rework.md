## ADDED Requirements

### Requirement: remove-quality-yield-bonus

移除原材料品质对产出数量的良品率加成。产出数量公式简化为 `base * output_quantity * sufficiency`。

#### Scenario: production-without-quality-bonus

- **WHEN** 工厂使用任意品质的原材料生产
- **THEN** 产出数量仅由基础产能、配方产出系数和原料充足率决定，不受原材料品质影响

#### Scenario: raw-material-layer-unchanged

- **WHEN** 原料层工厂（无输入原料）生产
- **THEN** 产出数量不变（`base * output_quantity`）

### Requirement: quality-weighted-blend

产品品质采用科技排名与原材料品质的加权混合，权重在配方级别配置。

#### Scenario: quality-with-material-input

- **WHEN** 工厂使用原材料生产，且配方 `tech_quality_weight = 0.6`
- **THEN** 产品品质 = `tech_rank_ratio * 0.6 + material_quality * 0.4`

#### Scenario: quality-raw-material-layer

- **WHEN** 原料层工厂生产（无输入原料）
- **THEN** 产品品质 = `tech_rank_ratio`（仅由科技决定）

#### Scenario: quality-multiple-factories

- **WHEN** 同一 FactoryType 下有多个工厂各自取料生产
- **THEN** 原材料品质按各工厂产出数量加权平均后参与品质计算

### Requirement: three-factor-scoring

消费者（Folk）和企业（B2B）评分公式改为品质、品牌、价格吸引力的三维加权混合。

#### Scenario: folk-scoring

- **WHEN** 居民评价卖方挂单，且上一轮该商品采购均价为 avg_price
- **THEN** 评分 = `w_quality * quality + w_brand * brand_value + w_price * price_attractiveness`，其中 `price_attractiveness = 2 * sigmoid(k * (avg_price - price) / avg_price) - 1`，范围 [-1, 1]

#### Scenario: folk-scoring-no-history

- **WHEN** 居民评价卖方挂单，且上一轮无采购记录（均价为 0）
- **THEN** 使用该商品的 `base_price` 作为 avg_price 替代

#### Scenario: b2b-scoring

- **WHEN** 企业评价供应商，且上一轮该商品采购均价为 avg_price
- **THEN** 评分 = `w_quality * quality + w_brand * brand_value + w_price * price_attractiveness`，价格吸引力计算方式与 Folk 相同

#### Scenario: b2b-scoring-no-history

- **WHEN** 企业评价供应商，且上一轮无采购记录（均价为 0）
- **THEN** 使用该商品的 `base_price` 作为 avg_price 替代

### Requirement: track-avg-buy-price

Folk 和 Company 需追踪每种商品的上一轮采购均价。

#### Scenario: folk-avg-price-update

- **WHEN** 居民在一轮中购买了某商品（可能多笔成交）
- **THEN** 该商品的 `last_avg_buy_price` 更新为本轮所有成交的加权均价（按成交数量加权）

#### Scenario: company-avg-price-update

- **WHEN** 企业在一轮中采购了某原材料（可能多笔成交）
- **THEN** 该原材料的 `last_avg_buy_price` 更新为本轮所有成交的加权均价

#### Scenario: no-purchase-round

- **WHEN** 某轮中未购买某商品
- **THEN** 该商品的 `last_avg_buy_price` 保持上轮值不变

### Requirement: rename-vfm-to-quality

将所有 `value_for_money` / `vfm` / "性价比" 相关命名统一改为 `quality` / "品质"。

#### Scenario: folk-config-rename

- **WHEN** 加载居民配置
- **THEN** 读取 `w_quality`、`w_brand`、`w_price` 三个权重字段（原 `w_value_for_money` → `w_quality`，新增 `w_price`）

#### Scenario: ui-label-rename

- **WHEN** 显示居民概览表格
- **THEN** 表头显示 "品质偏好"（原 "性价比偏好"），新增 "价格偏好" 列
