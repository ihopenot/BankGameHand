## Why

游戏主循环中的 sell_phase 和 buy_phase 尚未实现。公司之间无法进行商品交易（上游卖原料/中间品 → 下游买原料/中间品），导致生产系统虽已完成但无法与市场衔接。没有采购阶段，公司无法获取生产所需的原料，整个经济循环无法运转。

## What Changes

1. **MarketService（市场撮合引擎）**：新建 `system/market_service.py`，包含 SellOrder、BuyIntent、TradeRecord 数据结构和逐轮匹配算法
2. **CompanyService.sell_phase**：实现公司卖方挂单逻辑，从库存和 ProductorComponent 定价生成 SellOrder
3. **CompanyService.buy_phase**：实现公司买方采购逻辑，计算原料需求、按性价比排序生成偏好、匹配后处理商品转移和现金/赊账
4. **ProductorComponent 扩展**：新增 `prices: Dict[GoodsType, Money]` 属性，存储各产出商品的当前标价
5. **LoanType 扩展**：新增 `TRADE_PAYABLE`（应付账款）类型
6. **Company 扩展**：初始化 LedgerComponent

## Impact

- **新增文件**：`system/market_service.py`
- **修改文件**：`system/company_service.py`、`component/productor_component.py`、`core/types.py`、`entity/company/company.py`
- **依赖**：依赖已实现的 StorageComponent、LedgerComponent、ProductorComponent、GoodsBatch/GoodsType
- **不影响**：经济周期系统、工厂生产逻辑、配置文件格式
- **简化**：本次不实现 CEO 特质、品牌权重差异、居民采购、动态定价
