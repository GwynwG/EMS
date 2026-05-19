"""四模块耦合关系图定义。

定义模块间的主要耦合边和辅助边，支持拓扑可视化和耦合分析。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CouplingEdge:
    """耦合关系边。"""
    source: str
    target: str
    label: str
    chinese_name: str
    edge_type: str  # "main" | "auxiliary" | "feedback"
    description: str = ""
    coupling_strength: float = 0.0
    residual_level: float = 0.0
    model_name: str | None = None
    risk_contribution: float = 0.0
    intelligent_compensation_triggered: bool = False
    main_contributing_variable: str = ""
    model_name_display: str = ""
    current_status_text: str = "正常"


@dataclass
class CouplingGraph:
    """四模块耦合关系图。"""
    nodes: list[dict] = field(default_factory=list)
    edges: list[CouplingEdge] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.nodes:
            self.nodes = self._default_nodes()
        if not self.edges:
            self.edges = self._default_edges()

    @staticmethod
    def _default_nodes() -> list[dict]:
        return [
            {"id": "execution_control", "label": "执行控制", "chinese_name": "执行控制模块",
             "type": "module", "group": "core",
             "description": "设定值、控制指令、控制模式、联锁状态、阀位、执行器反馈"},
            {"id": "energy_input", "label": "能量输入", "chinese_name": "能量输入模块",
             "type": "module", "group": "core",
             "description": "电压、电流、功率、供能状态、能量利用效率"},
            {"id": "environmental_constraint", "label": "环境约束", "chinese_name": "环境约束模块",
             "type": "module", "group": "core",
             "description": "冷却水流量/温度/压力、气压/真空、环境边界"},
            {"id": "state_maintenance", "label": "状态维持", "chinese_name": "状态维持模块",
             "type": "module", "group": "core",
             "description": "温度、压力、振动、稳定性指标、退化特征"},
            {"id": "diagnosis_layer", "label": "诊断层", "chinese_name": "诊断层",
             "type": "diagnosis", "group": "diagnosis",
             "description": "状态监测、异常预警、寿命评估"},
            {"id": "coupling_residual", "label": "耦合残差", "chinese_name": "复杂耦合/残差",
             "type": "residual", "group": "residual",
             "description": "多源耦合残差处理"},
            {"id": "model_residual", "label": "模型残差", "chinese_name": "模型残差",
             "type": "residual", "group": "residual",
             "description": "基础统计模型残差"},
            {"id": "intelligent_model", "label": "智能模型", "chinese_name": "智能补偿模型",
             "type": "model", "group": "model",
             "description": "智能补偿模型（XGBoost/Autoencoder等）"},
        ]

    @staticmethod
    def _default_edges() -> list[CouplingEdge]:
        return [
            # 主边
            CouplingEdge("execution_control", "energy_input",
                         "ctrl→energy", "执行→能量", "main",
                         "控制指令调节能量输入"),
            CouplingEdge("execution_control", "environmental_constraint",
                         "ctrl→env", "执行→环境", "main",
                         "控制指令影响环境边界"),
            CouplingEdge("energy_input", "state_maintenance",
                         "energy→state", "能量→状态", "main",
                         "驱动能量影响设备状态"),
            CouplingEdge("environmental_constraint", "state_maintenance",
                         "env→state", "环境→状态", "main",
                         "环境边界条件影响设备状态"),
            CouplingEdge("state_maintenance", "execution_control",
                         "state→ctrl", "状态→执行(反馈)", "feedback",
                         "状态反馈至控制系统"),
            CouplingEdge("state_maintenance", "diagnosis_layer",
                         "state→diag", "状态→诊断", "main",
                         "状态数据输入诊断层"),
            # 辅助边
            CouplingEdge("energy_input", "coupling_residual",
                         "energy→耦合残差", "能量→耦合残差", "auxiliary",
                         "能量模块贡献耦合残差"),
            CouplingEdge("environmental_constraint", "coupling_residual",
                         "env→耦合残差", "环境→耦合残差", "auxiliary",
                         "环境模块贡献耦合残差"),
            CouplingEdge("execution_control", "coupling_residual",
                         "ctrl→耦合残差", "执行→耦合残差", "auxiliary",
                         "执行模块贡献耦合残差"),
            CouplingEdge("coupling_residual", "intelligent_model",
                         "耦合残差→智能模型", "耦合残差→智能", "auxiliary",
                         "耦合残差输入智能补偿模型"),
            CouplingEdge("model_residual", "intelligent_model",
                         "模型残差→智能模型", "模型残差→智能", "auxiliary",
                         "统计模型残差输入智能模型"),
            CouplingEdge("intelligent_model", "diagnosis_layer",
                         "智能→诊断", "智能→诊断", "auxiliary",
                         "智能模型输出至诊断层"),
        ]

    def get_node(self, node_id: str) -> dict | None:
        for n in self.nodes:
            if n["id"] == node_id:
                return n
        return None

    def get_edges_from(self, source: str) -> list[CouplingEdge]:
        return [e for e in self.edges if e.source == source]

    def get_edges_to(self, target: str) -> list[CouplingEdge]:
        return [e for e in self.edges if e.target == target]

    def get_edge(self, source: str, target: str) -> CouplingEdge | None:
        for e in self.edges:
            if e.source == source and e.target == target:
                return e
        return None
