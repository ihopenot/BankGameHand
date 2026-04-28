## Why

AI 决策调用采用串行 `run_agent()` 方式，每个 AI 公司的 LLM 调用包含子进程启动（冷启动）+ prompt 发送 + 推理。N 个 AI 公司导致玩家等待 N × (启动 + 推理) 时间。

## What Changes

利用 MCPAgentSDK 的 `prepare()` + `do_query()` API 将子进程启动与 prompt 发送解耦：
- `prepare()` 提前启动子进程，不发送 prompt
- `do_query()` 在已准备好的 session 上发送 prompt 并获取结果
- AI 调用从串行改为并行（`asyncio.gather`）
- 每轮 `do_query` 完成后立刻 `prepare` 下一轮 session，与玩家操作时间重叠

## Impact

- `component/ai_company_decision.py` — 新增 session 池、两阶段 AI 调用
- `system/decision_service.py` — 并行化 plan_phase、新增 prepare_next_round
- `game/game.py` — 初始化预热和游戏结束清理
- MCPAgentSDK 依赖升级至含 `prepare`/`do_query` 的版本
