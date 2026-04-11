import math
from pathlib import Path
from core.config import ConfigManager
from system.economy_models.dual_cycle_model import DualCycleModel
from system.economy_models import EconomyModel

TEST_CONFIG_DIR = str(Path(__file__).parent / "config")


class TestDualCycleModel:
    def setup_method(self) -> None:
        ConfigManager().load(TEST_CONFIG_DIR)

    def test_inherits_from_economy_model(self):
        """DualCycleModel 继承自 EconomyModel"""
        assert issubclass(DualCycleModel, EconomyModel)

    def test_name(self):
        """模型名称为 dual_cycle"""
        model = DualCycleModel()
        assert model.model_name == "dual_cycle"

    def test_calculate_returns_rate(self):
        """calculate 返回 int 类型 (Rate)"""
        model = DualCycleModel()
        result = model.calculate(0)
        assert isinstance(result, int)

    def test_calculate_at_zero_with_zero_phase(self):
        """t=0, phase=0, noise=0 时，sin(0)=0，结果应为 0"""
        model = DualCycleModel()
        result = model.calculate(0)
        assert result == 0

    def test_calculate_known_value(self):
        """已知参数下验证计算结果"""
        model = DualCycleModel()
        t = 25 // 4  # t=6
        result = model.calculate(t)
        short = 0.45 * math.sin(2 * math.pi * t / 25)
        long_ = 0.25 * math.sin(2 * math.pi * t / 60)
        expected = int(max(-1.0, min(1.0, short + long_)) * 10000)
        assert result == expected

    def test_fixed_seed_reproducible(self):
        """固定种子时结果可复现"""
        model1 = DualCycleModel()
        model2 = DualCycleModel()
        results1 = [model1.calculate(t) for t in range(20)]
        results2 = [model2.calculate(t) for t in range(20)]
        assert results1 == results2

    def test_get_state(self):
        """get_state 返回包含正确键的字典"""
        model = DualCycleModel()
        model.calculate(5)
        state = model.get_state()
        assert "last_t" in state
        assert "raw_value" in state
        assert "short_component" in state
        assert "long_component" in state
        assert "noise_value" in state
        assert state["last_t"] == 5

    def test_result_range(self):
        """多轮计算结果始终在 [-10000, 10000] 范围内"""
        model = DualCycleModel()
        for t in range(200):
            result = model.calculate(t)
            assert -10000 <= result <= 10000, f"t={t}, result={result}"
