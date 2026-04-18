"""LoanApplication 数据类型单元测试。"""

from core.entity import Entity
from core.types import LoanApplication


class TestLoanApplication:
    def test_create_loan_application(self):
        applicant = Entity()
        app = LoanApplication(applicant=applicant, amount=100_000)
        assert app.applicant is applicant
        assert app.amount == 100_000

    def test_loan_application_zero_amount(self):
        applicant = Entity()
        app = LoanApplication(applicant=applicant, amount=0)
        assert app.amount == 0
