"""四模块状态监测关系图 - 纯 SVG 静态示意图（第三版）。

核心修复：
1. 所有连线从节点边缘出发，硬编码路径，不再穿过节点
2. 节点改为三层文字结构（标题+说明+评分）
3. SVG 图层顺序：边 → 标签 → 节点（节点在最上层）
4. 标签放在空白区域，不压节点

配色原则：仅蓝(#4FC1FF)+灰(#6B7280)+红(#FF6B6B)三类色。
"""
from __future__ import annotations

from typing import Any

import streamlit.components.v1 as components

from src.domain_framework.coupling_graph import CouplingGraph
from src.visualization.theme import (
    BG_GRAPH_INNER,
    BG_GRAPH_WRAP,
    BG_LABEL,
    BORDER_MAIN,
    TEXT_MAIN,
    TEXT_SECONDARY,
    TEXT_MUTED,
    TEXT_DESC,
    ACCENT_BLUE,
    RISK_RED,
    SELECTED_COLOR,
    SELECTED_STROKE_WIDTH,
    NODE_FILL,
    NODE_STROKE,
    NODE_STROKE_WIDTH,
    NODE_RADIUS,
    EDGE_COLORS,
    FONT_FAMILY,
    FONT_MONO,
)


# ── 节点布局定义 ──
# (cx, cy) = 节点中心坐标; w, h = 宽高
NODE_DEFS = [
    {"id": "execution_control",        "label": "执行控制模块",     "desc": "设定值 / 控制指令",          "cx": 600, "cy": 130, "w": 200, "h": 110, "group": "core"},
    {"id": "energy_input",             "label": "能量输入模块",     "desc": "功率 / 能量驱动",            "cx": 180, "cy": 360, "w": 200, "h": 110, "group": "core"},
    {"id": "environmental_constraint", "label": "环境约束模块",     "desc": "边界条件 / 外部约束",        "cx": 1020, "cy": 360, "w": 200, "h": 110, "group": "core"},
    {"id": "state_maintenance",        "label": "状态维持模块",     "desc": "温度 / 压力 / 振动状态",     "cx": 600, "cy": 540, "w": 220, "h": 116, "group": "core"},
    {"id": "coupling_residual",        "label": "复杂耦合/残差",    "desc": "多源耦合残差处理",           "cx": 180, "cy": 710, "w": 190, "h": 100, "group": "residual"},
    {"id": "model_residual",           "label": "模型残差",         "desc": "统计模型残差",               "cx": 600, "cy": 710, "w": 190, "h": 100, "group": "residual"},
    {"id": "intelligent_model",        "label": "智能补偿模型入口", "desc": "XGBoost / Autoencoder",      "cx": 1000, "cy": 710, "w": 200, "h": 100, "group": "model"},
    {"id": "diagnosis_layer",          "label": "诊断层",           "desc": "状态监测 / 异常预警",        "cx": 600, "cy": 870, "w": 190, "h": 100, "group": "diagnosis"},
]


# ── 边定义 — 每条边手动指定 SVG path 和标签位置 ──
# path: 从源节点边缘 → 目标节点边缘的 SVG path
# label_xy: 标签文字中心坐标 (放在空白区域)
EDGE_DEFS = [
    # ── 主关系（蓝色实线）──
    {
        "id": "execution_control__energy_input",
        "label": "执行→能量",
        "type": "main",
        # 从执行控制底部偏左 → 能量输入顶部偏右
        "path": "M 520 185 C 480 260, 260 280, 220 305",
        "label_xy": (350, 245),
    },
    {
        "id": "execution_control__environmental_constraint",
        "label": "执行→环境",
        "type": "main",
        # 从执行控制底部偏右 → 环境约束顶部偏左
        "path": "M 680 185 C 720 260, 940 280, 980 305",
        "label_xy": (850, 245),
    },
    {
        "id": "energy_input__state_maintenance",
        "label": "能量→状态",
        "type": "main",
        # 从能量输入右侧 → 状态维持顶部偏左
        "path": "M 280 370 C 360 380, 460 440, 510 482",
        "label_xy": (370, 420),
    },
    {
        "id": "environmental_constraint__state_maintenance",
        "label": "环境→状态",
        "type": "main",
        # 从环境约束左侧 → 状态维持顶部偏右
        "path": "M 920 370 C 840 380, 740 440, 690 482",
        "label_xy": (830, 420),
    },
    {
        "id": "state_maintenance__diagnosis_layer",
        "label": "状态→诊断",
        "type": "main",
        # 从状态维持底部偏右 → 诊断层顶部（曲线从右侧绕过模型残差）
        "path": "M 640 598 C 780 660, 750 800, 620 820",
        "label_xy": (750, 710),
    },

    # ── 反馈（蓝色虚线）──
    {
        "id": "state_maintenance__execution_control",
        "label": "反馈",
        "type": "feedback",
        # 从状态维持左侧 → 执行控制左侧，大弧线从左侧绕出
        "path": "M 490 530 C 350 520, 350 180, 500 140",
        "label_xy": (370, 350),
    },

    # ── 辅助线（灰色虚线）──
    {
        "id": "energy_input__coupling_residual",
        "label": "",
        "type": "auxiliary",
        # 从能量输入底部 → 耦合残差顶部
        "path": "M 180 415 C 180 500, 180 600, 180 660",
        "label_xy": (0, 0),
    },
    {
        "id": "environmental_constraint__coupling_residual",
        "label": "",
        "type": "auxiliary",
        # 从环境约束底部 → 耦合残差顶部，走外侧长弧
        "path": "M 1020 415 C 1100 500, 400 600, 240 660",
        "label_xy": (0, 0),
    },
    {
        "id": "execution_control__coupling_residual",
        "label": "",
        "type": "auxiliary",
        # 从执行控制左侧 → 耦合残差顶部，走外侧长弧
        "path": "M 500 140 C 350 150, 100 400, 120 660",
        "label_xy": (0, 0),
    },
    {
        "id": "coupling_residual__intelligent_model",
        "label": "",
        "type": "auxiliary",
        # 从耦合残差右侧 → 智能模型左侧，底部水平弧
        "path": "M 275 720 C 400 740, 750 740, 900 720",
        "label_xy": (0, 0),
    },
    {
        "id": "model_residual__intelligent_model",
        "label": "",
        "type": "auxiliary",
        # 从模型残差右侧 → 智能模型底部偏左
        "path": "M 695 720 C 750 740, 850 750, 940 740",
        "label_xy": (0, 0),
    },
    {
        "id": "intelligent_model__diagnosis_layer",
        "label": "",
        "type": "auxiliary",
        # 从智能模型底部 → 诊断层右侧
        "path": "M 1000 760 C 1000 810, 750 850, 695 870",
        "label_xy": (0, 0),
    },
]


def _score_to_text_color(score: float | None) -> str:
    """根据健康分数返回文字色：蓝色(正常) / 红色(低分)。"""
    if score is None:
        return TEXT_SECONDARY
    if score < 40:
        return RISK_RED
    return ACCENT_BLUE


def _build_arrow_marker(color: str, marker_id: str, size: float = 8) -> str:
    """生成箭头 marker 定义。"""
    h = size * 0.6
    return (
        f'<marker id="{marker_id}" markerWidth="{size}" markerHeight="{h}" '
        f'refX="{size}" refY="{h/2}" orient="auto" markerUnits="strokeWidth">'
        f'<polygon points="0 0, {size} {h/2}, 0 {h}" fill="{color}"/>'
        f'</marker>'
    )


def render_four_module_graph_svg(selected_id: str, module_scores: dict[str, float] | None = None) -> None:
    """渲染四模块状态监测关系图（纯 SVG）。

    Args:
        selected_id: 当前选中的节点或边 id
        module_scores: 核心四模块的健康分数
    """
    module_scores = module_scores or {}
    node_map = {nd["id"]: nd for nd in NODE_DEFS}

    # ════════════════════════════════════════════════════════════
    # defs：箭头 markers + 选中蓝色阴影
    # ════════════════════════════════════════════════════════════
    defs_parts = [
        f'<filter id="blueShadow" x="-30%" y="-30%" width="160%" height="160%">'
        f'<feGaussianBlur stdDeviation="3" result="blur"/>'
        f'<feFlood flood-color="{ACCENT_BLUE}" flood-opacity="0.20" result="color"/>'
        f'<feComposite in="color" in2="blur" operator="in" result="shadow"/>'
        f'<feMerge><feMergeNode in="shadow"/><feMergeNode in="SourceGraphic"/></feMerge>'
        f'</filter>',
    ]
    defs_parts.append(_build_arrow_marker(ACCENT_BLUE, "arrow_main"))
    defs_parts.append(_build_arrow_marker(ACCENT_BLUE, "arrow_feedback"))
    defs_parts.append(_build_arrow_marker(TEXT_MUTED, "arrow_auxiliary"))
    defs_parts.append(_build_arrow_marker(ACCENT_BLUE, "arrow_selected"))
    defs_str = "\n".join(defs_parts)

    # ════════════════════════════════════════════════════════════
    # 第一层：边（连线）
    # ════════════════════════════════════════════════════════════
    edge_parts = []
    for edge in EDGE_DEFS:
        ecfg = EDGE_COLORS.get(edge["type"], EDGE_COLORS["main"])
        is_sel = edge["id"] == selected_id

        color = ACCENT_BLUE if is_sel else ecfg["stroke"]
        width = SELECTED_STROKE_WIDTH if is_sel else ecfg["width"]

        dash = ""
        opacity = "0.85"
        if edge["type"] == "feedback":
            dash = 'stroke-dasharray="6,3"'
        elif edge["type"] == "auxiliary":
            dash = 'stroke-dasharray="4,3"'
            opacity = "0.6"
            if is_sel:
                opacity = "0.9"
                dash = ""

        marker = "url(#arrow_selected)" if is_sel else f"url(#arrow_{edge['type']})"

        edge_parts.append(
            f'<path d="{edge["path"]}" fill="none" stroke="{color}" '
            f'stroke-width="{width:.1f}" {dash} opacity="{opacity}" '
            f'marker-end="{marker}"/>'
        )

    edges_str = "\n".join(edge_parts)

    # ════════════════════════════════════════════════════════════
    # 第二层：边标签底板 + 标签文字
    # ════════════════════════════════════════════════════════════
    label_parts = []
    for edge in EDGE_DEFS:
        if not edge["label"]:
            continue
        lx, ly = edge["label_xy"]
        if lx == 0 and ly == 0:
            continue

        is_sel = edge["id"] == selected_id
        label_color = ACCENT_BLUE if is_sel else TEXT_SECONDARY
        font_w = "600" if is_sel else "400"
        text_len = len(edge["label"]) * 8 + 16

        # 底板
        label_parts.append(
            f'<rect x="{lx - text_len/2:.0f}" y="{ly - 11:.0f}" '
            f'width="{text_len:.0f}" height="20" rx="4" ry="4" '
            f'fill="{BG_LABEL}" opacity="0.92"/>'
        )
        # 文字
        label_parts.append(
            f'<text x="{lx:.0f}" y="{ly + 3:.0f}" '
            f'font-size="12" fill="{label_color}" text-anchor="middle" '
            f'font-weight="{font_w}" font-family="{FONT_FAMILY}" opacity="0.9">'
            f'{edge["label"]}</text>'
        )

    labels_str = "\n".join(label_parts)

    # ════════════════════════════════════════════════════════════
    # 第三层：节点（在最上层，覆盖线和标签）
    # ════════════════════════════════════════════════════════════
    node_parts = []
    for nd in NODE_DEFS:
        nid = nd["id"]
        is_sel = nid == selected_id
        score = module_scores.get(nid)

        fill = NODE_FILL
        stroke = ACCENT_BLUE if is_sel else NODE_STROKE
        stroke_w = SELECTED_STROKE_WIDTH if is_sel else NODE_STROKE_WIDTH
        shadow = ' filter="url(#blueShadow)"' if is_sel else ""

        x = nd["cx"] - nd["w"] / 2
        y = nd["cy"] - nd["h"] / 2
        r = NODE_RADIUS

        # 三层文字 y 坐标
        title_y = nd["cy"] - 28
        desc_y = nd["cy"] + 2
        score_y = nd["cy"] + 28

        # 第1层：标题
        title_text = (
            f'<text x="{nd["cx"]}" y="{title_y}" '
            f'font-size="20" fill="{TEXT_MAIN}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-weight="700" font-family="{FONT_FAMILY}">'
            f'{nd["label"]}</text>'
        )

        # 第2层：说明
        desc_text = (
            f'<text x="{nd["cx"]}" y="{desc_y}" '
            f'font-size="12" fill="{TEXT_DESC}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-weight="400" font-family="{FONT_FAMILY}">'
            f'{nd["desc"]}</text>'
        )

        # 第3层：评分/状态值
        score_text = ""
        if score is not None:
            score_color = _score_to_text_color(score)
            score_text = (
                f'<text x="{nd["cx"]}" y="{score_y}" '
                f'font-size="16" fill="{score_color}" '
                f'text-anchor="middle" dominant-baseline="middle" '
                f'font-weight="600" font-family="{FONT_MONO}">'
                f'{score:.1f}</text>'
            )

        node_parts.append(
            f'<g>'
            f'<rect x="{x:.0f}" y="{y:.0f}" width="{nd["w"]}" height="{nd["h"]}" '
            f'rx="{r}" ry="{r}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{stroke_w:.1f}"{shadow}/>'
            f'{title_text}'
            f'{desc_text}'
            f'{score_text}'
            f'</g>'
        )

    nodes_str = "\n".join(node_parts)

    # ════════════════════════════════════════════════════════════
    # 组装完整 HTML（注意图层顺序）
    # ════════════════════════════════════════════════════════════
    svg_html = f"""
<div style="background:{BG_GRAPH_WRAP}; border-radius:14px; border:1px solid {BORDER_MAIN};
            padding:24px; width:100%; box-sizing:border-box; overflow:hidden; pointer-events:none;">
<svg viewBox="0 0 1200 940" width="100%" height="940" preserveAspectRatio="xMidYMid meet"
     xmlns="http://www.w3.org/2000/svg" style="pointer-events:none; display:block; margin:0 auto;">
<defs>
{defs_str}
</defs>
<!-- 背景 -->
<rect x="0" y="0" width="1200" height="940" rx="8" ry="8" fill="{BG_GRAPH_INNER}"/>
<!-- 图标题 -->
<text x="600" y="42" font-size="26" font-weight="700" fill="{TEXT_MAIN}"
      text-anchor="middle" font-family="{FONT_FAMILY}">四模块状态监测关系图</text>
<text x="600" y="68" font-size="13" fill="{TEXT_MUTED}"
      text-anchor="middle" font-family="{FONT_FAMILY}">特种材料制备设备状态监测系统</text>
<!-- 第一层：连线 -->
{edges_str}
<!-- 第二层：标签 -->
{labels_str}
<!-- 第三层：节点（最上层） -->
{nodes_str}
</svg>
</div>
"""

    components.html(svg_html, height=1000, scrolling=False)


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
