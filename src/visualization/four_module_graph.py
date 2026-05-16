"""四模块交互拓扑图。

使用 streamlit-echarts 或自定义 HTML/JS 实现可交互的四模块拓扑图。
"""
from __future__ import annotations

from typing import Any, Optional

from src.domain_framework.coupling_graph import CouplingGraph


def build_echarts_graph_option(
    graph: CouplingGraph,
    module_scores: dict[str, float] | None = None,
    selected_node: str | None = None,
    selected_edge: str | None = None,
    graph_height: int = 720,
) -> dict[str, Any]:
    """构建 ECharts graph 图表配置。

    selected_node: 当前选中的节点 id（高亮）
    selected_edge: 当前选中的边 id，格式 "source__target"（高亮）
    """
    module_scores = module_scores or {}

    # 节点颜色映射
    def score_color(score: float) -> str:
        if score >= 80:
            return "#00C853"
        elif score >= 60:
            return "#FFD600"
        elif score >= 40:
            return "#FF6D00"
        return "#D50000"

    # 解析选中边的 source/target
    sel_edge_src, sel_edge_tgt = None, None
    if selected_edge and "__" in selected_edge:
        parts = selected_edge.split("__")
        if len(parts) == 2:
            sel_edge_src, sel_edge_tgt = parts[0], parts[1]

    # 构建节点
    nodes = []
    positions = {
        "execution_control": (300, 150),
        "energy_input": (600, 100),
        "environmental_constraint": (150, 400),
        "state_maintenance": (450, 350),
        "diagnosis_layer": (750, 350),
        "coupling_residual": (300, 550),
        "model_residual": (550, 550),
        "intelligent_model": (425, 680),
    }

    group_colors = {
        "core": "#1565C0",
        "diagnosis": "#6A1B9A",
        "residual": "#E65100",
        "model": "#2E7D32",
    }

    for node in graph.nodes:
        nid = node["id"]
        x, y = positions.get(nid, (400, 400))
        score = module_scores.get(nid)
        is_selected = nid == selected_node

        item_style = {
            "color": score_color(score) if score is not None else group_colors.get(node.get("group", ""), "#666"),
            "borderColor": "#FFD600" if is_selected else "#333",
            "borderWidth": 4 if is_selected else 2,
            "shadowBlur": 20 if is_selected else 5,
            "shadowColor": "rgba(255,214,0,0.6)" if is_selected else "rgba(0,0,0,0.3)",
        }

        label_text = f"{node['label']}"
        if score is not None:
            label_text += f"\n{score:.1f}"

        nodes.append({
            "name": nid,
            "x": x,
            "y": y,
            "symbolSize": 70 if node.get("type") == "module" else 50,
            "itemStyle": item_style,
            "label": {
                "show": True,
                "formatter": label_text,
                "fontSize": 13,
                "fontWeight": "bold",
                "color": "#fff",
            },
            "tooltip": {
                "formatter": f"<b>{node['label']}</b><br/>{node['description']}<br/>"
                + (f"评分: {score:.1f}" if score is not None else ""),
            },
            "category": node.get("group", "core"),
            "_nodeData": node,
        })

    # 构建边（支持选中高亮）
    edges = []
    for edge in graph.edges:
        line_style = {
            "main": {"color": "#42A5F5", "width": 3, "curveness": 0.1},
            "feedback": {"color": "#FF9800", "width": 2.5, "curveness": 0.2, "type": "dashed"},
            "auxiliary": {"color": "#78909C", "width": 1.5, "curveness": 0.15, "type": "dotted"},
        }
        style = line_style.get(edge.edge_type, line_style["main"])

        # 判断边是否被选中
        is_edge_selected = (sel_edge_src == edge.source and sel_edge_tgt == edge.target)

        edge_line_style = {
            "color": "#FFD600" if is_edge_selected else style["color"],
            "width": 5 if is_edge_selected else style["width"],
            "curveness": style.get("curveness", 0.1),
            "type": style.get("type", "solid"),
            "shadowBlur": 10 if is_edge_selected else 0,
            "shadowColor": "rgba(255,214,0,0.6)" if is_edge_selected else "transparent",
        }

        edges.append({
            "source": edge.source,
            "target": edge.target,
            "lineStyle": edge_line_style,
            "label": {
                "show": True,
                "formatter": edge.chinese_name,
                "fontSize": 11 if is_edge_selected else 10,
                "color": "#FFD600" if is_edge_selected else "#aaa",
                "fontWeight": "bold" if is_edge_selected else "normal",
            },
            "tooltip": {
                "formatter": (
                    f"<b>{edge.chinese_name}</b><br/>"
                    f"{edge.description}<br/>"
                    f"耦合强度: {edge.coupling_strength:.2f}<br/>"
                    f"残差水平: {edge.residual_level:.2f}"
                ),
            },
            "_edgeData": {
                "source": edge.source,
                "target": edge.target,
                "label": edge.label,
                "chinese_name": edge.chinese_name,
                "edge_type": edge.edge_type,
                "description": edge.description,
            },
        })

    # ECharts 配置
    option = {
        "backgroundColor": "#0f2137",
        "title": {
            "text": "四模块交互拓扑图",
            "subtext": "特种材料制备设备状态监测系统",
            "top": 10,
            "left": "center",
            "textStyle": {"color": "#eee", "fontSize": 18},
            "subtextStyle": {"color": "#aaa", "fontSize": 12},
        },
        "tooltip": {
            "trigger": "item",
            "backgroundColor": "rgba(10,25,41,0.95)",
            "borderColor": "#1565C0",
            "textStyle": {"color": "#eee"},
        },
        "animationDuration": 500,
        "series": [{
            "type": "graph",
            "layout": "none",
            "data": nodes,
            "links": edges,
            "roam": False,
            "draggable": False,
            "emphasis": {
                "focus": "adjacency",
                "lineStyle": {"width": 5},
                "itemStyle": {"shadowBlur": 15, "shadowColor": "rgba(255,255,255,0.3)"},
                "label": {"fontSize": 14},
            },
            "lineStyle": {"opacity": 0.8},
            "edgeLabel": {"fontSize": 10},
            "categories": [
                {"name": "core", "itemStyle": {"color": "#1565C0"}},
                {"name": "diagnosis", "itemStyle": {"color": "#6A1B9A"}},
                {"name": "residual", "itemStyle": {"color": "#E65100"}},
                {"name": "model", "itemStyle": {"color": "#2E7D32"}},
            ],
        }],
    }

    return option


def get_module_detail(node_id: str, module_scores: dict[str, float] | None = None) -> dict[str, Any]:
    """获取模块详情。"""
    from src.domain_framework.module_schema import get_module_meta, ModuleType

    try:
        mt = ModuleType(node_id)
        meta = get_module_meta(mt)
        score = (module_scores or {}).get(node_id, 100.0)

        from src.domain_framework.module_scoring import ModuleScorer
        risk_level = ModuleScorer.determine_risk_level(100 - score)

        return {
            "name": meta.chinese_name,
            "description": meta.description,
            "score": score,
            "risk_level": risk_level,
            "variables": meta.variables,
        }
    except (ValueError, KeyError):
        # 非核心节点
        node_info = {
            "diagnosis_layer": {
                "name": "诊断层",
                "description": "状态监测、异常预警、寿命评估的综合诊断层",
                "type": "diagnosis",
            },
            "coupling_residual": {
                "name": "耦合残差",
                "description": "多源耦合残差处理模块",
                "type": "residual",
            },
            "model_residual": {
                "name": "模型残差",
                "description": "基础统计模型残差",
                "type": "residual",
            },
            "intelligent_model": {
                "name": "智能模型",
                "description": "智能补偿模型（XGBoost/Autoencoder等）",
                "type": "model",
            },
        }
        return node_info.get(node_id, {"name": node_id, "description": "未知节点"})


def get_edge_detail(
    source: str,
    target: str,
    coupling_graph: CouplingGraph | None = None,
) -> dict[str, Any]:
    """获取边详情。"""
    if coupling_graph is None:
        coupling_graph = CouplingGraph()

    edge = coupling_graph.get_edge(source, target)
    if edge is None:
        return {"error": "未找到该耦合关系"}

    return {
        "name": edge.chinese_name,
        "source": edge.source,
        "target": edge.target,
        "coupling_strength": edge.coupling_strength,
        "residual_level": edge.residual_level,
        "model_name": edge.model_name,
        "description": edge.description,
        "edge_type": edge.edge_type,
    }
