"""Plotly 深色主题图表工具模块。

统一的颜色、字体和布局配置，确保所有图表与深色主题一致。
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.visualization.theme import (
    BG_CONTENT,
    BORDER_MAIN,
    TEXT_MAIN,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_BLUE,
    RISK_RED,
    FONT_FAMILY,
)


# 默认颜色循环
DEFAULT_COLORS = [ACCENT_BLUE, RISK_RED, TEXT_SECONDARY, TEXT_MUTED]

# 模块中文名映射（用于图例）
_MODULE_CN = {
    "execution_control": "执行控制",
    "energy_input": "能量输入",
    "environmental_constraint": "环境约束",
    "state_maintenance": "状态维持",
}


def _get_base_layout(title: str, height: int = 380) -> dict:
    """返回深色主题的 Plotly layout 配置。"""
    return dict(
        plot_bgcolor=BG_CONTENT,
        paper_bgcolor=BG_CONTENT,
        height=height,
        margin=dict(l=50, r=30, t=50, b=40),
        font=dict(color=TEXT_SECONDARY, family="Microsoft YaHei, PingFang SC, sans-serif", size=12),
        title=dict(text=title, font=dict(size=14, color=TEXT_MAIN)),
        xaxis=dict(
            gridcolor=BORDER_MAIN,
            zerolinecolor=BORDER_MAIN,
            showgrid=True,
            gridwidth=1,
        ),
        yaxis=dict(
            gridcolor=BORDER_MAIN,
            zerolinecolor=BORDER_MAIN,
            showgrid=True,
            gridwidth=1,
        ),
        legend=dict(
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        hovermode="x unified",
    )


def _series_to_x(series: pd.Series):
    """将 Series 的索引转为 x 轴数据。"""
    if isinstance(series.index, pd.DatetimeIndex):
        return series.index
    return list(range(len(series)))


def render_single_line_chart(
    series: pd.Series,
    title: str,
    color: str,
    y_label: str = "",
    height: int = 380,
) -> None:
    """渲染单线趋势图（全宽）。"""
    if series.empty:
        st.info(f"暂无 {title} 数据")
        return

    x = _series_to_x(series)
    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=x,
        y=series.values,
        mode="lines",
        name=title,
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=f"rgba({_hex_to_rgb(color)},0.05)",
    ))
    fig.update_layout(**_get_base_layout(title, height))
    if y_label:
        fig.update_yaxes(title_text=y_label)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_multi_line_chart(
    df: pd.DataFrame,
    columns: list[str],
    title: str,
    colors: list[str] | None = None,
    height: int = 380,
    y_label: str = "",
) -> None:
    """渲染多线趋势图（全宽）。"""
    if df.empty or not columns:
        st.info(f"暂无 {title} 数据")
        return

    if colors is None:
        colors = DEFAULT_COLORS

    x = _series_to_x(df[columns[0]])
    fig = go.Figure()
    for i, col in enumerate(columns):
        color = colors[i % len(colors)]
        display_name = _MODULE_CN.get(col, col)
        fig.add_trace(go.Scattergl(
            x=x,
            y=df[col].values,
            mode="lines",
            name=display_name,
            line=dict(color=color, width=2),
        ))
    fig.update_layout(**_get_base_layout(title, height))
    if y_label:
        fig.update_yaxes(title_text=y_label)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_trend_tab_content(df: pd.DataFrame) -> None:
    """渲染首页趋势监测 tab 的全部内容：风险分数 + 健康指数 + 模块评分。"""
    # 风险分数趋势
    if "risk_score" in df.columns:
        render_single_line_chart(
            df["risk_score"].tail(200),
            title="综合风险分数趋势",
            color=RISK_RED,
            y_label="风险分数",
        )

    # 健康指数趋势
    if "health_index" in df.columns:
        render_single_line_chart(
            df["health_index"].tail(200),
            title="健康指数趋势",
            color=ACCENT_BLUE,
            y_label="健康指数",
        )

    # 模块评分趋势
    module_cols = [c for c in df.columns if c.endswith("__module_score")]
    if module_cols:
        render_multi_line_chart(
            df[module_cols].tail(200),
            columns=module_cols,
            title="模块评分趋势",
            y_label="评分",
        )


def _hex_to_rgb(hex_color: str) -> str:
    """将 #RRGGBB 转为 'R, G, B' 字符串。"""
    h = hex_color.lstrip("#")
    return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"
