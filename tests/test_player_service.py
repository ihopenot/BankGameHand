"""Tests for PlayerService."""
from __future__ import annotations

from typing import List

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.input_controller import PlayerInputController
from entity.company.company import Company
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsBatch, GoodsType
from system.player_service import PlayerService


# ── Mock 输入控制器 ──

class MockInputController(PlayerInputController):
    """测试用输入控制器，按顺序返回预设的输入。"""

    def __init__(self, inputs: List[str]) -> None:
        self.inputs = list(inputs)
        self.call_count = 0

    def get_input(self, prompt: str) -> str:
        result = self.inputs[self.call_count]
        self.call_count += 1
        return result


# ── 辅助工厂方法 ──

def _make_goods_type(name: str = "TestGoods") -> GoodsType:
    return GoodsType(name=name, base_price=100, bonus_ceiling=0.1)


def _make_factory_type(gt: GoodsType) -> FactoryType:
    recipe = Recipe(input_goods_type=None, input_quantity=0, output_goods_type=gt, output_quantity=10)
    return FactoryType(recipe=recipe, base_production=1, build_cost=1000, maintenance_cost=50, build_time=0)


def _make_company(cash: int = 10000, factory_type: FactoryType | None = None) -> Company:
    company = Company()
    ledger = company.get_component(LedgerComponent)
    ledger.cash = cash
    if factory_type is not None:
        pc = company.get_component(ProductorComponent)
        factory = Factory(factory_type, build_remaining=0)
        pc.factories[factory_type].append(factory)
    return company


class FakeGame:
    """最小化的 Game 替身，供 PlayerService 测试使用。"""

    def __init__(self, companies, round_number=1, total_rounds=10, economy_index=0):
        self.company_service = type("CS", (), {"companies": companies})()
        self.economy_service = type("ES", (), {"economy_index": economy_index})()
        self.round = round_number
        self.total_rounds = total_rounds


class TestFormatEconomySummary:
    def test_contains_round_info(self) -> None:
        companies = {"c0": _make_company()}
        game = FakeGame(companies, round_number=3, total_rounds=20, economy_index=1523)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_economy_summary()
        assert "3" in result
        assert "20" in result

    def test_contains_economy_index(self) -> None:
        companies = {"c0": _make_company()}
        game = FakeGame(companies, round_number=1, total_rounds=10, economy_index=1523)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_economy_summary()
        assert "0.1523" in result

    def test_negative_economy_index(self) -> None:
        companies = {"c0": _make_company()}
        game = FakeGame(companies, round_number=1, total_rounds=10, economy_index=-3000)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_economy_summary()
        assert "-0.3000" in result


class TestFormatCompanyTable:
    def test_contains_company_name(self) -> None:
        gt = _make_goods_type("Silicon")
        ft = _make_factory_type(gt)
        companies = {"company_0": _make_company(cash=15000, factory_type=ft)}
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_company_table()
        assert "company_0" in result

    def test_contains_factory_type(self) -> None:
        gt = _make_goods_type("Silicon")
        ft = _make_factory_type(gt)
        companies = {"company_0": _make_company(cash=15000, factory_type=ft)}
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_company_table()
        assert "Silicon" in result

    def test_contains_cash(self) -> None:
        gt = _make_goods_type("Silicon")
        ft = _make_factory_type(gt)
        companies = {"company_0": _make_company(cash=15000, factory_type=ft)}
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_company_table()
        assert "15000" in result

    def test_contains_inventory_info(self) -> None:
        gt = _make_goods_type("Chips")
        ft = _make_factory_type(gt)
        company = _make_company(cash=5000, factory_type=ft)
        storage = company.get_component(StorageComponent)
        storage.add_batch(GoodsBatch(goods_type=gt, quantity=200, quality=0.5, brand_value=10))
        companies = {"company_1": company}
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_company_table()
        assert "Chips" in result
        assert "200" in result

    def test_contains_receivables_and_payables(self) -> None:
        gt = _make_goods_type("Wheat")
        ft = _make_factory_type(gt)
        company = _make_company(cash=8000, factory_type=ft)
        ledger = company.get_component(LedgerComponent)
        from core.types import Loan, LoanType, RepaymentType
        other = _make_company()
        loan = Loan(creditor=company, debtor=other, principal=3000, rate=0, term=1,
                    loan_type=LoanType.TRADE_PAYABLE, repayment_type=RepaymentType.BULLET)
        ledger.receivables.append(loan)
        companies = {"company_2": company}
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_company_table()
        assert "3000" in result

    def test_empty_inventory_shows_dash(self) -> None:
        companies = {"company_3": _make_company(cash=1000)}
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_company_table()
        assert "-" in result

    def test_multiple_companies(self) -> None:
        gt = _make_goods_type("Food")
        ft = _make_factory_type(gt)
        companies = {
            "company_a": _make_company(cash=1000, factory_type=ft),
            "company_b": _make_company(cash=2000, factory_type=ft),
        }
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        result = service.format_company_table()
        assert "company_a" in result
        assert "company_b" in result


class TestPlayerActPhase:
    def test_skip_command(self) -> None:
        companies = {"c0": _make_company()}
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        service.player_act_phase()

    def test_empty_input_skips(self) -> None:
        companies = {"c0": _make_company()}
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController([""])
        service.player_act_phase()

    def test_invalid_then_skip(self, capsys) -> None:
        companies = {"c0": _make_company()}
        game = FakeGame(companies)
        service = PlayerService(game)
        service.input_controller = MockInputController(["invalid_cmd", "skip"])
        service.player_act_phase()
        captured = capsys.readouterr()
        assert "无法识别" in captured.out

    def test_prints_economy_and_company_info(self, capsys) -> None:
        gt = _make_goods_type("Gold")
        ft = _make_factory_type(gt)
        companies = {"company_0": _make_company(cash=5000, factory_type=ft)}
        game = FakeGame(companies, round_number=2, total_rounds=10, economy_index=500)
        service = PlayerService(game)
        service.input_controller = MockInputController(["skip"])
        service.player_act_phase()
        captured = capsys.readouterr()
        assert "第 2 / 10 回合" in captured.out
        assert "company_0" in captured.out
