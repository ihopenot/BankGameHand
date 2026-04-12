## ADDED Requirements

### Requirement: game-config

游戏初始化配置 `config/game.yaml` 定义公司生成参数。

#### Scenario: config-loaded

- **WHEN** Game 初始化时加载 `config/game.yaml`
- **THEN** 能读取到每种工厂类型对应的公司数量、初始资金等参数

### Requirement: game-init-companies

Game 初始化时从配置创建公司实例。

#### Scenario: companies-created

- **WHEN** Game.__init__ 执行完成
- **THEN** 每种工厂类型创建了配置数量的公司，每公司持有一个已建好的工厂、初始资金、初始定价

### Requirement: game-init-folks

Game 初始化时创建居民实例。

#### Scenario: folks-created

- **WHEN** Game.__init__ 执行完成
- **THEN** 3 层居民从 folk.yaml 加载完成，持有 LedgerComponent 和 StorageComponent

### Requirement: game-init-services

Game 初始化时创建并关联所有 Service。

#### Scenario: services-initialized

- **WHEN** Game.__init__ 执行完成
- **THEN** economy_service、company_service、market_service、folk_service、productor_service 均已初始化且关联到 Game

### Requirement: game-loop-runs

game_loop 能从头到尾自动运行指定回合数。

#### Scenario: full-loop-execution

- **WHEN** 调用 game_loop()
- **THEN** 按 update → sell → buy → product → settlement 顺序执行每回合，运行至 game_end 条件满足时停止，无异常抛出

### Requirement: company-update-phase

ProductorService.update_phase 推进工厂建造进度。

#### Scenario: factory-build-tick

- **WHEN** update_phase 执行
- **THEN** 所有公司的在建工厂 build_remaining 减 1

### Requirement: buy-phase-integration

采购阶段正确串联居民采购和公司采购。

#### Scenario: buy-phase-flow

- **WHEN** buy_phase 执行
- **THEN** 居民先采购终端消费品，公司再采购原料/中间品，成交后商品和现金正确转移

### Requirement: main-entry

提供 main.py 入口脚本启动游戏。

#### Scenario: run-main

- **WHEN** 执行 `python main.py`
- **THEN** 游戏初始化并自动运行完整循环，无异常
