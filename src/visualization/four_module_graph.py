"""四模块状态监测关系图 - 纯 SVG 静态示意图（第四版：驾驶舱升级）。

5 层领域模型布局：执行控制 → 作用条件 → 核心状态 → 残差补偿 → 诊断决策。
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


# ── 节点布局定义（5 层）──
# (cx, cy) = 节点中心坐标; w, h = 宽高
# viewBox: 0 0 1200 940
NODE_DEFS = [
    # Layer 1: 执行控制（顶部居中）
    {"id": "execution_control",        "label": "执行控制模块",     "desc": "设定值 / 控制指令 / 控制模式",  "cx": 600, "cy": 120, "w": 220, "h": 110, "group": "core"},
    # Layer 2: 作用条件（左右对称）
    {"id": "energy_input",             "label": "能量输入模块",     "desc": "功率 / 电压 / 能量驱动",       "cx": 220, "cy": 310, "w": 210, "h": 110, "group": "core"},
    {"id": "environmental_constraint", "label": "环境约束模块",     "desc": "冷却水 / 气压 / 环境边界",     "cx": 980, "cy": 310, "w": 210, "h": 110, "group": "core"},
    # Layer 3: 核心状态（居中）
    {"id": "state_maintenance",        "label": "状态维持模块",     "desc": "温度 / 压力 / 振动 / 稳定性",  "cx": 600, "cy": 500, "w": 240, "h": 120, "group": "core"},
    # Layer 4: 残差补偿（三列）
    {"id": "coupling_residual",        "label": "复杂耦合/残差",    "desc": "多源耦合残差处理",             "cx": 180, "cy": 690, "w": 200, "h": 100, "group": "residual"},
    {"id": "model_residual",           "label": "模型残差",         "desc": "PCA/PLS 统计残差",             "cx": 600, "cy": 690, "w": 200, "h": 100, "group": "residual"},
    {"id": "intelligent_model",        "label": "智能补偿模型",     "desc": "XGBoost / Autoencoder",        "cx": 1020, "cy": 690, "w": 210, "h": 100, "group": "model"},
    # Layer 5: 诊断决策（底部居中）
    {"id": "diagnosis_layer",          "label": "诊断层",           "desc": "状态监测 / 异常预警 / 寿命评估", "cx": 600, "cy": 860, "w": 200, "h": 100, "group": "diagnosis"},
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
        "path": "M 510 175 C 460 230, 300 250, 260 255",
        "label_xy": (370, 215),
    },
    {
        "id": "execution_control__environmental_constraint",
        "label": "执行→环境",
        "type": "main",
        "path": "M 690 175 C 740 230, 900 250, 935 255",
        "label_xy": (830, 215),
    },
    {
        "id": "energy_input__state_maintenance",
        "label": "能量→状态",
        "type": "main",
        "path": "M 325 365 C 400 380, 460 430, 500 440",
        "label_xy": (390, 400),
    },
    {
        "id": "environmental_constraint__state_maintenance",
        "label": "环境→状态",
        "type": "main",
        "path": "M 875 365 C 800 380, 740 430, 700 440",
        "label_xy": (810, 400),
    },
    {
        "id": "state_maintenance__diagnosis_layer",
        "label": "状态→诊断",
        "type": "main",
        "path": "M 600 560 C 600 620, 600 790, 600 810",
        "label_xy": (630, 700),
    },

    # ── 反馈（蓝色虚线）──
    {
        "id": "state_maintenance__execution_control",
        "label": "反馈",
        "type": "feedback",
        "path": "M 480 490 C 320 480, 320 180, 490 130",
        "label_xy": (340, 320),
    },

    # ── 辅助线（灰色虚线）──
    {
        "id": "energy_input__coupling_residual",
        "label": "",
        "type": "auxiliary",
        "path": "M 220 365 C 220 460, 200 580, 190 640",
        "label_xy": (0, 0),
    },
    {
        "id": "environmental_constraint__coupling_residual",
        "label": "",
        "type": "auxiliary",
        "path": "M 980 365 C 1080 480, 400 560, 260 640",
        "label_xy": (0, 0),
    },
    {
        "id": "execution_control__coupling_residual",
        "label": "",
        "type": "auxiliary",
        "path": "M 490 175 C 340 190, 100 420, 120 640",
        "label_xy": (0, 0),
    },
    {
        "id": "coupling_residual__intelligent_model",
        "label": "",
        "type": "auxiliary",
        "path": "M 280 710 C 420 730, 780 730, 915 710",
        "label_xy": (0, 0),
    },
    {
        "id": "model_residual__intelligent_model",
        "label": "",
        "type": "auxiliary",
        "path": "M 700 700 C 780 720, 860 720, 915 710",
        "label_xy": (0, 0),
    },
    {
        "id": "intelligent_model__diagnosis_layer",
        "label": "",
        "type": "auxiliary",
        "path": "M 1020 740 C 1020 800, 780 850, 700 860",
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
        f'<feGaussianBlur stdDeviation="2" result="blur"/>'
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
            f'font-size="13" fill="{label_color}" text-anchor="middle" '
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
            f'font-size="22" fill="{TEXT_MAIN}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-weight="700" font-family="{FONT_FAMILY}" '
            f'text-rendering="optimizeLegibility">'
            f'{nd["label"]}</text>'
        )

        # 第2层：说明
        desc_text = (
            f'<text x="{nd["cx"]}" y="{desc_y}" '
            f'font-size="13" fill="{TEXT_DESC}" '
            f'text-anchor="middle" dominant-baseline="middle" '
            f'font-weight="400" font-family="{FONT_FAMILY}" '
            f'text-rendering="optimizeLegibility">'
            f'{nd["desc"]}</text>'
        )

        # 第3层：评分/状态值
        score_text = ""
        if score is not None:
            score_color = _score_to_text_color(score)
            score_text = (
                f'<text x="{nd["cx"]}" y="{score_y}" '
                f'font-size="18" fill="{score_color}" '
                f'text-anchor="middle" dominant-baseline="middle" '
                f'font-weight="600" font-family="{FONT_MONO}" '
                f'text-rendering="optimizeLegibility">'
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
    """获取模块详情（统一从 MODULE_REGISTRY 获取）。"""
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
        return {"name": node_id, "description": "未知节点"}


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
