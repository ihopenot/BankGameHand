from __future__ import annotations

from collections import defaultdict
from typing import List, Tuple

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from core.types import Loan, LoanType, RepaymentType
from entity.folk import Folk

# 雇佣关系：(居民组, 公司, 劳动力点数)
HireRecord = Tuple[Folk, object, int]


class LaborService:
    """劳动力市场匹配服务。

    匹配规则：
    - 居民按 labor_points_per_capita 降序聚为 FolkBatch，高技能居民优先受雇
    - 岗位按 wage 降序聚为 WorkBatch，高工资岗位优先被填满
    - 每个 FolkBatch 依次填满 WorkBatch，按供需比例形成 1对1 雇佣关系
    """

    def match(self, companies: list, folks: List[Folk]) -> List[HireRecord]:
        """执行劳动力匹配，返回雇佣关系列表。

        Returns:
            List of (folk, company, labor_points)，表示每条雇佣关系。
        """
        # ── 1. 按 labor_points_per_capita 降序聚类 FolkBatch ──
        folk_groups: dict = defaultdict(list)
        for folk in folks:
            folk_groups[folk.labor_points_per_capita].append(folk)
        folk_batches = sorted(folk_groups.items(), key=lambda x: x[0], reverse=True)

        # ── 2. 按 wage 降序聚类 WorkBatch，计算每个公司的总需求 ──
        company_demand: dict = {}
        for company in companies:
            pc = company.get_component(ProductorComponent)
            demand = sum(
                ft.labor_demand * len(factory_list)
                for ft, factory_list in pc.factories.items()
            )
            if demand > 0:
                company_demand[company] = demand

        work_groups: dict = defaultdict(dict)
        for company, demand in company_demand.items():
            work_groups[company.wage][company] = demand
        work_batches = sorted(work_groups.items(), key=lambda x: x[0], reverse=True)

        # ── 3. 匹配 ──
        # 跟踪每个 folk 和 company 的剩余供给/需求
        folk_remaining: dict = {folk: folk.labor_supply for folk in folks}
        company_remaining: dict = dict(company_demand)
        hire_records: List[HireRecord] = []

        for _ppc, folk_group in folk_batches:
            for _wage, work_group in work_batches:
                # FolkBatch 本批次的总供给
                batch_supply = sum(folk_remaining[f] for f in folk_group if folk_remaining[f] > 0)
                # WorkBatch 本批次的总需求
                batch_demand = sum(company_remaining.get(c, 0) for c in work_group)

                if batch_supply <= 0 or batch_demand <= 0:
                    continue

                # 实际满足量
                filled = min(batch_supply, batch_demand)

                # 按 WorkBatch 内各公司需求比例分配劳动力
                for company, c_demand in work_group.items():
                    c_remaining = company_remaining.get(company, 0)
                    if c_remaining <= 0:
                        continue
                    # 该公司在 WorkBatch 中的占比
                    company_share = int(filled * c_remaining / batch_demand)
                    if company_share <= 0:
                        continue

                    # 按 FolkBatch 内各 Folk 的供给比例分配给这家公司
                    folk_supply_total = sum(folk_remaining[f] for f in folk_group if folk_remaining[f] > 0)
                    if folk_supply_total <= 0:
                        continue

                    for folk in folk_group:
                        f_remaining = folk_remaining[folk]
                        if f_remaining <= 0:
                            continue
                        folk_share = int(company_share * f_remaining / folk_supply_total)
                        if folk_share <= 0:
                            continue
                        hire_records.append((folk, company, folk_share))
                        folk_remaining[folk] -= folk_share

                    company_remaining[company] = max(0, c_remaining - company_share)

        return hire_records

    def apply(self, companies: list, hire_records: List[HireRecord]) -> None:
        """将雇佣关系回写到 ProductorComponent，并生成工资负债。

        Args:
            companies: 企业列表（用于初始化 hired_labor_points = 0）。
            hire_records: match() 返回的雇佣关系列表。
        """
        # 重置所有公司的劳动力点数
        for company in companies:
            company.get_component(ProductorComponent).hired_labor_points = 0

        # 按雇佣关系累加劳动力点数，生成工资负债
        for folk, company, labor_points in hire_records:
            company.get_component(ProductorComponent).hired_labor_points += labor_points

            # 工资 = (劳动力点数 / per_capita) × wage，即按人口单位计算
            wage_units = labor_points / folk.labor_points_per_capita
            wage_amount = int(wage_units * company.wage)
            if wage_amount <= 0:
                continue

            loan = Loan(
                creditor=folk,
                debtor=company,
                principal=wage_amount,
                rate=0,
                term=1,
                loan_type=LoanType.TRADE_PAYABLE,
                repayment_type=RepaymentType.BULLET,
            )
            company.get_component(LedgerComponent).payables.append(loan)
            folk.get_component(LedgerComponent).receivables.append(loan)
