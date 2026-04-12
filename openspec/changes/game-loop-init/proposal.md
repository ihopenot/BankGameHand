## Why

Game 类只有骨架代码，各 Service 和 Entity 已实现但未接入主循环。游戏无法运行。需要完成初始化逻辑并将已有模块接入 game_loop，使经济模拟能自动运行。

## What Changes

- 新增 `config/game.yaml` 配置文件，定义公司初始化参数（每种产品的公司数量、初始资金等）
- 完善 `Game.__init__` 初始化逻辑：从配置创建公司（含工厂、初始资金、初始定价）、创建居民、初始化所有 Service
- 完善 `Game.game_loop` 各阶段调用：正确串联 EconomyService、CompanyService、MarketService、FolkService、ProductorService
- ProductorService 补充 `update_phase`（推进工厂建造）
- `player_act` 阶段跳过（当前无银行无玩家操作）
- 新增入口脚本 `main.py` 启动游戏

## Impact

- 新增文件：`config/game.yaml`、`main.py`、`tests/test_game_init.py`、`tests/test_game_loop.py`、`tests/test_productor_service_update.py`
- 修改文件：`game/game.py`、`system/productor_service.py`
- 修改测试文件：`tests/test_integration.py`、`tests/test_review_regressions.py`
- 新增测试配置：`tests/config_integration/game.yaml`、`goods.yaml`、`folk.yaml`
- 不修改已有组件（BaseComponent 子类）、不新增组件
- 不引入银行、贷款、玩家交互等未实现的业务逻辑
