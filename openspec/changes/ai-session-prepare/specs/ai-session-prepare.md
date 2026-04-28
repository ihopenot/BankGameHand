## ADDED Requirements

### Requirement: AI Session Pool

AI 决策组件维护一个类级别 session 池，为每个 AI 公司保存预先准备的 AgentSession。

#### Scenario: Prepare session for AI company
- **WHEN** `prepare_session` 被调用并传入公司名称
- **THEN** 调用 `sdk.prepare(config)` 创建 AgentSession 并存入 session 池

#### Scenario: Prepare sessions for next round
- **WHEN** `prepare_next_sessions` 被调用并传入公司名称列表
- **THEN** 对所有 AI 公司并行调用 `prepare_session`

### Requirement: Two-phase AI Decision Call

AI 决策调用拆分为 prepare 和 query 两阶段。

#### Scenario: Query AI with prepared session
- **WHEN** `plan_phase` 调用 AI 公司决策且 session 池中存在该公司的 session
- **THEN** 使用 `sdk.do_query(session, prompt)` 发送 prompt 并获取结果，session 自动关闭

#### Scenario: Fallback when session unavailable
- **WHEN** `plan_phase` 调用 AI 公司决策但 session 池中无可用 session
- **THEN** 回退到 `sdk.run_agent(config)` 作为兜底

### Requirement: Parallel AI Decision Execution

DecisionService.plan_phase 中所有 AI 公司的决策调用并行执行。

#### Scenario: Parallel do_query for all AI companies
- **WHEN** `plan_phase` 被调用且有多个 AI 公司
- **THEN** 使用 `asyncio.gather` 并行调用所有 AI 公司的 `do_query`

### Requirement: Round-over-round Session Preparation

每轮 AI 决策完成后立即 prepare 下一轮的 session，与后续游戏阶段（含玩家操作）重叠。

#### Scenario: Prepare next round after plan_phase
- **WHEN** `plan_phase` 完成所有 AI 决策调用
- **THEN** 立即调用 `prepare_next_round` 为所有 AI 公司 prepare 下一轮 session

#### Scenario: First round preparation
- **WHEN** 游戏循环开始前
- **THEN** 调用 `prepare_next_round` 为所有 AI 公司 prepare 首轮 session

### Requirement: Session Cleanup on Game End

游戏结束时清理所有残留 session 和 SDK 资源。

#### Scenario: Cleanup on game end
- **WHEN** 游戏循环结束
- **THEN** 关闭所有未使用的 prepared session，调用 SDK shutdown
