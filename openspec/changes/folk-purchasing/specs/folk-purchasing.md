## ADDED Requirements

### Requirement: Folk Entity（配置驱动）

每个居民群体作为独立经济实体存在，由配置文件定义其属性。不硬编码阶层标识，行为差异完全由配置参数决定。

#### Scenario: 从配置加载 Folk 列表
- **WHEN** 游戏初始化时通过 `ConfigManager.section("folk")` 加载 `config/folk.yaml`
- **THEN** 返回 `folks` 列表，每个条目创建一个 Folk 实体。配置格式为 `folks: List[Folk]`，每个 Folk 包含 population、w_value_for_money、w_brand、base_demands

#### Scenario: 每层人均基础需求不同
- **WHEN** 配置中不同 Folk 条目的 `base_demands` 对同一商品有不同的 `per_capita` 值
- **THEN** 各 Folk 实体对各商品的需求量独立计算，体现不同群体的消费差异（如某群体不消费某商品时 per_capita=0）

#### Scenario: Folk 实体组件挂载
- **WHEN** Folk 实体初始化
- **THEN** 每个 Folk 独立持有 LedgerComponent（现金）和 StorageComponent（库存），互不影响

#### Scenario: 配置示例
- **WHEN** `config/folk.yaml` 包含如下结构
- **THEN** 生成对应数量的 Folk 实体，各自属性不同

```yaml
folks:
  - population: 6000
    w_value_for_money: 0.95
    w_brand: 0.05
    base_demands:
      食品: { per_capita: 10, sensitivity: 0.1 }
      服装: { per_capita: 1, sensitivity: 0.5 }
      手机: { per_capita: 0, sensitivity: 0.8 }
  - population: 3000
    w_value_for_money: 0.5
    w_brand: 0.5
    base_demands:
      食品: { per_capita: 10, sensitivity: 0.2 }
      服装: { per_capita: 5, sensitivity: 0.5 }
      手机: { per_capita: 3, sensitivity: 0.7 }
  - population: 1000
    w_value_for_money: 0.2
    w_brand: 0.8
    base_demands:
      食品: { per_capita: 10, sensitivity: 0.05 }
      服装: { per_capita: 8, sensitivity: 0.3 }
      手机: { per_capita: 8, sensitivity: 0.4 }
```

### Requirement: 需求计算

每个 Folk 对每种终端消费品有独立的需求量，由其配置的人均基础需求决定。

#### Scenario: 计算消费需求
- **WHEN** 采购阶段开始
- **THEN** 某 Folk 对商品X的需求量 = population * base_demands[X].per_capita * (1 + 经济周期指数 * base_demands[X].sensitivity)

#### Scenario: 无需求的商品
- **WHEN** 某 Folk 配置中某商品的 per_capita 为 0 或未配置该商品
- **THEN** 该 Folk 不采购该商品

### Requirement: 加权均分采购

居民采购使用 softmax 归一化评分后按权重分配需求量。

#### Scenario: 评分计算
- **WHEN** 某 Folk 对某终端消费品的所有 SellOrder 评分
- **THEN** 评分 = w_value_for_money * (品质产出系数 / 标价) + w_brand * 品牌值，其中权重来自该 Folk 的配置

#### Scenario: softmax 归一化
- **WHEN** 对所有卖方评分完成
- **THEN** 权重_i = exp(评分_i) / sum(exp(评分_j))，所有卖方都获得正权重

#### Scenario: 按权重分配
- **WHEN** 权重计算完成
- **THEN** 每个卖方分配量 = floor(需求量 * 权重_i)，取整数

### Requirement: 迭代重分配

卖方库存不足时，剩余需求重新分配给其他有库存的卖方。

#### Scenario: 卖方库存充足
- **WHEN** 所有卖方库存 >= 分配量
- **THEN** 全部成交，一次分配完成

#### Scenario: 部分卖方库存不足
- **WHEN** 某卖方库存 < 分配量
- **THEN** 该卖方只成交其剩余库存，剩余需求收集起来；移除已售罄卖方，对剩余卖方重新 softmax 分配；循环直到需求满足或无卖方有库存

#### Scenario: 所有卖方售罄
- **WHEN** 所有卖方库存耗尽但需求未满足
- **THEN** 剩余需求记为缺货，不再分配

### Requirement: 采购结算

成交后进行商品转移和现金支付。

#### Scenario: 商品转移
- **WHEN** 居民与卖方成交
- **THEN** 从卖方 StorageComponent 扣减对应商品，买方（Folk）StorageComponent 入库新 GoodsBatch

#### Scenario: 现金支付（暂时无限现金）
- **WHEN** 成交完成
- **THEN** 居民通过 LedgerComponent 支付 成交量 * 卖方标价 的现金给卖方
