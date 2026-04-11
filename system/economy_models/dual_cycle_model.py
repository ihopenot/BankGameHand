import math
import random

from core.config import ConfigManager
from core.types import Rate
from system.economy_models import EconomyModel


class DualCycleModel(EconomyModel):
    """双周期正弦波经济模型。

    公式: economy_index(t) = clamp(A1*sin(2π*t/T1+φ1) + A2*sin(2π*t/T2+φ2) + noise(t), -1.0, +1.0)
    """

    model_name = "dual_cycle"

    def __init__(self) -> None:
        config = ConfigManager().section("economy")
        model_config = getattr(config, self.model_name)
        short = model_config.short_cycle
        long = model_config.long_cycle
        noise_cfg = model_config.noise
        seed: int | None = model_config.random_seed

        self._rng = random.Random(seed)

        self._t1: int = short.period
        self._a1: float = short.amplitude
        phi1: float | None = short.phase
        self._phi1: float = phi1 if phi1 is not None else self._rng.uniform(0, 2 * math.pi)

        self._t2: int = long.period
        self._a2: float = long.amplitude
        phi2: float | None = long.phase
        self._phi2: float = phi2 if phi2 is not None else self._rng.uniform(0, 2 * math.pi)

        self._noise_std: float = noise_cfg.std

        self._last_t: int = -1
        self._raw_value: float = 0.0
        self._short_component: float = 0.0
        self._long_component: float = 0.0
        self._noise_value: float = 0.0

    def calculate(self, t: int) -> Rate:
        self._last_t = t

        self._short_component = self._a1 * math.sin(2 * math.pi * t / self._t1 + self._phi1)
        self._long_component = self._a2 * math.sin(2 * math.pi * t / self._t2 + self._phi2)

        if self._noise_std > 0:
            self._noise_value = self._rng.gauss(0, self._noise_std)
        else:
            self._noise_value = 0.0

        self._raw_value = self._short_component + self._long_component + self._noise_value
        clamped = max(-1.0, min(1.0, self._raw_value))

        return int(clamped * 10000)

    def get_state(self) -> dict[str, int | float]:
        return {
            "last_t": self._last_t,
            "raw_value": self._raw_value,
            "short_component": self._short_component,
            "long_component": self._long_component,
            "noise_value": self._noise_value,
        }
