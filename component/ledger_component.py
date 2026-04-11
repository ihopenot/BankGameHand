from typing import List
from core.types import Loan

class LedgerComponent:
    cash: int
    loans: List[Loan]
    deposit: List[Loan]