"""模块间耦合关系状态表组件。"""
from __future__ import annotations

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
    TABLE_HEADER_BG,
    TABLE_ROW_ALT,
    HIGHLIGHT_ROW_BG,
)


def _bar_html(value: float, color: str) -> str:
    pct = max(0, min(100, value * 100))
    return (
        f'<div style="display:inline-block; width:60px; height:6px; '
        f'background:#1B1D21; border-radius:3px; overflow:hidden; '
        f'vertical-align:middle; margin-left:6px;">'
        f'<div style="width:{pct}%; height:100%; background:{color}; border-radius:3px;"></div></div>'
    )


def render_relation_table(edges_data: list[dict], selected_id: str = "") -> None:
    """渲染模块间耦合关系状态表。"""
    type_labels = {"main": "主关系", "feedback": "反馈", "auxiliary": "辅助"}

    rows = ""
    for edge in edges_data:
        eid = edge.get("id", "")
        is_sel = (eid == selected_id)
        row_bg = HIGHLIGHT_ROW_BG if is_sel else ""
        bl = f"border-left: 3px solid {ACCENT_BLUE};" if is_sel else ""

        cs = edge.get("coupling_strength", 0)
        rl = edge.get("residual_level", 0)
        rc = edge.get("risk_contribution", 0)

        cs_c = RISK_RED if cs > 0.7 else (ACCENT_BLUE if cs > 0.4 else TEXT_MUTED)
        rl_c = RISK_RED if rl > 0.5 else (ACCENT_BLUE if rl > 0.3 else TEXT_MUTED)

        if rc > 0.6:
            rc_label, rc_c = "高", RISK_RED
        elif rc > 0.3:
            rc_label, rc_c = "中", ACCENT_BLUE
        else:
            rc_label, rc_c = "低", TEXT_MUTED

        st_text = edge.get("current_status", "正常")
        st_c = RISK_RED if st_text == "预警" else (ACCENT_BLUE if st_text == "关注" else TEXT_MUTED)

        rows += f"""
        <tr style="background:{row_bg}; {bl}">
            <td style="padding:8px 10px; font-size:13px; color:{TEXT_MAIN};">{edge.get('relation_name','')}</td>
            <td style="padding:8px 10px; font-size:12px; color:{TEXT_SECONDARY};">{type_labels.get(edge.get('relation_type',''), edge.get('relation_type',''))}</td>
            <td style="padding:8px 10px; font-size:13px; color:{cs_c}; font-family:{FONT_MONO};">{cs:.2f}{_bar_html(cs, cs_c)}</td>
            <td style="padding:8px 10px; font-size:13px; color:{rl_c}; font-family:{FONT_MONO};">{rl:.2f}{_bar_html(rl, rl_c)}</td>
            <td style="padding:8px 10px; font-size:12px; color:{rc_c}; font-weight:600;">{rc_label}</td>
            <td style="padding:8px 10px; font-size:12px; color:{TEXT_SECONDARY};">{edge.get('model_name','')}</td>
            <td style="padding:8px 10px; font-size:12px; color:{st_c}; font-weight:600;">{st_text}</td>
        </tr>"""

    st.markdown(
        f"""
        <div style="overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; font-family:{FONT_FAMILY};">
            <thead><tr style="background:{TABLE_HEADER_BG};">
                <th style="padding:8px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">关系</th>
                <th style="padding:8px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">类型</th>
                <th style="padding:8px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">耦合强度</th>
                <th style="padding:8px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">残差水平</th>
                <th style="padding:8px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">风险贡献</th>
                <th style="padding:8px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">对应模型</th>
                <th style="padding:8px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">当前状态</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
