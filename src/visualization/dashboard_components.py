"""Dashboard UI 组件 — 极简工业风格。

颜色仅使用：蓝(#4FC1FF) + 灰(#A7B0BD) + 红(#FF6B6B)
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from src.visualization.theme import (
    BG_CARD,
    BORDER_MAIN,
    TEXT_MAIN,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_BLUE,
    RISK_RED,
    FONT_FAMILY,
    FONT_MONO,
    STATUS_COLORS,
    BG_GRAPH_INNER,
    BG_SUMMARY_BLOCK,
    BORDER_SUMMARY,
    TABLE_HEADER_BG,
    TABLE_ROW_ALT,
    HIGHLIGHT_ROW_BG,
)

# ── 模块 ID → 中文名映射 ──
MODULE_ID_TO_CHINESE: dict[str, str] = {
    "execution_control": "执行控制模块",
    "energy_input": "能量输入模块",
    "environmental_constraint": "环境约束模块",
    "state_maintenance": "状态维持模块",
    "coupling_residual": "复杂耦合/残差",
    "model_residual": "模型残差",
    "intelligent_model": "智能补偿模型",
    "diagnosis_layer": "诊断层",
}

MODULE_SHORT_CHINESE: dict[str, str] = {
    "execution_control": "执行控制",
    "energy_input": "能量输入",
    "environmental_constraint": "环境约束",
    "state_maintenance": "状态维持",
    "coupling_residual": "耦合残差",
    "model_residual": "模型残差",
    "intelligent_model": "智能模型",
    "diagnosis_layer": "诊断层",
}


def _status_to_color(status: str) -> str:
    """状态 → 颜色：severe 用红，其他全用蓝。"""
    if status == "severe":
        return RISK_RED
    return ACCENT_BLUE


def render_kpi_card(
    label: str,
    value: str,
    subtext: str = "",
    status: str = "normal",
) -> None:
    """渲染统一 KPI 卡片。

    极简风格：背景统一 #2A2D33，左侧色条仅蓝/红两色。
    """
    color = _status_to_color(status)
    st.markdown(
        f"""
        <div style="
            background: {BG_CARD};
            border: 1px solid {BORDER_MAIN};
            border-left: 3px solid {color};
            border-radius: 12px;
            padding: 18px 20px;
            height: 122px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: visible;
            box-sizing: border-box;
        ">
            <div style="
                font-size: 12px;
                color: {TEXT_SECONDARY};
                font-weight: 500;
                letter-spacing: 0.02em;
                font-family: {FONT_FAMILY};
                white-space: normal;
                word-break: break-word;
            ">{label}</div>
            <div style="
                font-size: 30px;
                line-height: 1.15;
                font-weight: 700;
                color: {color};
                font-family: {FONT_MONO};
                white-space: normal;
                word-break: break-word;
            ">{value}</div>
            {"<div style='font-size: 11px; color: " + TEXT_MUTED + "; line-height: 1.3; white-space: normal; word-break: break-word;'>" + subtext + "</div>" if subtext else "<div style='font-size: 11px;'>&nbsp;</div>"}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_coupling_text(coupling_str: str) -> str:
    """将耦合关系文本格式化为中文短文本。"""
    for sep in [" ↔ ", " ↔ ", " → ", " -> ", " - "]:
        if sep in coupling_str:
            parts = coupling_str.split(sep)
            if len(parts) == 2:
                src = MODULE_SHORT_CHINESE.get(parts[0].strip(), parts[0].strip())
                tgt = MODULE_SHORT_CHINESE.get(parts[1].strip(), parts[1].strip())
                return f"{src} → {tgt}"
    if coupling_str.strip() in MODULE_SHORT_CHINESE:
        return MODULE_SHORT_CHINESE[coupling_str.strip()]
    return coupling_str


def render_metric_card(
    title: str,
    value: str | float,
    delta: str | None = None,
    color: str | None = None,
) -> None:
    """渲染指标卡片（兼容旧接口）。"""
    if color is None:
        color = ACCENT_BLUE
    st.markdown(
        f"""
        <div style="
            background: {BG_CARD};
            border: 1px solid {BORDER_MAIN};
            border-radius: 12px;
            padding: 18px 20px;
            height: 122px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: visible;
            box-sizing: border-box;
        ">
            <div style="
                font-size: 12px;
                color: {TEXT_SECONDARY};
                font-weight: 500;
                letter-spacing: 0.02em;
                font-family: {FONT_FAMILY};
            ">{title}</div>
            <div style="
                font-size: 28px;
                font-weight: 700;
                color: {color};
                word-wrap: break-word;
                font-family: {FONT_MONO};
            ">{value}</div>
            {f'<div style="font-size: 11px; color: {TEXT_MUTED};">{delta}</div>' if delta else '<div style="font-size: 11px;">&nbsp;</div>'}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_risk_badge(level: str) -> str:
    """返回风险等级对应的 HTML 徽章。"""
    label_map = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}
    color = RISK_RED if level == "severe" else ACCENT_BLUE
    label = label_map.get(level, level)
    return (
        f'<span style="background:{color}1A; color:{color}; padding:4px 14px; '
        f'border-radius:4px; font-size:12px; font-weight:600; border:1px solid {color}44;'
        f'letter-spacing:0.05em;">{label}</span>'
    )


def render_module_score_bar(module_name: str, score: float, chinese_name: str) -> None:
    """渲染模块评分条。"""
    color = RISK_RED if score < 40 else ACCENT_BLUE

    st.markdown(
        f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 13px; color: {TEXT_SECONDARY}; font-family: {FONT_FAMILY};">{chinese_name}</span>
                <span style="font-size: 14px; color: {color}; font-weight: 600; font-family: {FONT_MONO};">{score:.1f}</span>
            </div>
            <div style="background: {BG_GRAPH_INNER}; border-radius: 3px; height: 6px; overflow: hidden;">
                <div style="background: {color}; width: {score}%; height: 100%; border-radius: 3px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alarm_item(alarm: dict[str, Any]) -> None:
    """渲染单条预警记录。"""
    level = alarm.get("level", "normal")
    color = RISK_RED if level == "severe" else ACCENT_BLUE
    st.markdown(
        f"""
        <div style="
            border-left: 3px solid {color};
            padding: 10px 14px;
            margin-bottom: 8px;
            background: {BG_CARD};
            border-radius: 0 8px 8px 0;
            border: 1px solid {BORDER_MAIN};
            border-left-color: {color};
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; color: {color}; font-size: 11px;
                             letter-spacing: 0.06em;
                             background: {color}15; padding: 2px 8px; border-radius: 3px;
                             font-family: {FONT_FAMILY};">{level.upper()}</span>
                <span style="font-size: 11px; color: {TEXT_MUTED}; font-family: {FONT_MONO};">{alarm.get('timestamp', '')}</span>
            </div>
            <div style="font-size: 13px; color: {TEXT_MAIN}; margin-top: 6px; line-height: 1.5;">{alarm.get('message', '')}</div>
            <div style="font-size: 11px; color: {TEXT_MUTED}; margin-top: 4px;">模块: {alarm.get('module', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════
# 驾驶舱新增组件
# ════════════════════════════════════════════════════════════

def render_kpi_card_3layer(
    label: str,
    value: str,
    subtext: str = "",
    status: str = "normal",
) -> None:
    """渲染 3 层 KPI 卡片（驾驶舱版）。

    使用 min-height 替代固定高度，解决文字溢出问题。
    """
    color = _status_to_color(status)
    sub_html = (
        f"<div style='font-size: 11px; color: {TEXT_MUTED}; line-height: 1.3; "
        f"white-space: normal; word-break: break-word;'>{subtext}</div>"
        if subtext
        else "<div style='font-size: 11px;'>&nbsp;</div>"
    )
    st.markdown(
        f"""
        <div style="
            background: {BG_CARD};
            border: 1px solid {BORDER_MAIN};
            border-left: 3px solid {color};
            border-radius: 10px;
            padding: 14px 16px;
            min-height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: visible;
            box-sizing: border-box;
        " title="{value}">
            <div style="
                font-size: 12px;
                color: {TEXT_SECONDARY};
                font-weight: 500;
                letter-spacing: 0.02em;
                font-family: {FONT_FAMILY};
                white-space: normal;
                word-break: break-word;
            ">{label}</div>
            <div style="
                font-size: 26px;
                line-height: 1.15;
                font-weight: 700;
                color: {color};
                font-family: {FONT_MONO};
                white-space: normal;
                word-break: break-word;
                overflow-wrap: break-word;
            ">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_system_status_summary_blocks(data: dict) -> None:
    """渲染系统状态摘要区（4 个区块）。"""
    from src.visualization.summary_cards import (
        render_data_link_status_block,
        render_model_status_block,
        render_risk_sources_block,
        render_recommended_focus_block,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_data_link_status_block(data.get("data_link", {}))
    with col2:
        render_model_status_block(data.get("model_status", {}))
    with col3:
        render_risk_sources_block(data.get("risk_sources", {}))
    with col4:
        render_recommended_focus_block(data.get("recommended_focus", {}))


def _progress_bar_html(value: float, color: str = ACCENT_BLUE) -> str:
    """生成内联进度条 HTML。"""
    pct = max(0, min(100, value * 100))
    return (
        f'<div style="display:inline-block; width:60px; height:6px; background:{BG_GRAPH_INNER}; '
        f'border-radius:3px; overflow:hidden; vertical-align:middle; margin-left:6px;">'
        f'<div style="width:{pct}%; height:100%; background:{color}; border-radius:3px;"></div></div>'
    )


def render_relationship_status_table(edges_data: list[dict], selected_id: str = "") -> None:
    """渲染模块间耦合关系状态表。"""
    type_labels = {"main": "主关系", "feedback": "反馈", "auxiliary": "辅助", "risk_fusion": "风险融合"}
    contribution_colors = {
        "高": RISK_RED,
        "中": ACCENT_BLUE,
        "低": TEXT_MUTED,
    }

    rows_html = ""
    for edge in edges_data:
        eid = edge.get("id", "")
        is_selected = (eid == selected_id)
        row_bg = HIGHLIGHT_ROW_BG if is_selected else ""
        border_left = f"border-left: 3px solid {ACCENT_BLUE};" if is_selected else ""

        cs = edge.get("coupling_strength", 0)
        rl = edge.get("residual_level", 0)
        rc = edge.get("risk_contribution", 0)

        # 风险贡献等级
        if rc > 0.6:
            rc_label = "高"
        elif rc > 0.3:
            rc_label = "中"
        else:
            rc_label = "低"
        rc_color = contribution_colors.get(rc_label, TEXT_MUTED)

        # 耦合强度颜色
        cs_color = RISK_RED if cs > 0.7 else (ACCENT_BLUE if cs > 0.4 else TEXT_MUTED)
        rl_color = RISK_RED if rl > 0.5 else (ACCENT_BLUE if rl > 0.3 else TEXT_MUTED)

        status = edge.get("current_status", "正常")
        status_color = RISK_RED if status == "预警" else (ACCENT_BLUE if status == "关注" else TEXT_MUTED)

        rows_html += f"""
        <tr style="background: {row_bg}; {border_left}">
            <td style="padding: 8px 10px; font-size: 13px; color: {TEXT_MAIN}; font-family: {FONT_FAMILY};">{edge.get('relation_name', '')}</td>
            <td style="padding: 8px 10px; font-size: 12px; color: {TEXT_SECONDARY};">{type_labels.get(edge.get('relation_type', ''), edge.get('relation_type', ''))}</td>
            <td style="padding: 8px 10px; font-size: 13px; color: {cs_color}; font-family: {FONT_MONO};">{cs:.2f}{_progress_bar_html(cs, cs_color)}</td>
            <td style="padding: 8px 10px; font-size: 13px; color: {rl_color}; font-family: {FONT_MONO};">{rl:.2f}{_progress_bar_html(rl, rl_color)}</td>
            <td style="padding: 8px 10px; font-size: 12px; color: {rc_color}; font-weight: 600;">{rc_label}</td>
            <td style="padding: 8px 10px; font-size: 12px; color: {TEXT_SECONDARY};">{edge.get('model_name', '')}</td>
            <td style="padding: 8px 10px; font-size: 12px; color: {status_color}; font-weight: 600;">{status}</td>
        </tr>"""

    st.markdown(
        f"""
        <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-family: {FONT_FAMILY};">
            <thead>
                <tr style="background: {TABLE_HEADER_BG};">
                    <th style="padding: 8px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">关系</th>
                    <th style="padding: 8px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">类型</th>
                    <th style="padding: 8px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">耦合强度</th>
                    <th style="padding: 8px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">残差水平</th>
                    <th style="padding: 8px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">风险贡献</th>
                    <th style="padding: 8px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">对应模型</th>
                    <th style="padding: 8px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">当前状态</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_contribution_variables_table(variables: list[dict], selected_module: str = "") -> None:
    """渲染主要贡献变量表。"""
    rows_html = ""
    for var in variables[:15]:
        module = var.get("module", "")
        is_selected = (module == selected_module) and selected_module != ""
        row_bg = HIGHLIGHT_ROW_BG if is_selected else ""
        border_left = f"border-left: 3px solid {ACCENT_BLUE};" if is_selected else ""

        cd = var.get("contribution_degree", 0)
        cd_color = RISK_RED if cd > 0.5 else (ACCENT_BLUE if cd > 0.3 else TEXT_MUTED)

        status = var.get("status", "正常")
        status_color = RISK_RED if status == "预警" else (ACCENT_BLUE if status == "关注" else TEXT_MUTED)

        module_cn = MODULE_SHORT_CHINESE.get(module, module)

        rows_html += f"""
        <tr style="background: {row_bg}; {border_left}">
            <td style="padding: 6px 10px; font-size: 12px; color: {TEXT_SECONDARY}; font-family: {FONT_MONO};">{var.get('variable', '')}</td>
            <td style="padding: 6px 10px; font-size: 13px; color: {TEXT_MAIN};">{var.get('chinese_name', '')}</td>
            <td style="padding: 6px 10px; font-size: 12px; color: {TEXT_SECONDARY};">{module_cn}</td>
            <td style="padding: 6px 10px; font-size: 13px; color: {TEXT_MAIN}; font-family: {FONT_MONO};">{var.get('current_value', '')}</td>
            <td style="padding: 6px 10px; font-size: 12px; color: {TEXT_MUTED};">{var.get('unit', '')}</td>
            <td style="padding: 6px 10px; font-size: 13px; color: {cd_color}; font-family: {FONT_MONO};">{cd:.2f}{_progress_bar_html(cd, cd_color)}</td>
            <td style="padding: 6px 10px; font-size: 12px; color: {status_color}; font-weight: 600;">{status}</td>
        </tr>"""

    st.markdown(
        f"""
        <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-family: {FONT_FAMILY};">
            <thead>
                <tr style="background: {TABLE_HEADER_BG};">
                    <th style="padding: 6px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">变量</th>
                    <th style="padding: 6px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">中文名</th>
                    <th style="padding: 6px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">所属模块</th>
                    <th style="padding: 6px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">当前值</th>
                    <th style="padding: 6px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">单位</th>
                    <th style="padding: 6px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">贡献度</th>
                    <th style="padding: 6px 10px; text-align: left; font-size: 12px; color: {TEXT_SECONDARY}; font-weight: 600; border-bottom: 1px solid {BORDER_MAIN};">状态</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_module_relation_display(relation_str: str) -> str:
    """将模块关系字符串格式化为中文显示（支持 → 箭头）。"""
    for sep in [" ↔ ", " ↔ ", " → ", " -> ", " - ", " <-> "]:
        if sep in relation_str:
            parts = relation_str.split(sep)
            if len(parts) == 2:
                src = MODULE_SHORT_CHINESE.get(parts[0].strip(), parts[0].strip())
                tgt = MODULE_SHORT_CHINESE.get(parts[1].strip(), parts[1].strip())
                return f"{src} → {tgt}"
    if relation_str.strip() in MODULE_SHORT_CHINESE:
        return MODULE_SHORT_CHINESE[relation_str.strip()]
    return relation_str
