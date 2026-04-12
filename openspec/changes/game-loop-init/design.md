## Context

BankGameHand 是一个经济模拟游戏。已实现了完整的组件层（LedgerComponent、ProductorComponent、StorageComponent）、实体层（Company、Folk）、服务层（EconomyService、MarketService、CompanyService、FolkService、ProductorService）以及市场撮合引擎。

但 `Game` 类只有骨架代码，缺少初始化逻辑，各 service 未实际创建和关联，game_loop 各阶段未正确调用已有服务。

当前阶段不实现 Bank、贷款、玩家交互等系统，目标是让无银行版本的经济循环跑起来（对应 GameDesign 中 Warmup 阶段）。

## Goals / Non-Goals

**Goals:**
- 从配置文件驱动创建公司和居民
- 将所有已有 Service 接入 game_loop
- 游戏能自动运行完整循环（采购→生产→挂单→结算）
- 标准要以接入用户操作后能直接运行为准

**Non-Goals:**
- 不实现新的 BaseComponent 子类
- 不实现 Bank 实体和银行业务
- 不实现公司 AI 决策（定价调整、品牌/科技投入、扩产）
- 不实现政府服务
- 不实现玩家交互
- 不实现破产/清算逻辑
- 不实现经济统计（通胀率等）

## Decisions

1. **Game 初始化**：新增 `config/game.yaml` 配置公司生成参数（每种工厂类型的公司数量、初始资金）。Game.__init__ 中按配置加载 goods→recipes→factory_types→创建公司→创建居民→初始化 services。Game.__init__ 接受可选的 `config_path` 参数用于测试。

2. **公司创建**：每个公司绑定一种 FactoryType，持有一个已建好的工厂（build_remaining=0）。初始资金和初始定价从配置读取。ProductorComponent 的 tech_values 和 brand_values 初始化为 0。公司在 dict 中使用全局递增编号 `company_{idx}` 作为键，确保唯一性。

3. **game_loop 阶段映射**：
   - update_phase → EconomyService.update_phase + ProductorService.update_phase（含工厂建造推进） + MarketService.update_phase
   - sell_phase → CompanyService.sell_phase(market)
   - buy_phase → FolkService.buy_phase(market, economy_index) + CompanyService.buy_phase(market) + match + settle
   - product_phase → ProductorService.product_phase
   - plan_phase → 跳过
   - player_act → 跳过
   - settlement_phase → LedgerComponent.generate_bills + settle_all（结算赊账）
   - act_phase → 跳过

4. **ProductorService.update_phase**：先遍历所有 ProductorComponent 的工厂调用 tick_build() 推进建造，再清空 max_tech 并更新。

5. **buy_phase 流程**：居民采购使用 FolkService.buy_phase（内含 settle_trades）；公司采购使用 CompanyService.buy_phase 生成 BuyIntent 列表 → MarketService.match 撮合 → CompanyService.settle_trades 结算。economy_index 从 Rate（/10000）归一化为比率传入 FolkService，使用 `Game.RATE_SCALE` 常量。

6. **settlement_phase**：遍历所有公司的 LedgerComponent，调用 generate_bills + settle_all 处理赊账 Loan。

7. **ProductorService 直接调用**：Game.product_phase 直接调用 ProductorService.product_phase，不经过 CompanyService。

8. **game_end 条件**：`round >= total_rounds`（从 config/game.yaml 读取 total_rounds），而非硬编码 `round > 20`。

9. **集成测试适配**：已有的集成测试 `_GameForTest` 通过 `config_path` 参数使用独立的测试配置目录。不再使用 MagicMock 替代 service，而是使用完整的 Game 初始化。

## Risks / Trade-offs

- 无公司 AI 决策意味着公司每回合定价不变、不投入品牌/科技、不扩产，经济循环较静态
- 无破产机制意味着现金耗尽的公司仍然存在（但无法采购，实际处于停产状态）
- 无政府保底收入意味着居民初始现金耗尽后无法继续购买
- 这些都是已知的简化，后续 change 逐步补齐
