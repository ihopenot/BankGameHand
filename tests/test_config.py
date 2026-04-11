import pytest
import yaml

from core.config import AttrDict, ConfigManager


# ========== AttrDict Tests ==========


class TestAttrDict:
    def test_basic_attr_access(self):
        d = AttrDict({"name": "test", "value": 42})
        assert d.name == "test"
        assert d.value == 42

    def test_dict_style_access(self):
        d = AttrDict({"name": "test"})
        assert d["name"] == "test"

    def test_nested_dict(self):
        d = AttrDict({"server": {"host": "localhost", "port": 8080}})
        assert d.server.host == "localhost"
        assert d.server.port == 8080
        assert isinstance(d.server, AttrDict)

    def test_list_of_dicts(self):
        d = AttrDict({"players": [{"name": "Alice"}, {"name": "Bob"}]})
        assert d.players[0].name == "Alice"
        assert d.players[1].name == "Bob"
        assert isinstance(d.players[0], AttrDict)

    def test_dict_containing_list(self):
        d = AttrDict({"group": {"members": ["a", "b", "c"]}})
        assert d.group.members == ["a", "b", "c"]
        assert d.group.members[0] == "a"

    def test_list_of_lists(self):
        d = AttrDict({"matrix": [[1, 2], [3, 4]]})
        assert d.matrix[0] == [1, 2]
        assert d.matrix[1][1] == 4

    def test_deep_nested_dict_list_dict_list(self):
        """dict -> list -> dict -> list 深层嵌套"""
        d = AttrDict({
            "companies": [
                {
                    "name": "CorpA",
                    "departments": [
                        {"name": "Engineering", "members": ["Alice", "Bob"]},
                        {"name": "Sales", "members": ["Charlie"]},
                    ],
                },
                {
                    "name": "CorpB",
                    "departments": [
                        {"name": "HR", "members": ["Dave"]},
                    ],
                },
            ]
        })
        assert d.companies[0].name == "CorpA"
        assert d.companies[0].departments[0].name == "Engineering"
        assert d.companies[0].departments[0].members[1] == "Bob"
        assert d.companies[1].departments[0].members[0] == "Dave"

    def test_list_containing_mixed_types(self):
        d = AttrDict({"items": [1, "two", {"three": 3}, [4, 5]]})
        assert d.items[0] == 1
        assert d.items[1] == "two"
        assert d.items[2].three == 3
        assert d.items[3] == [4, 5]

    def test_missing_attr_raises(self):
        d = AttrDict({"a": 1})
        with pytest.raises(AttributeError):
            _ = d.nonexistent

    def test_empty_dict(self):
        d = AttrDict({})
        with pytest.raises(AttributeError):
            _ = d.anything

    def test_none_value(self):
        d = AttrDict({"val": None})
        assert d.val is None


# ========== ConfigManager Tests ==========


class TestConfigManager:
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """每个测试前重置单例"""
        ConfigManager._instance = None
        yield
        ConfigManager._instance = None

    @pytest.fixture
    def config_dir(self, tmp_path):
        """创建临时配置目录并写入测试 yaml 文件"""
        # economy.yaml
        economy = {
            "base_rate": 500,
            "growth": {"min": 100, "max": 1000},
        }
        with open(tmp_path / "economy.yaml", "w", encoding="utf-8") as f:
            yaml.dump(economy, f)

        # market.yaml
        market = {
            "products": [
                {"name": "iron", "price": 100, "tags": ["metal", "raw"]},
                {"name": "wood", "price": 50, "tags": ["organic"]},
            ],
            "rules": {
                "tax_rate": 0.05,
                "discounts": [0.1, 0.2, 0.3],
            },
        }
        with open(tmp_path / "market.yaml", "w", encoding="utf-8") as f:
            yaml.dump(market, f)

        # nested.yml (.yml 扩展名)
        nested = {
            "level1": {
                "level2": [
                    {
                        "level3": {
                            "values": [10, 20, 30],
                            "info": {"deep": True},
                        }
                    }
                ]
            }
        }
        with open(tmp_path / "nested.yml", "w", encoding="utf-8") as f:
            yaml.dump(nested, f)

        return tmp_path

    def test_singleton(self):
        a = ConfigManager()
        b = ConfigManager()
        assert a is b

    def test_load_and_section(self, config_dir):
        cfg = ConfigManager()
        cfg.load(str(config_dir))

        eco = cfg.section("economy")
        assert isinstance(eco, AttrDict)
        assert eco.base_rate == 500
        assert eco.growth.min == 100
        assert eco.growth.max == 1000

    def test_section_with_list_of_dicts(self, config_dir):
        cfg = ConfigManager()
        cfg.load(str(config_dir))

        mkt = cfg.section("market")
        assert mkt.products[0].name == "iron"
        assert mkt.products[0].price == 100
        assert mkt.products[0].tags == ["metal", "raw"]
        assert mkt.products[1].name == "wood"

    def test_section_with_nested_list_in_dict(self, config_dir):
        cfg = ConfigManager()
        cfg.load(str(config_dir))

        mkt = cfg.section("market")
        assert mkt.rules.tax_rate == 0.05
        assert mkt.rules.discounts == [0.1, 0.2, 0.3]

    def test_deep_nested_yml(self, config_dir):
        cfg = ConfigManager()
        cfg.load(str(config_dir))

        n = cfg.section("nested")
        assert n.level1.level2[0].level3.values == [10, 20, 30]
        assert n.level1.level2[0].level3.info.deep is True

    def test_section_not_found(self, config_dir):
        cfg = ConfigManager()
        cfg.load(str(config_dir))
        with pytest.raises(KeyError):
            cfg.section("nonexistent")

    def test_load_custom_path(self, tmp_path):
        custom = tmp_path / "custom_config"
        custom.mkdir()
        with open(custom / "app.yaml", "w", encoding="utf-8") as f:
            yaml.dump({"debug": True, "name": "test_app"}, f)

        cfg = ConfigManager()
        cfg.load(str(custom))

        app = cfg.section("app")
        assert app.debug is True
        assert app.name == "test_app"

    def test_load_invalid_dir(self):
        cfg = ConfigManager()
        with pytest.raises(FileNotFoundError):
            cfg.load("/nonexistent/path")

    def test_reload_clears_old_sections(self, tmp_path):
        """reload 后旧 section 应该被清除"""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        with open(dir1 / "a.yaml", "w", encoding="utf-8") as f:
            yaml.dump({"x": 1}, f)

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        with open(dir2 / "b.yaml", "w", encoding="utf-8") as f:
            yaml.dump({"y": 2}, f)

        cfg = ConfigManager()
        cfg.load(str(dir1))
        assert cfg.section("a").x == 1

        cfg.load(str(dir2))
        with pytest.raises(KeyError):
            cfg.section("a")
        assert cfg.section("b").y == 2
