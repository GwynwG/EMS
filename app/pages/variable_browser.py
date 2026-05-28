"""变量字典浏览器页面。

展示所有 29 个监测变量的完整信息：中文名、单位、模块、当前值、趋势缩略图。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

from app.shared import (
    ROOT, load_model_results,
    ACCENT_BLUE, RISK_RED, HEALTH_GREEN, WARN_AMBER,
    TEXT_MAIN, TEXT_SECONDARY, TEXT_MUTED, BG_CONTENT, BORDER_MAIN,
    FONT_FAMILY, _get_base_layout,
)


_MODULE_CN = {
    "execution_control": "执行控制",
    "energy_input": "能量输入",
    "environmental_constraint": "环境约束",
    "state_maintenance": "状态维持",
}

_MODULE_COLORS = {
    "execution_control": ACCENT_BLUE,
    "energy_input": HEALTH_GREEN,
    "environmental_constraint": WARN_AMBER,
    "state_maintenance": RISK_RED,
}


@st.cache_data
def _load_variable_dict() -> list[dict]:
    """加载变量字典。"""
    path = ROOT / "configs" / "variable_dictionary.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("variables", [])
    return []


def _find_matching_column(var_name: str, columns: list[str]) -> str | None:
    """在数据列中找到匹配的变量列（原始变量名或带后缀的特征名）。"""
    # 精确匹配
    if var_name in columns:
        return var_name
    # 带 _raw 后缀
    if f"{var_name}_raw" in columns:
        return f"{var_name}_raw"
    # 带模块前缀
    for prefix in ["execution_control__", "energy_input__",
                   "environmental_constraint__", "state_maintenance__"]:
        col = f"{prefix}{var_name}"
        if col in columns:
            return col
        col_raw = f"{prefix}{var_name}_raw"
        if col_raw in columns:
            return col_raw
    # 模糊匹配
    for col in columns:
        if var_name in col and ("_raw" in col or "_current" in col or "_value" in col):
            return col
    return None


def render_variable_browser_page() -> None:
    st.markdown("# 变量字典")
    st.caption("特种材料制备设备 29 个监测变量的完整信息与实时状态")

    variables = _load_variable_dict()
    df = load_model_results()

    if not variables:
        st.warning("变量字典为空，请检查 configs/variable_dictionary.yaml")
        return

    # ── 模块筛选 ──
    modules = list(_MODULE_CN.keys())
    selected_module = st.selectbox(
        "筛选模块", ["全部"] + modules,
        format_func=lambda x: "全部模块" if x == "全部" else _MODULE_CN.get(x, x),
    )

    if selected_module != "全部":
        variables = [v for v in variables if v.get("module") == selected_module]

    # ── 统计概览 ──
    st.markdown("## 概览")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("变量总数", len(variables))
    with c2:
        enabled_count = sum(1 for v in variables if v.get("enabled", True))
        st.metric("启用变量", enabled_count)
    with c3:
        modules_count = len(set(v.get("module", "") for v in variables))
        st.metric("覆盖模块", modules_count)
    with c4:
        devices = set(v.get("device", "") for v in variables)
        st.metric("涉及设备", len(devices))

    st.markdown("---")

    # ── 变量列表（按模块分组）──
    st.markdown("## 变量详情")

    # 按模块分组
    by_module: dict[str, list[dict]] = {}
    for v in variables:
        mod = v.get("module", "unknown")
        by_module.setdefault(mod, []).append(v)

    for mod, vars_in_mod in by_module.items():
        mod_cn = _MODULE_CN.get(mod, mod)
        mod_color = _MODULE_COLORS.get(mod, ACCENT_BLUE)

        st.markdown(f"### {mod_cn}（{len(vars_in_mod)} 个变量）")

        # 表格形式展示
        table_data = []
        for v in vars_in_mod:
            var_name = v.get("standard_name", "")
            cn_name = v.get("chinese_name", var_name)
            unit = v.get("unit", "-")
            device = v.get("device", "-")
            usage = v.get("usage", "-")
            sampling = v.get("sampling_rate", "-")
            enabled = v.get("enabled", True)

            # 查找当前值
            current_val = "—"
            if not df.empty:
                col = _find_matching_column(var_name, df.columns)
                if col and col in df.columns:
                    last_val = df[col].iloc[-1]
                    current_val = f"{last_val:.2f}" if isinstance(last_val, float) else str(last_val)

            table_data.append({
                "变量名": var_name,
                "中文名": cn_name,
                "单位": unit,
                "当前值": current_val,
                "设备": device,
                "采样率": sampling,
                "用途": usage,
                "状态": "启用" if enabled else "禁用",
            })

        st.dataframe(pd.DataFrame(table_data), width="stretch", hide_index=True)

        # 趋势缩略图（每个变量一个小图）
        if not df.empty:
            with st.expander(f"查看 {mod_cn} 变量趋势", expanded=False):
                trend_cols = st.columns(3)
                for i, v in enumerate(vars_in_mod):
                    var_name = v.get("standard_name", "")
                    cn_name = v.get("chinese_name", var_name)
                    unit = v.get("unit", "")

                    col = _find_matching_column(var_name, df.columns)
                    if col and col in df.columns:
                        with trend_cols[i % 3]:
                            series = df[col].dropna().tail(200)
                            if len(series) > 0:
                                fig = go.Figure()
                                fig.add_trace(go.Scattergl(
                                    x=list(range(len(series))),
                                    y=series.values,
                                    mode="lines",
                                    line=dict(color=mod_color, width=1.5),
                                    fill="tozeroy",
                                    fillcolor=f"rgba({mod_color.lstrip('#')},0.05)" if mod_color.startswith("#") else None,
                                ))
                                fig.update_layout(
                                    title=dict(text=f"{cn_name} ({unit})", font=dict(size=11, color=TEXT_SECONDARY)),
                                    height=180,
                                    margin=dict(l=5, r=5, t=30, b=5),
                                    plot_bgcolor=BG_CONTENT,
                                    paper_bgcolor=BG_CONTENT,
                                    xaxis=dict(showgrid=False, showticklabels=False),
                                    yaxis=dict(showgrid=True, gridcolor=BORDER_MAIN, gridwidth=0.5,
                                              tickfont=dict(size=9, color=TEXT_MUTED)),
                                    font=dict(family=FONT_FAMILY),
                                )
                                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        st.markdown("---")
