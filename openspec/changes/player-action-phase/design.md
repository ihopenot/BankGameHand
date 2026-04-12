## Context

BankGameHand 是一个回合制经济模拟游戏，主循环包含 8 个阶段。其中 `player_act()` 阶段当前为空（`pass`），需要实现玩家交互的基础框架。

游戏已有完整的经济模型（双周期正弦模型）、公司系统（LedgerComponent/ProductorComponent/StorageComponent）和市场匹配系统。玩家操作阶段位于 `product_phase` 之后、`settlement_phase` 之前。

## Goals / Non-Goals

**Goals:**
- 实现 PlayerService 作为玩家操作的服务层
- 在 player_act 阶段展示宏观经济数据和公司财务概览
- 支持最基础的玩家输入：跳过回合
- 为未来扩展更多玩家操作预留清晰的扩展点

**Non-Goals:**
- 不实现跳过以外的任何玩家操作（如建厂、调价等）
- 不引入第三方终端 UI 库
- 不改变现有游戏阶段顺序或其他服务逻辑
- 不实现 AI 玩家/自动玩家模式

## Decisions

1. **新增 PlayerService 而非直接在 Game 类中实现**：遵循项目已有的 Service 模式（CompanyService、FolkService 等），保持架构一致性。PlayerService 不继承 Service(ABC) 基类——项目中 6 个 Service 中只有 2 个（EconomyService、ProductorService）继承了 Service(ABC)，其余均为独立类，当前做法与多数一致。
2. **使用 `input()` 进行玩家输入**：最简实现，符合当前项目无 UI 框架的现状
3. **纯 print 文本表格展示**：不引入 rich/tabulate 等依赖，使用字符串格式化对齐列
4. **展示数据来源**：宏观数据从 EconomyService 获取，公司数据遍历 Company 实体的各 Component
5. **Game.interactive 参数控制玩家交互**：默认 `interactive=False`（测试安全），`main.py` 入口传入 `True`。PlayerService 在 Game 中构造一次、每回合复用，动态数据（回合数、经济指数）通过方法参数传入。
6. **RATE_SCALE 提取为 core/types.py 中的共享常量**：消除 Game 和 PlayerService 中的重复定义，统一从 `core.types.RATE_SCALE` 导入。
7. **经济指数使用 `:.4f` 格式化**：避免浮点精度显示问题。

## Risks / Trade-offs

- `input()` 会阻塞游戏循环，在非交互环境（如自动测试）中需要 mock；测试时通过 mock `builtins.input` 解决
- 纯文本表格在公司数量多或库存种类多时可能显示不整齐；当前配置为 12 家公司，可接受
