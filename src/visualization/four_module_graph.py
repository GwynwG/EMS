"""四模块交互拓扑图 - 纯 SVG 静态示意图。

使用 streamlit.components.v1.html 渲染 SVG 拓扑图，
根据 selected_id 高亮对应节点/边，无任何点击交互。
"""
from __future__ import annotations

from typing import Any, Optional

import streamlit as st
import streamlit.components.v1 as components

from src.domain_framework.coupling_graph import CouplingGraph


# ── 节点布局定义 ──
NODE_DEFS = [
    {"id": "execution_control",        "label": "执行控制模块",              "x": 600, "y": 100, "w": 180, "h": 70, "group": "core"},
    {"id": "energy_input",             "label": "能量输入模块",              "x": 180, "y": 310, "w": 180, "h": 70, "group": "core"},
    {"id": "environmental_constraint", "label": "环境约束模块",              "x": 1020, "y": 310, "w": 180, "h": 70, "group": "core"},
    {"id": "state_maintenance",        "label": "状态维持模块",              "x": 600, "y": 420, "w": 180, "h": 70, "group": "core"},
    {"id": "diagnosis_layer",          "label": "诊断层",                    "x": 600, "y": 660, "w": 180, "h": 60, "group": "diagnosis"},
    {"id": "coupling_residual",        "label": "复杂耦合/残差",             "x": 200, "y": 580, "w": 180, "h": 60, "group": "residual"},
    {"id": "model_residual",           "label": "模型残差",                  "x": 600, "y": 560, "w": 160, "h": 56, "group": "residual"},
    {"id": "intelligent_model",        "label": "智能补偿模型入口",          "x": 980, "y": 580, "w": 200, "h": 60, "group": "model"},
]

# ── 边定义 ──
EDGE_DEFS = [
    # 主关系 - 蓝色实线
    {"id": "execution_control__energy_input",             "src": "execution_control",        "tgt": "energy_input",             "label": "执行→能量",   "type": "main"},
    {"id": "execution_control__environmental_constraint", "src": "execution_control",        "tgt": "environmental_constraint", "label": "执行→环境",   "type": "main"},
    {"id": "energy_input__state_maintenance",             "src": "energy_input",             "tgt": "state_maintenance",        "label": "能量→状态",   "type": "main"},
    {"id": "environmental_constraint__state_maintenance", "src": "environmental_constraint", "tgt": "state_maintenance",        "label": "环境→状态",   "type": "main"},
    {"id": "state_maintenance__diagnosis_layer",          "src": "state_maintenance",        "tgt": "diagnosis_layer",          "label": "状态→诊断",   "type": "main"},
    # 反馈 - 弧形
    {"id": "state_maintenance__execution_control",        "src": "state_maintenance",        "tgt": "execution_control",        "label": "状态→执行(反馈)", "type": "feedback"},
    # 复杂耦合 - 灰色虚线
    {"id": "energy_input__coupling_residual",             "src": "energy_input",             "tgt": "coupling_residual",        "label": "", "type": "auxiliary"},
    {"id": "environmental_constraint__coupling_residual", "src": "environmental_constraint", "tgt": "coupling_residual",        "label": "", "type": "auxiliary"},
    {"id": "execution_control__coupling_residual",        "src": "execution_control",        "tgt": "coupling_residual",        "label": "", "type": "auxiliary"},
    {"id": "coupling_residual__intelligent_model",        "src": "coupling_residual",        "tgt": "intelligent_model",        "label": "", "type": "auxiliary"},
    {"id": "model_residual__intelligent_model",           "src": "model_residual",           "tgt": "intelligent_model",        "label": "", "type": "auxiliary"},
    {"id": "intelligent_model__diagnosis_layer",          "src": "intelligent_model",        "tgt": "diagnosis_layer",          "label": "", "type": "auxiliary"},
]

# ── 颜色定义 (工业深色主题) ──
GROUP_COLORS = {
    "core":      {"fill": "#0E2A3D", "stroke": "#22D3EE"},
    "diagnosis": {"fill": "#1A1040", "stroke": "#A78BFA"},
    "residual":  {"fill": "#2A1A0E", "stroke": "#F97316"},
    "model":     {"fill": "#0E2A1A", "stroke": "#10B981"},
}

EDGE_COLORS = {
    "main":      {"stroke": "#22D3EE", "width": 2.0},
    "feedback":  {"stroke": "#F59E0B", "width": 1.8},
    "auxiliary": {"stroke": "#4A5568", "width": 1.2},
}

SELECTED_COLOR = "#FFFFFE"


def _score_to_fill(score: float | None, group: str) -> str:
    """根据健康分数返回节点填充色（深色主题）。"""
    if score is None:
        return GROUP_COLORS.get(group, GROUP_COLORS["core"])["fill"]
    if score >= 80:
        return "#0A2E1A"   # 深绿
    elif score >= 60:
        return "#2A2200"   # 深黄
    elif score >= 40:
        return "#2A1A0A"   # 深橙
    return "#2A0A0A"       # 深红


def _score_to_stroke(score: float | None, group: str) -> str:
    """根据健康分数返回节点边框色（深色主题）。"""
    if score is None:
        return GROUP_COLORS.get(group, GROUP_COLORS["core"])["stroke"]
    if score >= 80:
        return "#10B981"
    elif score >= 60:
        return "#F59E0B"
    elif score >= 40:
        return "#F97316"
    return "#EF4444"


def _node_center(nd: dict) -> tuple[float, float]:
    return nd["x"], nd["y"]


def _build_edge_path(src_nd: dict, tgt_nd: dict, edge_type: str) -> str:
    """生成边的 SVG path 数据。"""
    sx, sy = _node_center(src_nd)
    tx, ty = _node_center(tgt_nd)

    if edge_type == "feedback":
        # 弧形反馈线
        mx = (sx + tx) / 2 + 80
        my = (sy + ty) / 2 - 60
        return f"M {sx} {sy} Q {mx} {my} {tx} {ty}"
    else:
        # 直线或微弯
        return f"M {sx} {sy} L {tx} {ty}"


def _build_arrow_marker(edge_type: str, color: str, marker_id: str) -> str:
    """生成箭头 marker 定义。"""
    dash = ' stroke-dasharray="4,2"' if edge_type == "auxiliary" else ""
    return f'''<marker id="{marker_id}" markerWidth="10" markerHeight="7"
        refX="10" refY="3.5" orient="auto" markerUnits="strokeWidth">
        <polygon points="0 0, 10 3.5, 0 7" fill="{color}"{dash}/>
    </marker>'''


def render_four_module_graph_svg(selected_id: str, module_scores: dict[str, float] | None = None) -> None:
    """渲染四模块交互拓扑图（纯 SVG）。

    Args:
        selected_id: 当前选中的节点或边 id
        module_scores: 核心四模块的健康分数
    """
    module_scores = module_scores or {}
    node_map = {nd["id"]: nd for nd in NODE_DEFS}

    # ── 构建 SVG 元素 ──

    # defs: filters + markers
    defs_parts = [
        '''<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="8" result="blur"/>
            <feFlood flood-color="#FFFDE7" flood-opacity="0.85" result="color"/>
            <feComposite in="color" in2="blur" operator="in" result="colorBlur"/>
            <feMerge><feMergeNode in="colorBlur"/><feMergeNode in="colorBlur"/><feMergeNode in="colorBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>''',
    ]

    for etype, ecolor in [("main", "#22D3EE"), ("feedback", "#F59E0B"), ("auxiliary", "#4A5568")]:
        mid = f"arrow_{etype}"
        defs_parts.append(_build_arrow_marker(etype, ecolor, mid))

    defs_parts.append(_build_arrow_marker("selected", SELECTED_COLOR, "arrow_selected"))

    defs_str = "\n".join(defs_parts)

    # 边
    edge_parts = []
    for edge in EDGE_DEFS:
        src_nd = node_map.get(edge["src"])
        tgt_nd = node_map.get(edge["tgt"])
        if not src_nd or not tgt_nd:
            continue

        ecfg = EDGE_COLORS.get(edge["type"], EDGE_COLORS["main"])
        is_sel = edge["id"] == selected_id
        color = SELECTED_COLOR if is_sel else ecfg["stroke"]
        width = ecfg["width"] + 2 if is_sel else ecfg["width"]
        dash = 'stroke-dasharray="8,4"' if edge["type"] == "auxiliary" and not is_sel else ""
        path_d = _build_edge_path(src_nd, tgt_nd, edge["type"])

        if is_sel:
            marker = "url(#arrow_selected)"
        else:
            marker = f"url(#arrow_{edge['type']})"

        label_html = ""
        if edge["label"]:
            mx = (src_nd["x"] + tgt_nd["x"]) / 2
            my = (src_nd["y"] + tgt_nd["y"]) / 2
            if edge["type"] == "feedback":
                mx += 50
                my -= 30
            else:
                mx += 15
                my -= 10
            label_html = f'<text x="{mx}" y="{my}" font-size="11" fill="{color}" text-anchor="middle" font-weight="{"bold" if is_sel else "normal"}" font-family="Fira Sans, sans-serif" opacity="0.85">{edge["label"]}</text>'

        glow = ' filter="url(#glow)"' if is_sel else ""
        edge_parts.append(
            f'<g>'
            f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'{dash} opacity="0.9" marker-end="{marker}"{glow}/>'
            f'{label_html}</g>'
        )

    edges_str = "\n".join(edge_parts)

    # 节点
    node_parts = []
    for nd in NODE_DEFS:
        nid = nd["id"]
        is_sel = nid == selected_id

        score = module_scores.get(nid)
        fill = _score_to_fill(score, nd["group"])
        stroke = SELECTED_COLOR if is_sel else _score_to_stroke(score, nd["group"])
        stroke_w = 5 if is_sel else 2
        font_w = "bold" if is_sel else "600"
        glow = ' filter="url(#glow)"' if is_sel else ""

        x = nd["x"] - nd["w"] / 2
        y = nd["y"] - nd["h"] / 2
        r = 12

        score_text = ""
        if score is not None:
            score_text = f'<text x="{nd["x"]}" y="{nd["y"] + 8}" font-size="12" fill="#8B9DC3" text-anchor="middle" font-weight="500" font-family="Fira Code, monospace">{score:.1f}</text>'

        node_parts.append(
            f'<g>'
            f'<rect x="{x}" y="{y}" width="{nd["w"]}" height="{nd["h"]}" rx="{r}" ry="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_w}"{glow}/>'
            f'<text x="{nd["x"]}" y="{nd["y"] - 4}" font-size="13" fill="#E2E8F0" text-anchor="middle" font-weight="{font_w}" font-family="Fira Sans, sans-serif">{nd["label"]}</text>'
            f'{score_text}'
            f'</g>'
        )

    nodes_str = "\n".join(node_parts)

    # ── 组装完整 HTML ──
    svg_html = f"""
<div style="background:#0F1729; border-radius:10px; border:1px solid #1E2D4A; padding:8px; width:100%; box-sizing:border-box; overflow:hidden; pointer-events:none; box-shadow: 0 4px 24px rgba(0,0,0,0.4);">
<svg viewBox="0 0 1200 760" width="100%" height="760" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg" style="pointer-events:none; display:block; margin:0 auto;">
<defs>
{defs_str}
</defs>
<rect x="0" y="0" width="1200" height="760" rx="8" ry="8" fill="#0B1120"/>
<text x="600" y="36" font-size="16" font-weight="600" fill="#CBD5E1" text-anchor="middle" font-family="Fira Sans, sans-serif" letter-spacing="0.04em">四模块交互拓扑图</text>
<text x="600" y="56" font-size="11" fill="#4A5568" text-anchor="middle" font-family="Fira Sans, sans-serif">特种材料制备设备状态监测系统</text>
{edges_str}
{nodes_str}
</svg>
</div>
"""

    components.html(svg_html, height=820, scrolling=False)


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
