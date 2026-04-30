"""地图系统集成测试：Game 初始化后公司正确持有 Plot 引用。"""

from component.ledger_component import LedgerComponent
from component.productor_component import ProductorComponent
from rich.console import Console

from game.game import Game


class TestMapIntegration:
    def test_companies_have_plot_assigned(self):
        game = Game()
        for company in game.companies:
            assert company.plot is not None, f"{company.name} has no plot assigned"
            assert company.plot.name != ""
            assert company.plot.country is not None

    def test_plot_country_chain(self):
        game = Game()
        company = game.companies[0]
        # 电子产业链公司应在硅谷工业区，属于华夏
        assert company.plot.name == "硅谷工业区"
        assert company.plot.country.name == "华夏"

    def test_map_service_loaded(self):
        game = Game()
        assert hasattr(game, 'map_service')
        assert len(game.map_service.countries) == 2
        assert len(game.map_service.plots) == 4

    def test_map_service_query_companies_in_plot(self):
        game = Game()
        companies_in_plot = game.map_service.get_companies_in_plot("硅谷工业区", game.companies)
        # 硅矿场(2) + 芯片工厂(2) + 手机工厂(2) = 6
        assert len(companies_in_plot) == 6

    def test_map_service_query_companies_in_country(self):
        game = Game()
        companies_in_china = game.map_service.get_companies_in_country("华夏", game.companies)
        # 硅谷工业区(6) + 江南纺织区(6) + 北方粮仓(7) = 19
        assert len(companies_in_china) == 19


class TestMapPanel:
    def test_render_map_panel_contains_countries(self):
        game = Game()
        svc = game.player_service
        c = Console(width=200)
        with c.capture() as capture:
            c.print(svc.render_map_panel())
        output = capture.get()
        assert "华夏" in output
        assert "西洋联邦" in output

    def test_render_map_panel_contains_plots(self):
        game = Game()
        svc = game.player_service
        c = Console(width=200)
        with c.capture() as capture:
            c.print(svc.render_map_panel())
        output = capture.get()
        assert "硅谷工业区" in output
        assert "江南纺织区" in output
        assert "北方粮仓" in output
        assert "新大陆科技园" in output

    def test_render_map_panel_contains_company_counts(self):
        game = Game()
        svc = game.player_service
        c = Console(width=200)
        with c.capture() as capture:
            c.print(svc.render_map_panel())
        output = capture.get()
        # 硅谷工业区有6家公司
        assert "6家" in output

    def test_render_map_panel_contains_neighbors(self):
        game = Game()
        svc = game.player_service
        c = Console(width=200)
        with c.capture() as capture:
            c.print(svc.render_map_panel())
        output = capture.get()
        # 硅谷工业区的相邻应显示江南纺织区
        assert "相邻" in output


class TestGovernmentCompanyPlot:
    def test_replenished_company_has_plot(self):
        """政府补充的公司也应有 plot 属性。"""
        game = Game()
        # 强制让食品厂公司全部破产
        food_companies = [
            c for c in game.companies
            if any("食品" in ft.recipe.output_goods_type.name
                   for ft in c.get_component(ProductorComponent).factories.keys())
        ]
        for c in food_companies:
            c.get_component(LedgerComponent).is_bankrupt = True

        # 执行破产清算和市场补充
        game.company_service.process_bankruptcies()
        game.company_service.replenish_market()
        game.companies = list(game.company_service.companies.values())

        # 新公司也应该有 plot
        for company in game.companies:
            assert company.plot is not None, f"{company.name} has no plot"
