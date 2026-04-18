"""CompanyService 破产清算与市场补充测试。"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from component.storage_component import StorageComponent
from core.entity import Entity
from core.types import Loan, LoanType, RepaymentType
from entity.company.company import Company
from entity.factory import Factory, FactoryType, Recipe
from entity.goods import GoodsBatch, GoodsType
from system.company_service import CompanyService


def _setup_goods_and_factory() -> FactoryType:
    """创建测试用 GoodsType、Recipe、FactoryType。"""
    if "test_ore" not in GoodsType.types:
        gt = GoodsType.__new__(GoodsType)
        gt.name = "test_ore"
        gt.base_price = 100
        gt.bonus_ceiling = 0.0
        GoodsType.types["test_ore"] = gt
    else:
        gt = GoodsType.types["test_ore"]

    recipe_key = "test_ore_recipe"
    if recipe_key not in Recipe.recipes:
        recipe = Recipe(
            input_goods_type=None,
            input_quantity=0,
            output_goods_type=gt,
            output_quantity=10,
        )
        Recipe.recipes[recipe_key] = recipe
    else:
        recipe = Recipe.recipes[recipe_key]

    ft_key = "test_ore_mine"
    if ft_key not in FactoryType.factory_types:
        ft = FactoryType(
            recipe=recipe,
            base_production=10,
            build_cost=10000,
            maintenance_cost=100,
            build_time=0,
        )
        FactoryType.factory_types[ft_key] = ft
    else:
        ft = FactoryType.factory_types[ft_key]

    return ft


def _make_bankrupt_company(
    cash: int, factory_type: FactoryType, num_factories: int = 1
) -> Company:
    """创建一家已标记破产的公司。"""
    company = Company()
    ledger = company.get_component(LedgerComponent)
    ledger.cash = cash
    ledger.is_bankrupt = True

    pc = company.get_component(ProductorComponent)
    for _ in range(num_factories):
        factory = Factory(factory_type, build_remaining=0)
        pc.factories[factory_type].append(factory)

    return company


def _make_entity(cash: int = 0) -> Entity:
    """创建带 LedgerComponent 的测试实体。"""
    e = Entity()
    e.init_component(LedgerComponent)
    e.get_component(LedgerComponent).cash = cash
    return e


class TestProcessBankruptcies:
    """CompanyService.process_bankruptcies() 测试。"""

    def test_liquidation_proceeds_calculation(self) -> None:
        """清算所得 = 工厂 build_cost × 50% + 现金。"""
        ft = _setup_goods_and_factory()
        # build_cost=10000, 1 factory → 5000; cash=2000 → total=7000
        company = _make_bankrupt_company(cash=2000, factory_type=ft, num_factories=1)

        creditor = _make_entity(cash=0)
        loan = Loan(
            creditor=creditor,
            debtor=company,
            principal=7000,
            rate=0,
            term=1,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.BULLET,
        )
        company_ledger = company.get_component(LedgerComponent)
        creditor_ledger = creditor.get_component(LedgerComponent)
        creditor_ledger.receivables.append(loan)
        company_ledger.payables.append(loan)

        service = CompanyService()
        service.process_bankruptcies()

        # 债权人应收到全部 7000（清算所得刚好够）
        assert creditor_ledger.cash == 7000

    def test_inventory_cleared(self) -> None:
        """破产公司库存应被清空。"""
        ft = _setup_goods_and_factory()
        company = _make_bankrupt_company(cash=0, factory_type=ft)

        storage = company.get_component(StorageComponent)
        gt = GoodsType.types["test_ore"]
        storage.add_batch(GoodsBatch(goods_type=gt, quantity=100, quality=0.5, brand_value=0))

        service = CompanyService()
        service.process_bankruptcies()

        # 公司已被销毁，无法获取组件
        assert company.get_component(StorageComponent) is None

    def test_repayment_priority_trade_before_loan(self) -> None:
        """应付账款（TRADE_PAYABLE）优先于银行贷款（CORPORATE_LOAN）偿还。"""
        ft = _setup_goods_and_factory()
        # build_cost=10000, 1 factory → 5000; cash=1000 → total=6000
        company = _make_bankrupt_company(cash=1000, factory_type=ft)

        supplier = _make_entity(cash=0)
        bank = _make_entity(cash=0)

        trade_debt = Loan(
            creditor=supplier,
            debtor=company,
            principal=4000,
            rate=0,
            term=1,
            loan_type=LoanType.TRADE_PAYABLE,
            repayment_type=RepaymentType.BULLET,
        )
        bank_loan = Loan(
            creditor=bank,
            debtor=company,
            principal=5000,
            rate=0,
            term=1,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.BULLET,
        )

        company_ledger = company.get_component(LedgerComponent)
        supplier_ledger = supplier.get_component(LedgerComponent)
        bank_ledger = bank.get_component(LedgerComponent)

        supplier_ledger.receivables.append(trade_debt)
        company_ledger.payables.append(trade_debt)
        bank_ledger.receivables.append(bank_loan)
        company_ledger.payables.append(bank_loan)

        service = CompanyService()
        service.process_bankruptcies()

        # 供应商应全额收回 4000，银行只能收回 6000-4000=2000
        assert supplier_ledger.cash == 4000
        assert bank_ledger.cash == 2000

    def test_bad_debt_writeoff(self) -> None:
        """清算不足时，未偿还的贷款应被核销（从债权方列表移除）。"""
        ft = _setup_goods_and_factory()
        # build_cost=10000 → 5000; cash=0 → total=5000
        company = _make_bankrupt_company(cash=0, factory_type=ft)

        bank = _make_entity(cash=0)
        loan = Loan(
            creditor=bank,
            debtor=company,
            principal=10000,
            rate=0,
            term=1,
            loan_type=LoanType.CORPORATE_LOAN,
            repayment_type=RepaymentType.BULLET,
        )
        company_ledger = company.get_component(LedgerComponent)
        bank_ledger = bank.get_component(LedgerComponent)
        bank_ledger.receivables.append(loan)
        company_ledger.payables.append(loan)

        service = CompanyService()
        service.process_bankruptcies()

        # 银行只收回 5000，贷款已被核销
        assert bank_ledger.cash == 5000
        assert loan not in bank_ledger.receivables

    def test_company_destroyed_after_liquidation(self) -> None:
        """清算完成后公司实体应被销毁。"""
        ft = _setup_goods_and_factory()
        company = _make_bankrupt_company(cash=0, factory_type=ft)

        service = CompanyService()
        service.process_bankruptcies()

        # 公司组件应已被清空
        assert company.get_component(LedgerComponent) is None
        assert company.get_component(ProductorComponent) is None

    def test_no_recursive_cascade(self) -> None:
        """本回合坏账不应递归触发其他公司破产检查。"""
        ft = _setup_goods_and_factory()

        # 公司 A 破产，欠公司 B 钱
        company_a = _make_bankrupt_company(cash=0, factory_type=ft)
        company_b = Company()
        company_b.get_component(LedgerComponent).cash = 100

        trade_debt = Loan(
            creditor=company_b,
            debtor=company_a,
            principal=50000,
            rate=0,
            term=1,
            loan_type=LoanType.TRADE_PAYABLE,
            repayment_type=RepaymentType.BULLET,
        )
        company_a.get_component(LedgerComponent).payables.append(trade_debt)
        company_b.get_component(LedgerComponent).receivables.append(trade_debt)

        service = CompanyService()
        service.process_bankruptcies()

        # 公司 B 不应被标记破产（即使收到大额坏账）
        company_b_ledger = company_b.get_component(LedgerComponent)
        assert company_b_ledger is not None  # 公司 B 未被销毁
        assert company_b_ledger.is_bankrupt is False

    def test_non_bankrupt_company_not_affected(self) -> None:
        """未标记破产的公司不应被清算。"""
        ft = _setup_goods_and_factory()
        healthy_company = Company()
        healthy_ledger = healthy_company.get_component(LedgerComponent)
        healthy_ledger.cash = 10000
        pc = healthy_company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))

        service = CompanyService()
        service.process_bankruptcies()

        # 正常公司不受影响
        assert healthy_company.get_component(LedgerComponent) is not None
        assert healthy_ledger.cash == 10000


class TestReplenishMarket:
    """CompanyService.replenish_market() 测试。"""

    def setup_method(self) -> None:
        """每个测试前清空全局组件追踪列表，确保隔离。"""
        ProductorComponent.components.clear()
        LedgerComponent.components.clear()
        StorageComponent.components.clear()

    def test_replenish_when_below_threshold(self) -> None:
        """生产者数量低于阈值时应创建新公司。"""
        ft = _setup_goods_and_factory()
        gt = GoodsType.types["test_ore"]

        # 只有 1 家存活公司生产 test_ore，阈值为 2
        company = Company()
        pc = company.get_component(ProductorComponent)
        pc.factories[ft].append(Factory(ft, build_remaining=0))

        service = CompanyService()
        service.companies["existing"] = company

        service.replenish_market()

        # 应该创建了 1 家新公司
        assert len(service.companies) == 2
        # 新公司应有对应的工厂和初始资金
        new_name = [k for k in service.companies if k != "existing"][0]
        new_company = service.companies[new_name]
        new_ledger = new_company.get_component(LedgerComponent)
        assert new_ledger.cash == service._new_company_cash
        new_pc = new_company.get_component(ProductorComponent)
        assert any(
            ft_key.recipe.output_goods_type is gt
            for ft_key, factories in new_pc.factories.items()
            if len(factories) > 0
        )

    def test_no_replenish_when_above_threshold(self) -> None:
        """生产者数量 >= 阈值时不应创建新公司。"""
        ft = _setup_goods_and_factory()

        service = CompanyService()
        for i in range(3):
            c = Company()
            pc = c.get_component(ProductorComponent)
            pc.factories[ft].append(Factory(ft, build_remaining=0))
            service.companies[f"company_{i}"] = c

        service.replenish_market()

        # 不应创建新公司
        assert len(service.companies) == 3

    def test_replenish_creates_multiple_if_needed(self) -> None:
        """多种商品都低于阈值时应分别创建新公司。"""
        ft1 = _setup_goods_and_factory()

        # 创建第二种商品和工厂类型
        gt2_key = "test_gem"
        if gt2_key not in GoodsType.types:
            gt2 = GoodsType.__new__(GoodsType)
            gt2.name = gt2_key
            gt2.base_price = 200
            gt2.bonus_ceiling = 0.0
            GoodsType.types[gt2_key] = gt2
        else:
            gt2 = GoodsType.types[gt2_key]

        recipe2_key = "test_gem_recipe"
        if recipe2_key not in Recipe.recipes:
            recipe2 = Recipe(
                input_goods_type=None,
                input_quantity=0,
                output_goods_type=gt2,
                output_quantity=5,
            )
            Recipe.recipes[recipe2_key] = recipe2
        else:
            recipe2 = Recipe.recipes[recipe2_key]

        ft2_key = "test_gem_mine"
        if ft2_key not in FactoryType.factory_types:
            ft2 = FactoryType(
                recipe=recipe2,
                base_production=5,
                build_cost=20000,
                maintenance_cost=200,
                build_time=0,
            )
            FactoryType.factory_types[ft2_key] = ft2
        else:
            ft2 = FactoryType.factory_types[ft2_key]

        service = CompanyService()
        # 两种商品都只有 1 家生产者
        c1 = Company()
        c1.get_component(ProductorComponent).factories[ft1].append(Factory(ft1, build_remaining=0))
        service.companies["ore_company"] = c1

        c2 = Company()
        c2.get_component(ProductorComponent).factories[ft2].append(Factory(ft2, build_remaining=0))
        service.companies["gem_company"] = c2

        service.replenish_market()

        # 应该分别为两种商品各创建 1 家新公司，总共 4 家
        assert len(service.companies) == 4
