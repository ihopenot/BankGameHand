## Why

当前 `EconomyService` 仅有空壳实现，无法驱动游戏经济周期运转。经济周期指数是整个游戏经济系统的外生驱动核心，所有其他经济指标（利率、消费信心、产能利用率等）都依赖于它。需要实现可扩展的经济模型架构，并完成双周期正弦波经济模型作为首个实现。

## What Changes

1. **通用注册表** (`core/registry.py`) — 提供按名称注册和实例化类的通用基础设施，供经济模型及后续其他模块使用
2. **模型基类** (`core/base_model.py`) — 定义 `BaseModel` ABC，作为所有模型（经济模型、未来其他模型）的通用基类
3. **经济周期模型抽象基类** (`system/economy_models/__init__.py`) — 定义 `EconomyModel(BaseModel)` ABC，规范经济周期模型的接口
4. **双周期正弦波模型** (`system/economy_models/dual_cycle_model.py`) — 实现设计文档中的双周期公式：`economy_index(t) = clamp(A1*sin(2π*t/T1+φ1) + A2*sin(2π*t/T2+φ2) + noise(t), -1.0, +1.0)`
5. **EconomyService 完整实现** (`system/economy_service.py`) — 从配置读取模型名称，通过注册表创建模型实例，在 `update_pahse` 中计算经济周期指数
6. **Service 基类修改** (`system/service.py`) — 增加 `game` 引用，所有 Service 可通过 `self.game` 访问游戏状态
7. **经济配置文件** (`config/economy.yaml`) — 定义模型选择和双周期参数

## Impact

- **新增文件**: `core/registry.py`, `core/base_model.py`, `system/economy_models/__init__.py`, `system/economy_models/dual_cycle_model.py`, `config/economy.yaml`
- **修改文件**: `system/economy_service.py`, `system/service.py`
- **依赖**: 仅使用 Python 标准库 (`math`, `random`)
- **影响范围**: `Service` 基类签名变更影响所有 Service 子类的构造函数
