"""MapService 及地图数据模型单元测试。"""

from entity.map import Country, Plot


class TestDataModels:
    def test_country_creation(self):
        country = Country(name="华夏", description="东方大国")
        assert country.name == "华夏"
        assert country.description == "东方大国"

    def test_plot_creation(self):
        country = Country(name="华夏", description="东方大国")
        plot = Plot(name="硅谷工业区", country=country, description="电子产业聚集地")
        assert plot.name == "硅谷工业区"
        assert plot.country is country
        assert plot.description == "电子产业聚集地"
        assert plot.neighbors == []

    def test_plot_neighbor_assignment(self):
        country = Country(name="华夏", description="东方大国")
        plot_a = Plot(name="A区", country=country, description="")
        plot_b = Plot(name="B区", country=country, description="")
        plot_a.neighbors.append(plot_b)
        plot_b.neighbors.append(plot_a)
        assert plot_b in plot_a.neighbors
        assert plot_a in plot_b.neighbors
