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
             "description": "异常检测、状态判别、趋势预警、辅助研判"},
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
                         "驱动能量影响系统状态"),
            CouplingEdge("environmental_constraint", "state_maintenance",
                         "env→state", "环境→状态", "main",
                         "环境边界条件影响系统状态"),
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

    def compute_coupling_matrix(self, module_features_df: "pd.DataFrame") -> "np.ndarray":
        """计算 4 个核心模块之间的耦合强度矩阵。

        基于模块特征序列的互相关系数，结合现有边权重加权。
        返回 4×4 numpy 数组，对角线为 1.0。
        """
        import numpy as np
        import pandas as pd

        modules = ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]
        n = len(modules)
        matrix = np.zeros((n, n))

        # 提取各模块特征的均值序列
        mod_series = {}
        for mod in modules:
            cols = [c for c in module_features_df.columns if c.startswith(f"{mod}__")]
            if cols:
                mod_series[mod] = module_features_df[cols].mean(axis=1)
            else:
                mod_series[mod] = pd.Series(np.zeros(len(module_features_df)))

        # 计算模块间相关系数
        for i, m1 in enumerate(modules):
            for j, m2 in enumerate(modules):
                if i == j:
                    matrix[i, j] = 1.0
                elif i < j:
                    corr = mod_series[m1].corr(mod_series[m2])
                    corr = abs(corr) if not np.isnan(corr) else 0.0
                    # 结合边权重
                    edge = self.get_edge(m1, m2)
                    edge_rev = self.get_edge(m2, m1)
                    edge_weight = 1.0
                    if edge:
                        edge_weight = max(edge_weight, edge.coupling_strength if edge.coupling_strength > 0 else 0.5)
                    if edge_rev:
                        edge_weight = max(edge_weight, edge_rev.coupling_strength if edge_rev.coupling_strength > 0 else 0.5)
                    matrix[i, j] = round(corr * edge_weight, 3)
                    matrix[j, i] = matrix[i, j]

        return matrix
