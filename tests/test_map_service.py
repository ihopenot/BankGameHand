"""MapService 及地图数据模型单元测试。"""

import pytest

from entity.map import Country, Plot
from system.map_service import MapService


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


class TestMapServiceLoad:
    def _sample_config(self):
        return {
            "countries": [
                {"name": "华夏", "description": "东方大国"},
                {"name": "西洋联邦", "description": "工业强国"},
            ],
            "plots": [
                {"name": "硅谷工业区", "country": "华夏", "description": "电子产业聚集地", "neighbors": ["江南纺织区"]},
                {"name": "江南纺织区", "country": "华夏", "description": "传统纺织业重镇", "neighbors": ["硅谷工业区"]},
                {"name": "新大陆科技园", "country": "西洋联邦", "description": "高科技产业基地", "neighbors": []},
            ],
        }

    def test_load_countries(self):
        svc = MapService()
        svc.load_map(self._sample_config())
        assert "华夏" in svc.countries
        assert "西洋联邦" in svc.countries
        assert svc.countries["华夏"].name == "华夏"

    def test_load_plots(self):
        svc = MapService()
        svc.load_map(self._sample_config())
        assert "硅谷工业区" in svc.plots
        assert svc.plots["硅谷工业区"].country.name == "华夏"

    def test_neighbors_resolved(self):
        svc = MapService()
        svc.load_map(self._sample_config())
        plot_a = svc.plots["硅谷工业区"]
        plot_b = svc.plots["江南纺织区"]
        assert plot_b in plot_a.neighbors
        assert plot_a in plot_b.neighbors

    def test_neighbor_consistency_error(self):
        """A 列 B 为邻居但 B 未列 A 时应报错。"""
        config = {
            "countries": [{"name": "X", "description": ""}],
            "plots": [
                {"name": "A", "country": "X", "description": "", "neighbors": ["B"]},
                {"name": "B", "country": "X", "description": "", "neighbors": []},
            ],
        }
        svc = MapService()
        with pytest.raises(ValueError, match="相邻关系不一致"):
            svc.load_map(config)

    def test_unknown_country_error(self):
        config = {
            "countries": [{"name": "X", "description": ""}],
            "plots": [
                {"name": "A", "country": "不存在", "description": "", "neighbors": []},
            ],
        }
        svc = MapService()
        with pytest.raises(ValueError, match="不存在"):
            svc.load_map(config)

    def test_unknown_neighbor_error(self):
        config = {
            "countries": [{"name": "X", "description": ""}],
            "plots": [
                {"name": "A", "country": "X", "description": "", "neighbors": ["不存在"]},
            ],
        }
        svc = MapService()
        with pytest.raises(ValueError, match="不存在"):
            svc.load_map(config)


from entity.company.company import Company


class TestMapServiceQueries:
    def _setup(self):
        svc = MapService()
        config = {
            "countries": [
                {"name": "华夏", "description": ""},
                {"name": "西洋联邦", "description": ""},
            ],
            "plots": [
                {"name": "A区", "country": "华夏", "description": "", "neighbors": ["B区"]},
                {"name": "B区", "country": "华夏", "description": "", "neighbors": ["A区"]},
                {"name": "C区", "country": "西洋联邦", "description": "", "neighbors": []},
            ],
        }
        svc.load_map(config)
        return svc

    def test_get_plots_by_country(self):
        svc = self._setup()
        plots = svc.get_plots_by_country("华夏")
        names = [p.name for p in plots]
        assert "A区" in names
        assert "B区" in names
        assert "C区" not in names

    def test_get_companies_in_plot(self):
        svc = self._setup()
        c1 = Company(name="c1")
        c1.plot = svc.get_plot("A区")
        c2 = Company(name="c2")
        c2.plot = svc.get_plot("B区")
        companies = [c1, c2]
        result = svc.get_companies_in_plot("A区", companies)
        assert result == [c1]

    def test_get_companies_in_country(self):
        svc = self._setup()
        c1 = Company(name="c1")
        c1.plot = svc.get_plot("A区")
        c2 = Company(name="c2")
        c2.plot = svc.get_plot("C区")
        companies = [c1, c2]
        result = svc.get_companies_in_country("华夏", companies)
        assert result == [c1]

    def test_get_neighbors(self):
        svc = self._setup()
        neighbors = svc.get_neighbors("A区")
        assert len(neighbors) == 1
        assert neighbors[0].name == "B区"
