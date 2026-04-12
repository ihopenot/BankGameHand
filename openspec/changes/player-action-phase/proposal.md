## Why

游戏主循环中 `player_act()` 阶段目前为空（`pass`），玩家无法与游戏进行任何交互。需要实现玩家操作阶段的基础框架，使玩家能够在每回合查看经济状况并做出决策。

## What Changes

- 新增 `PlayerService`，负责玩家操作阶段的展示与输入逻辑
- 在 `player_act()` 阶段展示宏观经济数据（回合数、经济指数）和所有公司的财务概览（现金、库存、应收/应付款、工厂状态）
- 支持玩家输入"跳过回合"操作（`skip` 或直接回车）
- 使用纯文本表格格式化输出，不引入第三方依赖

## Impact

- **新增文件**：`system/player_service.py`、`tests/test_player_service.py`
- **修改文件**：`game/game.py`（新增 `interactive` 参数，初始化 PlayerService）、`main.py`（传入 `interactive=True`）、`core/types.py`（新增 `RATE_SCALE` 常量）、`tests/test_game_init.py`（使用共享 `RATE_SCALE`）
- **不影响**：现有游戏阶段顺序、其他服务逻辑
