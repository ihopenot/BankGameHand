## Why

当前游戏仅支持终端 CLI 交互（stdin + rich 输出），无法通过网页访问游戏数据或操作。
需要一个 WebCli 以 WebController 形式提供网页端游戏界面，支持：
- 在浏览器中查看每回合经济数据、企业/银行/居民状态、贷款申请
- 通过网页提交玩家操作（审批贷款或跳过回合）

## What Changes

1. **新增 `WebInputController`**：实现 `PlayerInputController` 接口，通过 `threading.Event` 阻塞等待来自 WebSocket 的玩家操作
2. **新增 `WebController`**：基于 FastAPI 的 Web 应用，包含 HTTP 路由（静态页面）和 WebSocket handler（状态推送 + 操作接收）
3. **新增前端页面**：单 HTML 文件 + 原生 JS + CSS，通过 WebSocket 接收 JSON 数据渲染表格，提供贷款审批表单
4. **扩展 `PlayerService`**：新增 `*_dict()` 系列方法，返回 JSON 可序列化的 dict，供 WebController 使用
5. **新增 `web_main.py`**：Web 模式独立入口，启动 FastAPI 服务并在子线程运行 game loop

## Impact

- **新增文件**：`web/web_controller.py`、`web/web_input_controller.py`、`web/static/index.html`、`web_main.py`
- **修改文件**：`system/player_service.py`（新增 dict 方法，不影响现有 render 方法）
- **新增依赖**：`fastapi`、`uvicorn`、`websockets`
- **不影响**：现有 `main.py` 入口、game loop 逻辑、所有 service 实现、测试套件
