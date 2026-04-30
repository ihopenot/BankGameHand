"""PlayerService 终端展示与 PlayerAction 单元测试。"""

from unittest.mock import MagicMock

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.input_controller import PlayerInputController, _parse_approvals
from core.types import (
    Loan, LoanApplication, LoanApprovalParam, LoanType,
    PlayerAction, RATE_SCALE, RepaymentType,
)
from entity.bank import Bank
from entity.company.company import Company
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsBatch, GoodsType
from system.bank_service import BankService, LoanOffer
from system.player_service import PlayerService


class FakeInputController(PlayerInputController):
    """测试用输入控制器，按序返回预设输入。"""

    def __init__(self, inputs):
        self._inputs = list(inputs)
        self._index = 0

    def get_input(self, prompt: str) -> str:
        if self._index < len(self._inputs):
            val = self._inputs[self._index]
            self._index += 1
            return val
        return "skip"


def _make_player_service():
    """创建带有 mock Game 的 PlayerService。"""
    game = MagicMock()
    game.round = 1
    game.total_rounds = 20
    game.economy_service.economy_index = int(0.5 * RATE_SCALE)
    game.company_service.companies = {}
    return PlayerService(game)


def _make_company_with_price():
    """创建有工厂和定价的公司。"""
    gt = GoodsType(name="硅", base_price=1000)
    recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt, output_quantity=100, tech_quality_weight=1.0)
    ft = FactoryType(recipe=recipe, labor_demand=50, build_cost=50000, maintenance_cost=3000, build_time=2)
    company = Company(name="test_company")
    company.wage = 10
    pc = company.get_component(ProductorComponent)
    pc.factories[ft].append(Factory(ft, build_remaining=0))
    pc.prices[gt] = 1200
    pc.tech_values[recipe] = 500
    pc.brand_values[gt] = 300
    ledger = company.get_component(LedgerComponent)
    ledger.cash = 100_000
    return company, gt, recipe


class TestFormatCompanyTable:
    def test_includes_pricing(self):
        svc = _make_player_service()
        company, gt, _ = _make_company_with_price()
        svc.game.company_service.companies = {"company_0": company}
        table = svc.format_company_table()
        assert "定价" in table
        assert "1200" in table

    def test_includes_tech_brand_factory_count(self):
        svc = _make_player_service()
        company, gt, recipe = _make_company_with_price()
        svc.game.company_service.companies = {"company_0": company}
        table = svc.format_company_table()
        assert "科技" in table
        assert "品牌" in table
        assert "开工" in table
        assert "停工" in table
        assert "在建" in table
        # tech=500, brand=300
        assert "500" in table
        assert "300" in table

    def test_multiple_products(self):
        svc = _make_player_service()
        gt1 = GoodsType(name="硅", base_price=1000)
        gt2 = GoodsType(name="芯片", base_price=5000)
        recipe1 = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt1, output_quantity=100, tech_quality_weight=1.0)
        ft1 = FactoryType(recipe=recipe1, labor_demand=50, build_cost=50000, maintenance_cost=3000, build_time=2)
        company = Company(name="multi_product_company")
        company.wage = 10
        pc = company.get_component(ProductorComponent)
        pc.factories[ft1].append(Factory(ft1, build_remaining=0))
        pc.prices[gt1] = 1200
        pc.prices[gt2] = 5500
        company.get_component(LedgerComponent).cash = 100_000
        svc.game.company_service.companies = {"company_0": company}
        table = svc.format_company_table()
        assert "1200" in table
        assert "5500" in table


class TestFormatBankSummary:
    def test_basic(self):
        svc = _make_player_service()
        bank = Bank()
        bank.get_component(LedgerComponent).cash = 500_000
        output = svc.format_bank_summary({"银行A": bank})
        assert "银行A" in output
        assert "500000" in output

    def test_with_loans(self):
        svc = _make_player_service()
        bank = Bank()
        bank.get_component(LedgerComponent).cash = 400_000
        company = Company(name="debtor")
        loan = Loan(
            creditor=bank, debtor=company, principal=100_000,
            rate=500, term=5, loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        bank.get_component(LedgerComponent).receivables.append(loan)
        output = svc.format_bank_summary({"银行A": bank})
        assert "100000" in output


class TestFormatActiveLoans:
    def test_display(self):
        svc = _make_player_service()
        bank = Bank()
        company = Company(name="debtor")
        loan = Loan(
            creditor=bank, debtor=company, principal=100_000,
            rate=500, term=5, loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.EQUAL_PRINCIPAL,
        )
        output = svc.format_active_loans([loan])
        assert "100000" in output
        assert "500" in output

    def test_no_loans(self):
        svc = _make_player_service()
        output = svc.format_active_loans([])
        assert "暂无" in output


class TestFormatLoanApplications:
    def test_display(self):
        svc = _make_player_service()
        company = Company(name="applicant")
        app = LoanApplication(applicant=company, amount=80_000)
        output = svc.format_loan_applications([app], {"company_0": company})
        assert "80000" in output
        assert "company_0" in output

    def test_no_applications(self):
        svc = _make_player_service()
        output = svc.format_loan_applications([], {})
        assert "暂无" in output


# ── PlayerAction 解析测试 ──


class TestParseApprovals:
    def test_single_approval(self):
        result = _parse_approvals(["1:50000:500:5:1"])
        assert len(result) == 1
        assert result[0].application_index == 1
        assert result[0].amount == 50_000
        assert result[0].rate == 500
        assert result[0].term == 5
        assert result[0].repayment_type == RepaymentType.EQUAL_PRINCIPAL

    def test_multiple_approvals(self):
        result = _parse_approvals(["1:50000:500:5:1", "2:30000:800:3:2"])
        assert len(result) == 2
        assert result[1].application_index == 2
        assert result[1].repayment_type == RepaymentType.INTEREST_FIRST

    def test_default_repayment_type(self):
        result = _parse_approvals(["1:50000:500:5"])
        assert len(result) == 1
        assert result[0].repayment_type == RepaymentType.EQUAL_PRINCIPAL

    def test_invalid_token_skipped(self):
        result = _parse_approvals(["bad", "1:50000:500:5:1"])
        assert len(result) == 1


class TestGetAction:
    def test_skip(self):
        ctrl = FakeInputController(["skip"])
        action = ctrl.get_action("prompt: ")
        assert action.action_type == "skip"

    def test_empty_is_skip(self):
        ctrl = FakeInputController([""])
        action = ctrl.get_action("prompt: ")
        assert action.action_type == "skip"

    def test_approve(self):
        ctrl = FakeInputController(["approve 银行A 1:50000:500:5:1"])
        action = ctrl.get_action("prompt: ")
        assert action.action_type == "approve_loans"
        assert action.bank_name == "银行A"
        assert len(action.approvals) == 1
        assert action.approvals[0].amount == 50_000

    def test_approve_multiple(self):
        ctrl = FakeInputController(["approve 银行A 1:50000:500:5:1 2:30000:800:3:2"])
        action = ctrl.get_action("prompt: ")
        assert len(action.approvals) == 2


# ── PlayerAction 审批处理测试 ──


class TestHandleLoanApproval:
    def _setup(self):
        svc = _make_player_service()
        bank_service = BankService()
        bank = bank_service.create_bank("银行A", 500_000)
        company = Company(name="applicant")
        svc.game.company_service.companies = {"company_0": company}
        app = LoanApplication(applicant=company, amount=100_000)
        bank_service.collect_applications([app])
        return svc, bank_service, bank, company

    def test_approve_via_action(self):
        svc, bank_service, bank, company = self._setup()
        action = PlayerAction(
            action_type="approve_loans",
            bank_name="银行A",
            approvals=[
                LoanApprovalParam(
                    application_index=1, amount=100_000,
                    rate=500, term=5,
                    repayment_type=RepaymentType.EQUAL_PRINCIPAL,
                ),
            ],
        )
        svc.handle_loan_approval(action, bank_service)
        offers = bank_service.get_offers()
        assert len(offers) == 1
        assert offers[0].rate == 500
        assert offers[0].amount == 100_000

    def test_skip_has_no_offers(self):
        svc, bank_service, bank, company = self._setup()
        action = PlayerAction(action_type="skip")
        # skip 不调用 handle_loan_approval，所以无 offer
        assert bank_service.get_offers() == []

    def test_amount_limited_by_bank_cash(self):
        svc, bank_service, bank, company = self._setup()
        action = PlayerAction(
            action_type="approve_loans",
            bank_name="银行A",
            approvals=[
                LoanApprovalParam(
                    application_index=1, amount=600_000,
                    rate=500, term=5,
                    repayment_type=RepaymentType.EQUAL_PRINCIPAL,
                ),
            ],
        )
        svc.handle_loan_approval(action, bank_service)
        offers = bank_service.get_offers()
        assert len(offers) == 1
        assert offers[0].amount <= 500_000

    def test_invalid_bank_name(self):
        svc, bank_service, bank, company = self._setup()
        action = PlayerAction(
            action_type="approve_loans",
            bank_name="不存在银行",
            approvals=[
                LoanApprovalParam(
                    application_index=1, amount=50_000,
                    rate=500, term=5,
                    repayment_type=RepaymentType.EQUAL_PRINCIPAL,
                ),
            ],
        )
        svc.handle_loan_approval(action, bank_service)
        assert bank_service.get_offers() == []

    def test_invalid_index_skipped(self):
        svc, bank_service, bank, company = self._setup()
        action = PlayerAction(
            action_type="approve_loans",
            bank_name="银行A",
            approvals=[
                LoanApprovalParam(
                    application_index=99, amount=50_000,
                    rate=500, term=5,
                    repayment_type=RepaymentType.EQUAL_PRINCIPAL,
                ),
            ],
        )
        svc.handle_loan_approval(action, bank_service)
        assert bank_service.get_offers() == []
