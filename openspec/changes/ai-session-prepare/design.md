## Context

BankGameHand 的 AI 决策组件 (`AICompanyDecisionComponent`) 通过 MCPAgentSDK 调用 LLM 做出定价、投资、贷款决策。当前使用 `run_agent()` API，每次调用包含子进程启动 + prompt 发送 + 推理，且在 `DecisionService.plan_phase()` 中逐个公司串行执行。MCPAgentSDK 已合并 `split-prepare-query` 分支，新增 `prepare()` / `do_query()` API 支持会话预热。

## Goals / Non-Goals

**Goals:**
- 将 AI 调用从串行改为并行，减少 plan_phase 总耗时
- 利用 prepare + do_query 将子进程启动开销与玩家操作时间重叠
- 保持现有决策逻辑和缓存机制不变
- Session 不可用时回退到 run_agent，保证功能不退化

**Non-Goals:**
- 不改变 AI 决策的 prompt 内容和验证逻辑
- 不改变 Classic 决策组件的任何行为
- 不改变游戏循环的阶段顺序
- 不实现跨轮次的 AI 对话历史（session 为一次性的）

## Decisions

1. **Session 池作为类级别属性**：与现有 `_sdk`/`_loop` 类级别属性保持一致，所有 AI 公司共享 SDK 实例和事件循环，session 按公司名索引。

2. **prepare_next_round 在 plan_phase 完成后立即调用**：而非在 player_act 期间调用，确保子进程启动与后续所有阶段（loan_application + player_act + ...）重叠。

3. **回退策略**：session 不存在或 prepare 失败时回退到 run_agent，而非抛出异常中断游戏。这与当前"AI 失败时回退到 Classic"的设计理念一致。

4. **并行实现**：使用 asyncio.gather 在现有 ai-sdk-loop 线程中执行，无需引入额外线程或进程。

5. **plan_phase 并行 query 实现**：`plan_phase` 拆分为三步：① 先构建所有 context 并调用 `BaseCompanyDecisionComponent.set_context`（只设 context 不触发 AI）；② 通过 `AICompanyDecisionComponent.query_all_parallel` 将所有 AI 公司的 query 用 `asyncio.gather` 并行提交到事件循环；③ 回填 `_ai_decisions` 后逐个应用决策结果。同样，`prepare_next_sessions` 也用 `asyncio.gather` 并行 prepare。

6. **_call_ai 保留为兼容委托**：`_call_ai` 方法保留并委托到 `_query_ai`，避免外部引用断裂。

7. **_do_query 使用 _get_sdk 而非 _ensure_sdk_initialized**：do_query 在已 prepared 的 session 上调用，SDK 必然已初始化，无需重复初始化检查。

8. **query_all_parallel 的异常处理**：`asyncio.gather(*tasks, return_exceptions=True)` 确保单个公司 query 失败不会影响其他公司，失败时该公司的 decisions 回退为空 dict。

## Risks / Trade-offs

- **资源消耗**：每个 prepared session 占用一个子进程，N 个 AI 公司 = N 个并存的子进程。在 AI 公司较多时需关注内存占用。
- **Session 过期风险**：如果玩家操作时间过长，prepared session 的子进程可能超时退出。回退机制可兜底。
- **首轮仍有冷启动**：游戏首次 prepare_next_round 需等待所有 session 就绪后才能进入游戏循环。
