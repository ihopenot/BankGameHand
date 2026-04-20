## Context

BankGameHand 是一个回合制银行经营模拟游戏，当前仅支持终端交互。架构采用 ECS + Service Layer 模式，业务逻辑在 Service 层，输入通过 `PlayerInputController` 抽象（当前实现为 `StdinInputController`）。

game loop 同步执行，在 `player_act_phase` 阶段阻塞等待玩家输入。`PlayerService` 负责渲染数据（返回 rich 对象）和处理玩家操作。

## Goals / Non-Goals

**Goals:**
- 提供网页端游戏界面，展示与终端相同的数据
- 支持通过网页提交玩家操作（贷款审批 / 跳过）
- 保持现有终端模式不受影响，两种模式独立运行
- 架构上为后续多人模式预留 WebSocket 基础

**Non-Goals:**
- 多人同时操作（本次仅单人 Web 模式）
- 替换或修改现有终端 CLI 模式
- 游戏存档 / 读档功能
- 用户认证 / 登录

## Decisions

1. **替换模式**：WebController 通过 `WebInputController`（实现 `PlayerInputController` 接口）接入，不修改 game loop
2. **FastAPI + WebSocket**：选择 FastAPI 支持原生 WebSocket，为后续多人扩展友好；uvicorn 作为 ASGI server
3. **线程模型（实际实现）**：采用协程内联游戏循环而非多线程方案。`_handle_start_game` 在同一 async 上下文中顺序执行游戏阶段，通过 `await ws.receive_text()` 等待玩家操作。这简化了线程同步，消除了竞态条件风险。`WebInputController` 的 `threading.Event` 机制保留供未来多线程场景使用
4. **前端方案**：单 HTML 文件 + 原生 JS + WebSocket API，无构建步骤，无前端框架。深色主题 + 渐变色强调
5. **数据序列化**：在 `PlayerService` 新增 `*_dict()` 方法返回 JSON 可序列化 dict，与现有 `render_*` 方法并行。`economy_index` 统一 round 到 4 位小数
6. **状态推送时机**：每回合 player_act_phase 开始时推送完整游戏状态；游戏结束推送 `game_end` 事件
7. **游戏循环内联**：`WebController._handle_start_game()` 直接拆解 `Game.game_loop()` 的各阶段，在 player_act 位置插入 WebSocket 交互（发送状态 → 等待操作），避免了替换 game loop 方法的 monkey-patch 方案

## Risks / Trade-offs

- **单 WebSocket 连接**：当前设计仅支持一个 WebSocket 客户端，多个浏览器 tab 同时连接可能导致状态混乱；后续多人模式需要连接管理
- **线程安全**：game loop 和 FastAPI 在不同线程，通过 Event 同步；需确保共享状态（游戏数据读取）的线程安全，但由于数据流是单向的（game loop 产生数据 → WebSocket 推送），风险较低
- **新增依赖**：引入 fastapi、uvicorn、websockets 三个新依赖，需要维护
