## Why

居民部门（Folk）是经济模拟中的终端消费者，目前 `folk_service.py` 为空，经济循环缺少消费端。没有居民采购，公司生产的终端消费品无法被消费，经济循环无法闭合。

## What Changes

- 新增 `config/folk.yaml`：居民配置文件，格式为 `folks: List[Folk]`，每个 Folk 条目定义人口、偏好权重、各商品的人均基础需求和经济敏感度。不硬编码阶层标识，不同阶层的行为差异完全由配置参数决定
- 新增 `entity/folk.py`：Folk 实体类，由配置驱动初始化，持有 LedgerComponent 和 StorageComponent。提供 `load_folks` 工厂函数从 ConfigManager 加载
- 实现 `system/folk_service.py`：FolkService，包含：
  - 需求计算：按各 Folk 的人口和人均基础需求（每层每种商品不同）及经济周期计算各终端消费品需求量
  - 加权均分采购：对卖方评分做 softmax 归一化后按权重分配需求量（非逐轮匹配）
  - 迭代重分配：库存不足的卖方售罄后，剩余需求重新分配给其他卖方
  - 结算：商品转移和现金支付

## Impact

- 新增文件：`config/folk.yaml`、`entity/folk.py`、`system/folk_service.py`
- 依赖已有：`MarketService`（读取 SellOrder）、`LedgerComponent`、`StorageComponent`、`GoodsBatch`、`ConfigManager`
- 不修改现有文件
- 居民暂时设为无限现金，购买力约束、收入计算、储蓄机制留待后续实现
