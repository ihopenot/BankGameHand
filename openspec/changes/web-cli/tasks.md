# Web CLI 实现任务

## 1. PlayerService 数据序列化扩展

- [x] 1.1 为 PlayerService 新增 `*_dict()` 系列方法  <!-- TDD 任务 -->
  - [x] 1.1.1 写失败测试：`tests/test_player_service_dict.py` — 测试 `economy_summary_dict()`、`company_table_dict()`、`folk_table_dict()`、`bank_summary_dict()`、`loan_applications_dict()` 返回正确结构的 dict
  - [x] 1.1.2 验证测试失败（运行：`python -m pytest tests/test_player_service_dict.py -v`，确认失败原因是缺少方法）
  - [x] 1.1.3 写最小实现：`system/player_service.py` — 新增 5 个 `*_dict()` 方法，提取与 `render_*` 相同的数据但返回 dict
  - [x] 1.1.4 验证测试通过（运行：`python -m pytest tests/test_player_service_dict.py -v`，确认所有测试通过，输出干净）
  - [x] 1.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 1.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 2. WebInputController 实现

- [x] 2.1 实现 `WebInputController` 类  <!-- TDD 任务 -->
  - [x] 2.1.1 写失败测试：`tests/test_web_input_controller.py` — 测试 `get_action()` 阻塞等待、接收 skip 操作、接收 approve_loans 操作、`submit_action()` 解除阻塞
  - [x] 2.1.2 验证测试失败（运行：`python -m pytest tests/test_web_input_controller.py -v`，确认失败原因是缺少模块）
  - [x] 2.1.3 写最小实现：`web/web_input_controller.py` — 继承 `PlayerInputController`，使用 `threading.Event` 实现阻塞等待，提供 `submit_action()` 供 WebSocket handler 调用，提供 `set_state()` 供 game loop 推送当前回合状态
  - [x] 2.1.4 验证测试通过（运行：`python -m pytest tests/test_web_input_controller.py -v`，确认所有测试通过，输出干净）
  - [x] 2.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 2.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 3. WebController (FastAPI) 实现

- [x] 3.1 实现 `WebController` 类  <!-- TDD 任务 -->
  - [x] 3.1.1 写失败测试：`tests/test_web_controller.py` — 测试 GET / 返回 HTML、WebSocket 连接建立、WebSocket 接收状态推送、WebSocket 发送操作
  - [x] 3.1.2 验证测试失败（运行：`python -m pytest tests/test_web_controller.py -v`，确认失败原因是缺少模块）
  - [x] 3.1.3 写最小实现：`web/web_controller.py` — FastAPI 应用，GET / 返回静态页面，WebSocket /ws 处理连接和消息路由，启动/停止 game loop 的子线程管理
  - [x] 3.1.4 验证测试通过（运行：`python -m pytest tests/test_web_controller.py -v`，确认所有测试通过，输出干净）
  - [x] 3.1.5 重构：整理代码、改善命名、消除重复（保持所有测试通过）

- [x] 3.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 4. 前端页面实现

- [x] 4.1 创建前端 HTML 页面  <!-- 非 TDD 任务 -->
  - [x] 4.1.1 执行变更：`web/static/index.html` — 单文件实现完整 Web UI，包含：顶部状态栏（回合数、经济指数、游戏状态）、数据区（企业/居民/银行/贷款申请表格）、操作区（贷款审批表单 + 跳过按钮）、WebSocket 连接管理与 JSON 数据渲染、样式美化
  - [x] 4.1.2 验证无回归（运行：`python -m pytest tests/ -q`，确认所有测试通过）
  - [x] 4.1.3 检查：确认 HTML 文件可被 WebController 正确 serve，WebSocket 地址正确

- [x] 4.2 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 5. Web 模式入口与集成

- [x] 5.1 创建 `web_main.py` 入口脚本  <!-- 非 TDD 任务 -->
  - [x] 5.1.1 执行变更：`web_main.py` — 创建 Web 模式入口，初始化 WebController 并通过 uvicorn 启动 FastAPI 服务，支持命令行参数指定 host/port
  - [x] 5.1.2 验证无回归（运行：`python -m pytest tests/ -q`，确认所有测试通过）
  - [x] 5.1.3 检查：确认 `python web_main.py` 可启动服务，浏览器能访问页面并正常交互

- [x] 5.2 新增 `web/__init__.py` 模块初始化  <!-- 非 TDD 任务 -->
  - [x] 5.2.1 执行变更：`web/__init__.py` — 创建空的 `__init__.py` 使 web 目录成为 Python 包
  - [x] 5.2.2 验证无回归（运行：`python -m pytest tests/ -q`，确认所有测试通过）
  - [x] 5.2.3 检查：确认 `from web.web_controller import WebController` 可正常导入

- [x] 5.3 代码审查
  - 前置验证：调用 superpowers:verification-before-completion 运行全量测试，确认输出干净后才继续
  - 调用 superpowers:requesting-code-review 审查本任务组所有变更
  - 若存在 Critical/Important 问题：输出审查结果后停止等待用户输入
  - 若仅有 Minor 或无问题：自动继续下一任务组

## 6. PreCI 代码规范检查

- [x] 6.1 检测 preci 安装状态
- [x] 6.2 检测项目是否已 preci 初始化
- [x] 6.3 检测 PreCI Server 状态
- [x] 6.4 执行代码规范扫描
- [x] 6.5 处理扫描结果

## 7. Documentation Sync (Required)

- [x] 7.1 sync design.md: record technical decisions, deviations, and implementation details after each code change
- [x] 7.2 sync tasks.md: 逐一检查所有顶层任务及其子任务，将已完成但仍为 `[ ]` 的条目标记为 `[x]`；每次更新只修改 `[ ]` → `[x]`，禁止修改任何任务描述文字
- [x] 7.3 sync proposal.md: update scope/impact if changed
- [x] 7.4 sync specs/*.md: update requirements if changed
- [x] 7.5 Final review: ensure all OpenSpec docs reflect actual implementation
