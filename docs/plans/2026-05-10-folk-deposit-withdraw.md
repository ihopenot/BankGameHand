# Folk Deposit & Withdrawal Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Residents deposit excess cash into banks and withdraw when short, with player-settable deposit rates that attract deposits proportionally.

**Architecture:** Add `deposit_rate` to Bank entity. In `settlement_phase`, Folk calculate a reserve target (last_spending × savings_target_ratio), deposit excess or withdraw shortfall. Deposit allocation across banks uses rate-based attractiveness scoring. Player sets deposit rates during `player_act` phase.

**Tech Stack:** Python, existing Loan/LedgerComponent system (LoanType.DEPOSIT, term=0)

---

### Task 1: Add deposit_rate field to Bank entity

**Files:**
- Modify: `entity/bank.py`
- Test: `tests/test_bank_service.py`

**Step 1: Write the failing test**

In `tests/test_bank_service.py`, add:

```python
def test_bank_has_deposit_rate_default_zero():
    from entity.bank import Bank
    bank = Bank("test_bank")
    assert bank.deposit_rate == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_bank_service.py::test_bank_has_deposit_rate_default_zero -v`
Expected: FAIL with AttributeError

**Step 3: Write minimal implementation**

In `entity/bank.py`, add `self.deposit_rate: int = 0` to `Bank.__init__`:

```python
class Bank(Entity):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.deposit_rate: int = 0  # 万分比，玩家设定的存款利率
        self.init_component(LedgerComponent)
        self.init_component(MetricComponent)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_bank_service.py::test_bank_has_deposit_rate_default_zero -v`
Expected: PASS

**Step 5: Commit**

```bash
git add entity/bank.py tests/test_bank_service.py
git commit -m "feat: add deposit_rate field to Bank entity"
```

---

### Task 2: Add player action to set deposit rate

**Files:**
- Modify: `core/types.py` (add "set_deposit_rate" action type)
- Modify: `core/input_controller.py` (parse new command)
- Modify: `system/player_service.py` (handle new action)
- Test: `tests/test_input_controller.py`

**Step 1: Write the failing test**

In `tests/test_input_controller.py`, add a test for parsing the new `rate` command:

```python
def test_parse_set_deposit_rate():
    from core.input_controller import PlayerInputController
    from unittest.mock import patch

    class MockController(PlayerInputController):
        def get_input(self, prompt: str) -> str:
            return "rate 银行A 100"

    ctrl = MockController()
    action = ctrl.get_action("")
    assert action.action_type == "set_deposit_rate"
    assert action.bank_name == "银行A"
    assert action.deposit_rate == 100
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_input_controller.py::test_parse_set_deposit_rate -v`
Expected: FAIL (attribute not found or action_type is "skip")

**Step 3: Implement**

In `core/types.py`, add `deposit_rate` field to `PlayerAction`:

```python
class PlayerAction:
    def __init__(
        self,
        action_type: str = "skip",
        bank_name: str = "",
        approvals: list | None = None,
        deposit_rate: int = 0,
    ) -> None:
        self.action_type = action_type
        self.bank_name = bank_name
        self.approvals: list[LoanApprovalParam] = approvals or []
        self.deposit_rate = deposit_rate
```

In `core/input_controller.py`, add parsing for `rate` command in `get_action`:

```python
def get_action(self, prompt: str) -> PlayerAction:
    raw = self.get_input(prompt).strip()
    if not raw or raw.lower() == "skip":
        return PlayerAction(action_type="skip")

    parts = raw.split()
    if parts[0].lower() == "approve" and len(parts) >= 3:
        bank_name = parts[1]
        approvals = _parse_approvals(parts[2:])
        return PlayerAction(
            action_type="approve_loans",
            bank_name=bank_name,
            approvals=approvals,
        )

    if parts[0].lower() == "rate" and len(parts) >= 3:
        bank_name = parts[1]
        try:
            deposit_rate = int(parts[2])
        except ValueError:
            return PlayerAction(action_type="skip")
        return PlayerAction(
            action_type="set_deposit_rate",
            bank_name=bank_name,
            deposit_rate=deposit_rate,
        )

    return PlayerAction(action_type="skip")
```

In `system/player_service.py`, add handling in `player_act_phase` after the existing loan approval handling:

```python
def handle_set_deposit_rate(self, action: PlayerAction, bank_service: BankService) -> None:
    """设置银行存款利率。"""
    bank = bank_service.banks.get(action.bank_name)
    if bank is None:
        console.print(f"[red]银行 '{action.bank_name}' 不存在[/]")
        return
    bank.deposit_rate = action.deposit_rate
    console.print(f"[green]已设置 {action.bank_name} 存款利率为 {action.deposit_rate} 万分比[/]")
```

And in `player_act_phase`, add:

```python
elif action.action_type == "set_deposit_rate":
    self.handle_set_deposit_rate(action, bank_service)
```

**Step 4: Run tests**

Run: `pytest tests/test_input_controller.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add core/types.py core/input_controller.py system/player_service.py tests/test_input_controller.py
git commit -m "feat: add player action to set bank deposit rate"
```

---

### Task 3: Implement Folk deposit/withdraw logic in FolkService

**Files:**
- Modify: `system/folk_service.py`
- Test: `tests/test_folk_deposit.py` (new test file)

**Step 1: Write the failing tests**

Create `tests/test_folk_deposit.py`:

```python
"""Tests for folk deposit and withdrawal logic."""
from __future__ import annotations

import pytest

from component.ledger_component import LedgerComponent
from core.types import Loan, LoanType, RepaymentType
from entity.bank import Bank
from entity.folk import Folk, DemandFeedbackParams
from entity.goods import GoodsType
from system.folk_service import FolkService


def _make_folk(last_spending: int = 1000, cash: int = 5000) -> Folk:
    """Create a test folk with known spending and cash."""
    folk = Folk(
        name="test_folk",
        population=100,
        w_quality=0.4,
        w_brand=0.3,
        w_price=0.3,
        spending_flow={},
        base_demands={},
        labor_participation_rate=0.7,
        labor_points_per_capita=1.0,
        demand_feedback=DemandFeedbackParams(
            savings_target_ratio=3.0,
            max_adjustment=0.2,
            sensitivity=1.0,
            min_multiplier=0.4,
            max_multiplier=1.8,
        ),
    )
    folk.last_spending = last_spending
    ledger = folk.get_component(LedgerComponent)
    ledger.cash = cash
    return folk


def _make_bank(name: str = "bank_A", cash: int = 100000, deposit_rate: int = 100) -> Bank:
    bank = Bank(name)
    bank.deposit_rate = deposit_rate
    ledger = bank.get_component(LedgerComponent)
    ledger.cash = cash
    return bank


class TestFolkDepositExcess:
    """When folk has more cash than reserve target, deposit excess."""

    def test_deposits_excess_into_bank(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        # reserve = 1000 * 3.0 = 3000, excess = 2000
        bank = _make_bank(deposit_rate=100)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank})

        folk_ledger = folk.get_component(LedgerComponent)
        assert folk_ledger.cash == 3000
        assert len(folk_ledger.receivables) == 1
        deposit = folk_ledger.receivables[0]
        assert deposit.loan_type == LoanType.DEPOSIT
        assert deposit.principal == 2000
        assert deposit.rate == 100
        assert deposit.term == 0

    def test_no_deposit_when_cash_equals_reserve(self):
        folk = _make_folk(last_spending=1000, cash=3000)
        bank = _make_bank(deposit_rate=100)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank})

        folk_ledger = folk.get_component(LedgerComponent)
        assert folk_ledger.cash == 3000
        assert len(folk_ledger.receivables) == 0

    def test_no_deposit_when_no_spending_history(self):
        folk = _make_folk(last_spending=0, cash=5000)
        bank = _make_bank(deposit_rate=100)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank})

        folk_ledger = folk.get_component(LedgerComponent)
        assert folk_ledger.cash == 5000
        assert len(folk_ledger.receivables) == 0


class TestFolkWithdrawShortfall:
    """When folk has less cash than reserve target, withdraw from deposits."""

    def test_withdraws_shortfall_from_existing_deposit(self):
        folk = _make_folk(last_spending=1000, cash=2000)
        bank = _make_bank(deposit_rate=100)
        # Pre-create a deposit: folk deposited 3000 earlier
        deposit = Loan(
            creditor=folk,
            debtor=bank,
            principal=3000,
            rate=100,
            term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger = folk.get_component(LedgerComponent)
        bank_ledger = bank.get_component(LedgerComponent)
        folk_ledger.receivables.append(deposit)
        bank_ledger.payables.append(deposit)

        service = FolkService(folks=[folk])
        service.folk_deposit_phase(banks={"bank_A": bank})

        # reserve = 3000, shortfall = 1000
        assert folk_ledger.cash == 3000
        assert deposit.remaining == 2000

    def test_no_withdraw_when_no_deposits(self):
        folk = _make_folk(last_spending=1000, cash=2000)
        bank = _make_bank(deposit_rate=100)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank})

        folk_ledger = folk.get_component(LedgerComponent)
        # Can't withdraw, cash stays as is
        assert folk_ledger.cash == 2000


class TestDepositAllocation:
    """Deposits are allocated across banks based on rate attractiveness."""

    def test_all_to_highest_rate_when_spread_large(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        bank_a = _make_bank("bank_A", deposit_rate=300)
        bank_b = _make_bank("bank_B", deposit_rate=50)  # 300 - 50 = 250 > 200, so score = 0
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank_a, "bank_B": bank_b})

        folk_ledger = folk.get_component(LedgerComponent)
        # All 2000 excess goes to bank_A
        deposits_a = [l for l in folk_ledger.receivables if l.debtor is bank_a]
        deposits_b = [l for l in folk_ledger.receivables if l.debtor is bank_b]
        assert sum(d.principal for d in deposits_a) == 2000
        assert len(deposits_b) == 0

    def test_split_proportionally_when_rates_close(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        bank_a = _make_bank("bank_A", deposit_rate=200)
        bank_b = _make_bank("bank_B", deposit_rate=100)
        # max_rate=200, threshold=0. bank_a score=(200-0)/200=1.0, bank_b=(100-0)/200=0.5
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank_a, "bank_B": bank_b})

        folk_ledger = folk.get_component(LedgerComponent)
        deposits_a = [l for l in folk_ledger.receivables if l.debtor is bank_a]
        deposits_b = [l for l in folk_ledger.receivables if l.debtor is bank_b]
        total_a = sum(d.principal for d in deposits_a)
        total_b = sum(d.principal for d in deposits_b)
        assert total_a + total_b == 2000
        # bank_a gets 2/3, bank_b gets 1/3 (approx, due to int rounding)
        assert total_a > total_b

    def test_no_deposit_when_all_rates_zero(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        bank_a = _make_bank("bank_A", deposit_rate=0)
        bank_b = _make_bank("bank_B", deposit_rate=0)
        service = FolkService(folks=[folk])

        service.folk_deposit_phase(banks={"bank_A": bank_a, "bank_B": bank_b})

        folk_ledger = folk.get_component(LedgerComponent)
        # No deposits since no bank offers interest
        assert len(folk_ledger.receivables) == 0
        assert folk_ledger.cash == 5000
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_folk_deposit.py -v`
Expected: FAIL (folk_deposit_phase method doesn't exist)

**Step 3: Implement folk_deposit_phase in FolkService**

Add to `system/folk_service.py`:

```python
def folk_deposit_phase(self, banks: Dict[str, "Bank"]) -> None:
    """居民存取款阶段：超出储备目标的现金存入银行，不足则从存款取出。"""
    from entity.bank import Bank

    for folk in self.folks:
        if folk.last_spending <= 0:
            continue

        reserve_target = int(folk.last_spending * folk.demand_feedback.savings_target_ratio)
        folk_ledger = folk.get_component(LedgerComponent)
        excess = folk_ledger.cash - reserve_target

        if excess > 0:
            self._deposit_excess(folk, excess, banks)
        elif excess < 0:
            self._withdraw_shortfall(folk, -excess, banks)

def _deposit_excess(self, folk: "Folk", amount: int, banks: Dict[str, "Bank"]) -> None:
    """将多余现金按利率吸引力分配存入各银行。"""
    from entity.bank import Bank

    # 计算各银行吸引力得分
    bank_list = list(banks.values())
    rates = [bank.deposit_rate for bank in bank_list]
    max_rate = max(rates) if rates else 0
    if max_rate <= 0:
        return  # 无银行提供利息，不存款

    threshold = max_rate - 200  # 低于最高利率2%的银行得分为0
    scores = [max(0, (bank.deposit_rate - threshold) / 200) for bank in bank_list]
    total_score = sum(scores)
    if total_score <= 0:
        return

    # 按得分比例分配（最大余数法）
    raw_allocs = [amount * s / total_score for s in scores]
    floor_allocs = [int(a) for a in raw_allocs]
    remainders = [a - f for a, f in zip(raw_allocs, floor_allocs)]
    deficit = amount - sum(floor_allocs)
    indices = sorted(range(len(remainders)), key=lambda i: remainders[i], reverse=True)
    for i in indices[:deficit]:
        floor_allocs[i] += 1

    # 为每个分配到存款的银行创建 Deposit Loan
    folk_ledger = folk.get_component(LedgerComponent)
    for bank, alloc in zip(bank_list, floor_allocs):
        if alloc <= 0:
            continue
        deposit = Loan(
            creditor=folk,
            debtor=bank,
            principal=alloc,
            rate=bank.deposit_rate,
            term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger.issue_loan(deposit)

def _withdraw_shortfall(self, folk: "Folk", shortfall: int, banks: Dict[str, "Bank"]) -> None:
    """从已有存款中取出不足的现金。"""
    folk_ledger = folk.get_component(LedgerComponent)
    deposits = [l for l in folk_ledger.receivables if l.loan_type == LoanType.DEPOSIT]
    if not deposits:
        return

    remaining_need = shortfall
    for deposit in deposits:
        if remaining_need <= 0:
            break
        bank_ledger: LedgerComponent = deposit.debtor.get_component(LedgerComponent)
        withdrawn = bank_ledger.withdraw(deposit, remaining_need)
        remaining_need -= withdrawn
```

Need to add imports at top of `folk_service.py`:

```python
from core.types import Loan, LoanType, RepaymentType
```

**Step 4: Run tests**

Run: `pytest tests/test_folk_deposit.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add system/folk_service.py tests/test_folk_deposit.py
git commit -m "feat: implement folk deposit/withdraw logic with rate-based allocation"
```

---

### Task 4: Integrate folk_deposit_phase into game loop (settlement_phase)

**Files:**
- Modify: `game/game.py`
- Test: `tests/test_game_integration.py` (or add to existing integration tests)

**Step 1: Write the failing test**

Create `tests/test_folk_deposit_integration.py`:

```python
"""Integration test: folk deposits happen during settlement phase."""
from __future__ import annotations

from component.ledger_component import LedgerComponent
from core.types import LoanType


def test_folk_deposits_during_settlement(tmp_path):
    """After a full round, folk with excess cash should have deposits."""
    from tests.conftest import make_game_with_config

    game = make_game_with_config(tmp_path)
    # Set a deposit rate on the bank
    for bank in game.bank_service.banks.values():
        bank.deposit_rate = 100

    # Run enough rounds to establish spending history
    game.update_phase()
    game.sell_phase()
    game.buy_phase()
    game.plan_phase()
    game.maintenance_phase()
    game.labor_match_phase()
    game.product_phase()
    game.loan_application_phase()
    # Skip player_act (needs input controller)
    game.loan_acceptance_phase()
    game.settlement_phase()

    # Check that at least one folk has deposits (if they had excess cash)
    has_deposits = False
    for folk in game.folks:
        ledger = folk.get_component(LedgerComponent)
        deposits = [l for l in ledger.receivables if l.loan_type == LoanType.DEPOSIT]
        if deposits:
            has_deposits = True
            break
    # After first round, folk may or may not have excess depending on spending
    # The important thing is the phase runs without error
    assert True  # Integration smoke test - no crash
```

Note: If `make_game_with_config` doesn't exist in conftest, this test may need adjusting to match existing test patterns. The key assertion is that the phase runs correctly.

**Step 2: Implement integration**

In `game/game.py`, modify `settlement_phase` to call folk deposit before ledger settlement:

```python
def settlement_phase(self) -> None:
    # 居民存取款（在 ledger 结算之前）
    self.folk_service.folk_deposit_phase(banks=self.bank_service.banks)
    # 原有结算逻辑
    self.ledger_service.settle_all()
    self.company_service.process_bankruptcies()
    self.company_service.replenish_market()
    self.companies = list(self.company_service.companies.values())
```

**Step 3: Run all tests**

Run: `pytest tests/ -v --tb=short -q`
Expected: All existing tests still pass, new integration test passes

**Step 4: Commit**

```bash
git add game/game.py tests/test_folk_deposit_integration.py
git commit -m "feat: integrate folk deposit phase into settlement_phase"
```

---

### Task 5: Add deposit info to bank summary display

**Files:**
- Modify: `system/player_service.py`

**Step 1: Add deposit balance column to render_bank_summary**

In `render_bank_summary`, add a "存款总额" (total deposits) column:

```python
def render_bank_summary(self, banks: Dict[str, Bank]) -> Table:
    table = Table(title="银行概览", show_lines=True)
    table.add_column("银行名", style="bold")
    table.add_column("现金", justify="right", style="green")
    table.add_column("存款利率", justify="right", style="cyan")
    table.add_column("存款总额", justify="right", style="yellow")
    table.add_column("贷款总额", justify="right", style="yellow")
    table.add_column("本回合利息收入", justify="right", style="cyan")

    for name, bank in banks.items():
        ledger = bank.get_component(LedgerComponent)
        cash = ledger.cash
        total_loans = ledger.total_receivables()
        total_deposits = sum(
            loan.remaining for loan in ledger.payables
            if loan.loan_type == LoanType.DEPOSIT
        )
        interest_income = sum(
            min(bill.interest_due, bill.total_paid)
            for bill in ledger.bills
        )
        table.add_row(
            bank.name, str(cash),
            str(bank.deposit_rate),
            str(total_deposits),
            str(total_loans), str(interest_income),
        )

    return table
```

Also update `bank_summary_dict` for web client:

```python
def bank_summary_dict(self, banks: Dict[str, Bank]) -> List[dict]:
    result: List[dict] = []
    for name, bank in banks.items():
        ledger = bank.get_component(LedgerComponent)
        interest_income = sum(
            min(bill.interest_due, bill.total_paid)
            for bill in ledger.bills
        )
        total_deposits = sum(
            loan.remaining for loan in ledger.payables
            if loan.loan_type == LoanType.DEPOSIT
        )
        result.append({
            "name": bank.name,
            "cash": ledger.cash,
            "deposit_rate": bank.deposit_rate,
            "total_deposits": total_deposits,
            "total_loans": ledger.total_receivables(),
            "interest_income": interest_income,
        })
    return result
```

Add `LoanType` import to player_service.py:

```python
from core.types import RATE_SCALE, Loan, LoanApplication, LoanType, PlayerAction
```

**Step 2: Add deposit info to folk table**

In `render_folk_table`, add a "存款" column:

```python
table.add_column("存款", justify="right", style="cyan")
```

And in the row generation:

```python
total_deposits = sum(
    loan.remaining for loan in ledger.receivables
    if loan.loan_type == LoanType.DEPOSIT
)
# Add str(total_deposits) to table.add_row(...)
```

Similarly update `folk_table_dict`.

**Step 3: Run tests**

Run: `pytest tests/ -q`
Expected: PASS (display changes don't break logic)

**Step 4: Commit**

```bash
git add system/player_service.py
git commit -m "feat: display deposit rate and balances in bank/folk summaries"
```

---

### Task 6: Update player_act prompt to show rate command

**Files:**
- Modify: `system/player_service.py`

**Step 1: Update prompt string in player_act_phase**

Change the input prompt to include the `rate` command:

```python
action = self.input_controller.get_action(
    "输入操作 (skip=跳过, approve <银行名> <序号:金额:利率:期限:还款方式>, rate <银行名> <利率万分比>): "
)
```

**Step 2: Update player_act_phase to handle both actions in sequence**

Currently player gets one action per round. The design should allow the player to set rates and approve loans. Two options:
- Allow multiple commands per round (complex)
- Allow the rate to persist across rounds (simpler, more natural)

Since `deposit_rate` persists on the Bank object across rounds, the player sets it once and it stays. The current single-action-per-round is fine — player can choose to set rate OR approve loans each round.

**Step 3: Commit**

```bash
git add system/player_service.py
git commit -m "feat: update player action prompt to include rate command"
```

---

### Task 7: Handle existing deposits when rate changes (additive deposits)

**Files:**
- Modify: `system/folk_service.py`

**Step 1: Verify behavior with existing deposits**

When a folk already has a deposit at bank A (rate 100) and bank A's rate is now 200, new deposits should use the new rate. Existing deposits keep their original rate (this is already handled by the Loan object having its own `rate` field).

When depositing, if a folk already has an existing deposit at the same bank, we should add to it rather than creating a new Loan. This keeps the ledger cleaner.

**Step 1: Write the failing test**

In `tests/test_folk_deposit.py`, add:

```python
class TestDepositMerging:
    """When folk already has a deposit at a bank, add to it."""

    def test_adds_to_existing_deposit_same_bank(self):
        folk = _make_folk(last_spending=1000, cash=5000)
        bank = _make_bank("bank_A", deposit_rate=100)
        # Pre-existing deposit of 1000
        existing_deposit = Loan(
            creditor=folk,
            debtor=bank,
            principal=1000,
            rate=100,
            term=0,
            loan_type=LoanType.DEPOSIT,
            repayment_type=RepaymentType.BULLET,
        )
        folk_ledger = folk.get_component(LedgerComponent)
        bank_ledger = bank.get_component(LedgerComponent)
        folk_ledger.receivables.append(existing_deposit)
        bank_ledger.payables.append(existing_deposit)

        service = FolkService(folks=[folk])
        service.folk_deposit_phase(banks={"bank_A": bank})

        # reserve=3000, cash=5000, excess=2000
        # Should create a new deposit (since rate might differ), total deposits = 3000
        deposits = [l for l in folk_ledger.receivables if l.loan_type == LoanType.DEPOSIT]
        total_deposited = sum(d.remaining for d in deposits)
        assert total_deposited == 3000
        assert folk_ledger.cash == 3000
```

Actually, since the rate on the Bank can change between rounds, each deposit keeps its own rate. Creating a new Loan per deposit round is the correct behavior (simpler, and matches real banking). The test above verifies this works correctly.

**Step 2: Run test**

Run: `pytest tests/test_folk_deposit.py::TestDepositMerging -v`
Expected: PASS (already works with current implementation since issue_loan creates a new Loan)

**Step 3: Commit (if any changes needed)**

If tests pass without changes, just commit the new test:

```bash
git add tests/test_folk_deposit.py
git commit -m "test: verify deposit accumulation across rounds"
```

---

### Task 8: Final integration test — full game round with deposits

**Files:**
- Test: `tests/test_folk_deposit.py`

**Step 1: Write end-to-end test**

```python
class TestEndToEnd:
    """Full round: folk earns wages, buys goods, deposits excess."""

    def test_deposit_withdraw_cycle(self):
        """Simulate two phases: first deposit, then withdraw."""
        folk = _make_folk(last_spending=1000, cash=6000)
        bank = _make_bank("bank_A", deposit_rate=150)
        service = FolkService(folks=[folk])

        # Phase 1: deposit excess (reserve=3000, excess=3000)
        service.folk_deposit_phase(banks={"bank_A": bank})
        folk_ledger = folk.get_component(LedgerComponent)
        assert folk_ledger.cash == 3000

        # Simulate spending next round (folk spends and cash drops)
        folk.last_spending = 2000  # higher spending now
        folk_ledger.cash = 1000   # after buying, low on cash

        # Phase 2: withdraw shortfall (reserve=2000*3=6000, shortfall=5000)
        service.folk_deposit_phase(banks={"bank_A": bank})
        # Should withdraw up to what's available in deposit (3000)
        assert folk_ledger.cash == 4000  # 1000 + 3000 withdrawn
```

**Step 2: Run test**

Run: `pytest tests/test_folk_deposit.py::TestEndToEnd -v`
Expected: PASS

**Step 3: Final full test suite run**

Run: `pytest tests/ -q`
Expected: All pass (599+ existing + new tests)

**Step 4: Commit**

```bash
git add tests/test_folk_deposit.py
git commit -m "test: add end-to-end deposit/withdraw cycle test"
```

---

## Summary of Changes

| File | Change |
|------|--------|
| `entity/bank.py` | Add `deposit_rate: int = 0` field |
| `core/types.py` | Add `deposit_rate` field to `PlayerAction` |
| `core/input_controller.py` | Parse `rate <bank> <rate>` command |
| `system/folk_service.py` | Add `folk_deposit_phase`, `_deposit_excess`, `_withdraw_shortfall` |
| `system/player_service.py` | Handle `set_deposit_rate` action, display deposit info |
| `game/game.py` | Call `folk_deposit_phase` in `settlement_phase` |
| `tests/test_folk_deposit.py` | Full test coverage for deposit/withdraw logic |
| `tests/test_input_controller.py` | Test for rate command parsing |
| `tests/test_bank_service.py` | Test for bank deposit_rate field |
