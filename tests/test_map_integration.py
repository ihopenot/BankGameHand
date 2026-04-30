"""地图系统集成测试：Game 初始化后公司正确持有 Plot 引用。"""

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
