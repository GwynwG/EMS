"""四模块领域模型定义。

定义执行控制、能量输入、环境约束、状态维持四大模块的元数据结构。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ModuleType(str, Enum):
    EXECUTION_CONTROL = "execution_control"
    ENERGY_INPUT = "energy_input"
    ENVIRONMENTAL_CONSTRAINT = "environmental_constraint"
    STATE_MAINTENANCE = "state_maintenance"


@dataclass
class ModuleMeta:
    """单个模块的元数据描述。"""
    module_type: ModuleType
    label: str
    chinese_name: str
    description: str
    variables: list[str] = field(default_factory=list)
    score: float = 100.0
    risk_level: str = "normal"

    @property
    def id(self) -> str:
        return self.module_type.value


# ── 模块注册表 ──────────────────────────────────────────────

MODULE_REGISTRY: dict[ModuleType, ModuleMeta] = {
    ModuleType.EXECUTION_CONTROL: ModuleMeta(
        module_type=ModuleType.EXECUTION_CONTROL,
        label="Execution Control",
        chinese_name="执行控制模块",
        description="描述设备如何被调节：设定值、控制指令、控制模式、联锁状态、阀位、执行器反馈等。",
        variables=[
            "setpoint_temperature", "setpoint_pressure", "control_mode",
            "valve_position_main", "valve_position_cooling",
            "interlock_status", "actuator_feedback",
        ],
    ),
    ModuleType.ENERGY_INPUT: ModuleMeta(
        module_type=ModuleType.ENERGY_INPUT,
        label="Energy Input",
        chinese_name="能量输入模块",
        description="描述设备获得多少驱动能量：电压、电流、功率、供能状态、能量利用效率等。",
        variables=[
            "supply_voltage", "supply_current", "active_power",
            "reactive_power", "power_factor", "energy_efficiency",
            "power_frequency",
        ],
    ),
    ModuleType.ENVIRONMENTAL_CONSTRAINT: ModuleMeta(
        module_type=ModuleType.ENVIRONMENTAL_CONSTRAINT,
        label="Environmental Constraint",
        chinese_name="环境约束模块",
        description="描述设备在什么边界条件下运行：冷却水、气压/真空、环境扰动等。",
        variables=[
            "cooling_water_flow", "cooling_water_temp_in",
            "cooling_water_temp_out", "cooling_water_pressure",
            "vacuum_pressure", "ambient_pressure", "ambient_humidity",
        ],
    ),
    ModuleType.STATE_MAINTENANCE: ModuleMeta(
        module_type=ModuleType.STATE_MAINTENANCE,
        label="State Maintenance",
        chinese_name="状态维持模块",
        description="核心状态层：温度、压力、振动、稳定性指标、退化特征，描述设备当前是否稳定/异常/退化。",
        variables=[
            "furnace_temp_1", "furnace_temp_2", "furnace_temp_3",
            "furnace_pressure", "vibration_x", "vibration_y",
            "temp_stability_index", "degradation_index",
        ],
    ),
}


def get_module_meta(module_type: ModuleType | str) -> ModuleMeta:
    """根据模块类型获取元数据。"""
    if isinstance(module_type, str):
        module_type = ModuleType(module_type)
    return MODULE_REGISTRY[module_type]


def get_all_modules() -> list[ModuleMeta]:
    """返回所有注册模块。"""
    return list(MODULE_REGISTRY.values())


def get_module_variables(module_type: ModuleType | str) -> list[str]:
    """返回指定模块的标准变量名列表。"""
    return get_module_meta(module_type).variables


def get_all_variables() -> dict[ModuleType, list[str]]:
    """返回所有模块的变量映射。"""
    return {mt: meta.variables for mt, meta in MODULE_REGISTRY.items()}
