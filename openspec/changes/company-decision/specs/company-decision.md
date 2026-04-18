## ADDED Requirements

### Requirement: CEO 特质系统

每个公司拥有 5 维 CEO 特质，取值范围 0~1，在公司创建时随机生成或从配置加载。

#### Scenario: CEO 特质随机生成
- **WHEN** 创建公司时未指定 CEO 特质
- **THEN** 每个特质从 [0, 1] 均匀分布随机生成

#### Scenario: CEO 特质从配置加载
- **WHEN** game.yaml 中为公司指定了 CEO 特质值
- **THEN** 使用配置值初始化，未指定的特质仍随机生成

### Requirement: 产品定价

每回合 plan_phase 中，公司根据上轮销售情况调整下轮标价。

#### Scenario: 库存售罄时涨价
- **WHEN** 公司某商品上轮库存全部售出
- **THEN** 标价上涨，涨幅 = 基础涨幅 × (1 + 风险偏好 × 风险系数)

#### Scenario: 库存有剩余时降价
- **WHEN** 公司某商品上轮库存有剩余
- **THEN** 标价下降，降幅 = 基础降幅 × (1 + (1 - 利润追求) × 让利系数)

#### Scenario: 定价噪声
- **WHEN** 调整标价
- **THEN** 加入随机噪声，噪声幅度 = f(1 / 商业洞察力)，洞察力越低噪声越大

### Requirement: 投资计划表

plan_phase 中每个公司生成投资计划表，包含三个方向的计划金额（扩产/品牌/科技），但不实际扣钱。

#### Scenario: 扩产计划
- **WHEN** 投资意愿 = f(风险偏好, 现金充裕度, 市场前景) > 投资阈值
- **THEN** 计划金额 = 选定工厂类型的 build_cost

#### Scenario: 市场前景感知偏差
- **WHEN** 公司评估市场前景
- **THEN** 感知的供需比受商业洞察力影响：洞察力越低，感知偏差越大

#### Scenario: 品牌投入计划
- **WHEN** 到达 plan_phase
- **THEN** 计划金额 = 营收 × 基础比例 × (1 + 营销意识 × 营销系数)

#### Scenario: 科技投入计划
- **WHEN** 到达 plan_phase
- **THEN** 计划金额 = 营收 × 基础比例 × (1 + 科技重视度 × 科技系数)

### Requirement: 保留金机制

公司根据 CEO 保守倾向保留一定现金用于经营，不投入投资。

#### Scenario: 保留金计算
- **WHEN** act_phase 执行投资前
- **THEN** 保留金 = 经营开销 × (1 + (1 - 风险偏好) × 保留金系数)
  其中经营开销 = Σ(已建成工厂的 maintenance_cost)

#### Scenario: 激进 CEO 保留少
- **WHEN** 风险偏好 = 1.0
- **THEN** 保留金 = 经营开销 × 1.0（仅保留一倍开销）

#### Scenario: 保守 CEO 保留多
- **WHEN** 风险偏好 = 0.0
- **THEN** 保留金 = 经营开销 × (1 + 保留金系数)（默认三倍开销）

### Requirement: 投资执行与资金分配

act_phase 中根据投资预算执行计划表，未花完的资金回流。

#### Scenario: 预算充足全额执行
- **WHEN** 投资预算（现金 - 保留金）≥ 计划总额
- **THEN** 按计划金额全额执行扩产、品牌、科技投入

#### Scenario: 预算不足按比例分配
- **WHEN** 投资预算 < 计划总额
- **THEN** 按各方向计划金额的比例分配预算

#### Scenario: 扩产不够建厂时回流
- **WHEN** 扩产分配金额 < 工厂 build_cost
- **THEN** 扩产资金不扣款，回流到现金

#### Scenario: 品牌/科技投入执行
- **WHEN** act_phase 执行品牌/科技投入
- **THEN** 分配金额直接增加对应的 brand_values / tech_values，按产出商品类型/配方均分

### Requirement: 原料采购偏好

在 buy_phase 中根据 CEO 特质计算供应商评分排序。

#### Scenario: 采购偏好计算
- **WHEN** 公司生成 BuyIntent 的供应商偏好排序
- **THEN** 供应商评分 = w_性价比 × (品质产出系数 / 标价) + w_品牌 × 品牌值
  其中 w_品牌 = 营销意识 × brand_weight_coeff, w_性价比 = 1 - w_品牌

#### Scenario: 高营销意识偏好品牌
- **WHEN** CEO 营销意识高
- **THEN** 品牌权重增大，偏向品牌供应商

#### Scenario: 低营销意识偏好性价比
- **WHEN** CEO 营销意识低
- **THEN** 几乎纯按性价比排序

### Requirement: 决策参数配置化

所有公式中的系数通过 decision.yaml 配置，遵循项目 YAML-driven 模式。

#### Scenario: 配置加载
- **WHEN** 游戏初始化
- **THEN** 从 decision.yaml 加载所有决策系数（定价系数、投资阈值、保留金系数、品牌/科技投入比例等）
