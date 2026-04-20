## ADDED Requirements

### Requirement: WebInputController

实现 `PlayerInputController` 抽象接口的 Web 版本，通过 WebSocket 接收玩家操作。

#### Scenario: 玩家提交贷款审批操作
- **WHEN** 游戏到达 player_act_phase 且前端通过 WebSocket 发送审批操作 JSON
- **THEN** `get_action()` 解析 JSON 为 `PlayerAction(action_type="approve_loans", ...)`，game loop 继续执行

#### Scenario: 玩家跳过回合
- **WHEN** 游戏到达 player_act_phase 且前端发送 skip 操作
- **THEN** `get_action()` 返回 `PlayerAction(action_type="skip")`，game loop 继续执行

#### Scenario: 等待玩家输入时阻塞
- **WHEN** game loop 线程调用 `get_action()` 且前端尚未提交操作
- **THEN** 方法阻塞等待（通过 `threading.Event`），不消耗 CPU

### Requirement: WebController (FastAPI)

基于 FastAPI 的 Web 应用，提供 HTTP 路由和 WebSocket 通信。

#### Scenario: 提供静态页面
- **WHEN** 浏览器请求 `GET /`
- **THEN** 返回 `web/static/index.html` 页面

#### Scenario: WebSocket 连接与状态推送
- **WHEN** 前端建立 WebSocket 连接到 `/ws`
- **THEN** 服务端在每回合 player_act_phase 时推送游戏状态 JSON（经济指数、企业表、居民表、银行表、贷款申请表）

#### Scenario: 通过 WebSocket 接收操作
- **WHEN** 前端通过 WebSocket 发送玩家操作 JSON
- **THEN** 服务端解析操作并传递给 `WebInputController`，解除 game loop 阻塞

#### Scenario: 游戏启动
- **WHEN** 浏览器发送启动游戏请求（通过 WebSocket 消息或 POST /api/start）
- **THEN** 在子线程中创建 Game 实例并启动 game_loop

### Requirement: PlayerService 数据序列化

扩展 PlayerService 支持 JSON 数据输出。

#### Scenario: 获取经济概要 dict
- **WHEN** 调用 `economy_summary_dict()`
- **THEN** 返回包含 `round`、`total_rounds`、`economy_index` 的 dict

#### Scenario: 获取企业概览 dict
- **WHEN** 调用 `company_table_dict()`
- **THEN** 返回企业列表，每项含公司名、工厂类型、工厂数、现金、科技、品牌、定价、库存、应收款、应付款

#### Scenario: 获取贷款申请 dict
- **WHEN** 调用 `loan_applications_dict(applications, company_names)`
- **THEN** 返回贷款申请列表，每项含序号、申请企业名、申请金额

### Requirement: 前端页面

单 HTML 文件实现完整 Web UI。

#### Scenario: 展示游戏数据
- **WHEN** 收到 WebSocket 状态推送
- **THEN** 页面刷新所有数据表格（经济概要、企业表、居民表、银行表、贷款申请表）

#### Scenario: 提交贷款审批
- **WHEN** 玩家在贷款申请表中填写审批参数并点击提交
- **THEN** 通过 WebSocket 发送操作 JSON，操作区禁用直到下一回合

#### Scenario: 跳过回合
- **WHEN** 玩家点击"跳过回合"按钮
- **THEN** 通过 WebSocket 发送 skip 操作

#### Scenario: 游戏结束
- **WHEN** 收到游戏结束事件
- **THEN** 页面显示游戏结束提示，操作区禁用

### Requirement: Web 模式入口

独立的 Web 模式启动入口 `web_main.py`。

#### Scenario: 启动 Web 服务
- **WHEN** 运行 `python web_main.py`
- **THEN** 启动 FastAPI 服务（uvicorn），监听指定端口，等待浏览器连接后启动游戏
