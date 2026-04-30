## ADDED Requirements

### Requirement: Decision Component Directory Reorganization

All decision components shall be organized under `component/decision/` with company and folk subdirectories.

#### Scenario: Company decision components relocated
- **WHEN** the module structure is reorganized
- **THEN** `BaseCompanyDecisionComponent` is importable from `component.decision.company.base`
- **AND** `ClassicCompanyDecisionComponent` is importable from `component.decision.company.classic`
- **AND** `AICompanyDecisionComponent` is importable from `component.decision.company.ai`
- **AND** the old top-level files (`component/base_company_decision.py`, etc.) no longer exist
- **AND** all existing import paths in system/, game/, and tests/ are updated to the new paths
- **AND** all 514 existing tests pass after migration

### Requirement: Folk Decision Component

A decision component pattern for Folk entities that provides spending decisions (budget + demand per goods type).

#### Scenario: BaseFolkDecisionComponent abstract API
- **WHEN** a Folk entity has a `BaseFolkDecisionComponent` attached
- **THEN** the component provides an abstract `decide_spending()` method
- **AND** `decide_spending()` returns `Dict[str, Dict]` where each entry maps goods_type_name to `{"budget": int, "demand": int}`
- **AND** the component receives decision context via `set_context()`

#### Scenario: ClassicFolkDecisionComponent spending decision
- **WHEN** a Folk entity has a `ClassicFolkDecisionComponent` and `decide_spending()` is called
- **THEN** demand is calculated as `population * per_capita * (1 + economy_cycle_index * sensitivity)` per goods type
- **AND** budget is calculated as `demand * reference_price * spending_tendency` per goods type
- **AND** spending_tendency is derived from Folk's existing w_* weights and economy context
- **AND** goods types with `per_capita == 0` have demand=0 and budget=0

### Requirement: Enterprise Spending Flow to Residents

Enterprise spending on tech, brand, and maintenance shall partially flow to Folk groups based on configurable ratios.

#### Scenario: Spending flow configuration
- **WHEN** `folk.yaml` contains a `spending_flow` section with `tech`, `brand`, and `maintenance` entries
- **THEN** each entry has a `total_ratio` (fraction of enterprise spending that flows to residents)
- **AND** each entry has a `groups` mapping with allocation ratios per Folk group
- **AND** loading validates that the sum of all group ratios for each spending type equals 1.0 (within floating point tolerance)

#### Scenario: Tech spending flows to residents
- **WHEN** a company invests in tech during act_phase
- **THEN** `tech_amount * total_ratio` is distributed to Folk groups based on the configured group ratios
- **AND** each Folk group's `LedgerComponent.cash` increases by its share
- **AND** the remaining `(1 - total_ratio) * tech_amount` still updates `tech_values` as before

#### Scenario: Brand spending flows to residents
- **WHEN** a company invests in brand during act_phase
- **THEN** `brand_amount * total_ratio` is distributed to Folk groups based on the configured group ratios
- **AND** each Folk group's `LedgerComponent.cash` increases by its share

#### Scenario: Maintenance cost deducted and flows to residents
- **WHEN** a company has built factories with maintenance costs during act_phase
- **THEN** the total maintenance cost is deducted from the company's `LedgerComponent.cash`
- **AND** `maintenance_amount * total_ratio` is distributed to Folk groups based on the configured group ratios

### Requirement: FolkService Integration with Decision Components

FolkService shall use FolkDecisionComponent for spending decisions instead of hardcoded logic.

#### Scenario: FolkService uses decision component for spending
- **WHEN** `FolkService.buy_phase()` is called
- **THEN** each Folk's decision component's `decide_spending()` is called to get the spending plan
- **AND** the spending plan provides both demand quantities and budget constraints for purchasing
- **AND** purchasing respects both the demand and budget limits (buys min of what's demanded and what's affordable)

#### Scenario: Folk entities have decision components attached
- **WHEN** Folk entities are created via `load_folks()`
- **THEN** each Folk entity has a `ClassicFolkDecisionComponent` attached by default
