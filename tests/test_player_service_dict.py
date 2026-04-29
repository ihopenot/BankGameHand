"""PlayerService *_dict() 方法单元测试。"""
from __future__ import annotations

from game.game import Game
from core.types import LoanApplication


class TestEconomySummaryDict:
    def test_returns_round_info(self):
        game = Game()
        game.round = 3
        result = game.player_service.economy_summary_dict()
        assert result["round"] == 3
        assert result["total_rounds"] == game.total_rounds

    def test_returns_economy_index(self):
        game = Game()
        game.round = 1
        game.economy_service.update_phase()
        result = game.player_service.economy_summary_dict()
        assert "economy_index" in result
        assert isinstance(result["economy_index"], float)
        # economy_index should be rounded to 4 decimal places
        assert result["economy_index"] == round(result["economy_index"], 4)


class TestCompanyTableDict:
    def test_returns_list(self):
        game = Game()
        result = game.player_service.company_table_dict()
        assert isinstance(result, list)
        assert len(result) == len(game.company_service.companies)

    def test_company_entry_fields(self):
        game = Game()
        result = game.player_service.company_table_dict()
        entry = result[0]
        assert "name" in entry
        assert "factory_types" in entry
        assert "factory_count" in entry
        assert "cash" in entry
        assert "wage" in entry
        assert "hired_labor_points" in entry
        assert "tech" in entry
        assert "brand" in entry
        assert "prices" in entry
        assert "inventory" in entry
        assert "receivables" in entry
        assert "payables" in entry
        assert isinstance(entry["factory_count"], int)
        assert isinstance(entry["cash"], int)
        assert isinstance(entry["tech"], (int, float))
        assert isinstance(entry["brand"], (int, float))


class TestFolkTableDict:
    def test_returns_list(self):
        game = Game()
        result = game.player_service.folk_table_dict()
        assert isinstance(result, list)
        assert len(result) == len(game.folks)

    def test_folk_entry_fields(self):
        game = Game()
        result = game.player_service.folk_table_dict()
        entry = result[0]
        assert "name" in entry
        assert "population" in entry
        assert "cash" in entry
        assert "w_quality" in entry
        assert "w_brand" in entry
        assert "w_price" in entry
        assert "inventory" in entry


class TestBankSummaryDict:
    def test_returns_list(self):
        game = Game()
        result = game.player_service.bank_summary_dict(game.bank_service.banks)
        assert isinstance(result, list)
        assert len(result) == len(game.bank_service.banks)

    def test_bank_entry_fields(self):
        game = Game()
        result = game.player_service.bank_summary_dict(game.bank_service.banks)
        entry = result[0]
        assert "name" in entry
        assert "cash" in entry
        assert "total_loans" in entry
        assert "interest_income" in entry


class TestLoanApplicationsDict:
    def test_empty_applications(self):
        game = Game()
        result = game.player_service.loan_applications_dict(
            [], game.company_service.companies
        )
        assert isinstance(result, list)
        assert len(result) == 0

    def test_with_applications(self):
        game = Game()
        company = list(game.company_service.companies.values())[0]
        company_name = list(game.company_service.companies.keys())[0]
        app = LoanApplication(applicant=company, amount=50000)
        result = game.player_service.loan_applications_dict(
            [app], game.company_service.companies
        )
        assert len(result) == 1
        assert result[0]["index"] == 1
        assert result[0]["company_name"] == company_name
        assert result[0]["amount"] == 50000
