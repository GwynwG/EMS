"""主要贡献变量表组件。"""
from __future__ import annotations

import streamlit as st

from src.visualization.theme import (
    BORDER_MAIN,
    TEXT_MAIN,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_BLUE,
    RISK_RED,
    FONT_FAMILY,
    FONT_MONO,
    TABLE_HEADER_BG,
    HIGHLIGHT_ROW_BG,
)
from src.visualization.dashboard_components import MODULE_SHORT_CHINESE


def _bar_html(value: float, color: str) -> str:
    pct = max(0, min(100, value * 100))
    return (
        f'<div style="display:inline-block; width:50px; height:5px; '
        f'background:#1B1D21; border-radius:3px; overflow:hidden; '
        f'vertical-align:middle; margin-left:4px;">'
        f'<div style="width:{pct}%; height:100%; background:{color}; border-radius:3px;"></div></div>'
    )


def render_contribution_table(variables: list[dict], selected_module: str = "") -> None:
    """渲染主要贡献变量表（前 15 条）。"""
    rows = ""
    for var in variables[:15]:
        module = var.get("module", "")
        is_sel = (module == selected_module) and selected_module != ""
        row_bg = HIGHLIGHT_ROW_BG if is_sel else ""
        bl = f"border-left: 3px solid {ACCENT_BLUE};" if is_sel else ""

        cd = var.get("contribution_degree", 0)
        cd_c = RISK_RED if cd > 0.5 else (ACCENT_BLUE if cd > 0.3 else TEXT_MUTED)

        status = var.get("status", "正常")
        st_c = RISK_RED if status == "预警" else (ACCENT_BLUE if status == "关注" else TEXT_MUTED)

        mod_cn = MODULE_SHORT_CHINESE.get(module, module)

        rows += f"""
        <tr style="background:{row_bg}; {bl}">
            <td style="padding:6px 10px; font-size:12px; color:{TEXT_SECONDARY}; font-family:{FONT_MONO};">{var.get('variable','')}</td>
            <td style="padding:6px 10px; font-size:13px; color:{TEXT_MAIN};">{var.get('chinese_name','')}</td>
            <td style="padding:6px 10px; font-size:12px; color:{TEXT_SECONDARY};">{mod_cn}</td>
            <td style="padding:6px 10px; font-size:13px; color:{TEXT_MAIN}; font-family:{FONT_MONO};">{var.get('current_value','')}</td>
            <td style="padding:6px 10px; font-size:12px; color:{TEXT_MUTED};">{var.get('unit','')}</td>
            <td style="padding:6px 10px; font-size:13px; color:{cd_c}; font-family:{FONT_MONO};">{cd:.2f}{_bar_html(cd, cd_c)}</td>
            <td style="padding:6px 10px; font-size:12px; color:{st_c}; font-weight:600;">{status}</td>
        </tr>"""

    st.markdown(
        f"""
        <div style="overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; font-family:{FONT_FAMILY};">
            <thead><tr style="background:{TABLE_HEADER_BG};">
                <th style="padding:6px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">变量</th>
                <th style="padding:6px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">中文名</th>
                <th style="padding:6px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">所属模块</th>
                <th style="padding:6px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">当前值</th>
                <th style="padding:6px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">单位</th>
                <th style="padding:6px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">贡献度</th>
                <th style="padding:6px 10px; text-align:left; font-size:12px; color:{TEXT_SECONDARY}; border-bottom:1px solid {BORDER_MAIN};">状态</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
