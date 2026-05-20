"""Plotly 深色主题图表工具模块。

统一的颜色、字体和布局配置，确保所有图表与深色主题一致。
提供特征分类、特征名中文化、分类绘图等功能。
"""
from __future__ import annotations

import numpy as np
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


# ── 扩展颜色色板（8 色，低饱和、区分度高）──
PALETTE = [
    "#4FC1FF",  # 蓝
    "#FF6B6B",  # 红
    "#4EC9B0",  # 青
    "#DCDCAA",  # 黄
    "#C586C0",  # 紫
    "#D7BA7D",  # 棕
    "#A7B0BD",  # 灰
    "#6B7280",  # 深灰
]

# 模块中文名映射
_MODULE_CN = {
    "execution_control": "执行控制",
    "energy_input": "能量输入",
    "environmental_constraint": "环境约束",
    "state_maintenance": "状态维持",
}

# ── 变量名中文映射 ──
_VAR_NAME_CN = {
    "setpoint_temperature": "设定温度",
    "valve_position": "阀位",
    "control_mode": "控制模式",
    "temperature": "温度",
    "pressure": "压力",
    "vibration": "振动",
    "power": "功率",
    "voltage": "电压",
    "current": "电流",
    "flow_rate": "流量",
    "level": "液位",
    "speed": "转速",
    "frequency": "频率",
    "humidity": "湿度",
    "concentration": "浓度",
    "ph_value": "pH值",
    "density": "密度",
    "viscosity": "粘度",
    "torque": "扭矩",
    "displacement": "位移",
    "acceleration": "加速度",
    "rotation": "转速",
    "input_power": "输入功率",
    "output_power": "输出功率",
    "energy_consumption": "能耗",
    "efficiency": "效率",
    "ambient_temperature": "环境温度",
    "ambient_humidity": "环境湿度",
    "cooling_water_temp": "冷却水温度",
    "cooling_water_flow": "冷却水流量",
    "vibration_x": "X轴振动",
    "vibration_y": "Y轴振动",
    "vibration_z": "Z轴振动",
    "bearing_temp": "轴承温度",
    "motor_current": "电机电流",
    "motor_voltage": "电机电压",
    "oil_temperature": "油温",
    "oil_pressure": "油压",
    "oil_level": "油位",
}

# ── 后缀中文映射 ──
_SUFFIX_CN = {
    "_raw": "原值",
    "_current": "当前值",
    "_value": "值",
    "_mean": "均值",
    "_std": "标准差",
    "_max": "最大值",
    "_min": "最小值",
    "_range": "范围",
    "_median": "中位数",
    "_quantile": "分位数",
    "_variance": "方差",
    "_cummean": "累积均值",
    "_cumstd": "累积标准差",
    "_change_rate": "变化率",
    "_pct_change": "变化百分比",
    "_diff": "差分",
    "_slope": "斜率",
    "_acceleration": "加速度",
    "_rolling_mean_10": "10点滚动均值",
    "_rolling_std_10": "10点滚动标准差",
    "_rolling_mean_20": "20点滚动均值",
    "_rolling_std_20": "20点滚动标准差",
    "_lag_1": "滞后1期",
    "_lag_3": "滞后3期",
    "_lag_5": "滞后5期",
    "_jump_count": "跳变计数",
    "_exceed_count": "超限计数",
    "_missing_rate": "缺失率",
    "_frozen_rate": "冻结率",
    "_anomaly_score": "异常分数",
    "_residual": "残差",
}

# ── 特征分类后缀（按优先级排序，用 endswith 匹配）──
_CATEGORY_SUFFIXES = {
    "异常健康": ["_anomaly_score", "_residual", "_spe", "_t2", "_risk_score",
                "_health_index", "_missing_rate", "_frozen_rate"],
    "事件模式": ["_jump_count", "_exceed_count", "_alarm", "_event",
                "_operation", "_switch", "_interlock", "_mode"],
    "动态变化": ["_change_rate", "_pct_change", "_diff", "_slope",
                "_acceleration", "_rolling_mean_10", "_rolling_std_10",
                "_rolling_mean_20", "_rolling_std_20", "_lag_1", "_lag_3", "_lag_5"],
    "统计特征": ["_mean", "_std", "_max", "_min", "_range", "_median",
                "_quantile", "_variance", "_cummean", "_cumstd"],
    "原始变量": ["_raw", "_current", "_value"],
}


# ════════════════════════════════════════════════════════════
# 基础布局
# ════════════════════════════════════════════════════════════

def _get_base_layout(title: str, height: int = 380, n_traces: int = 1) -> dict:
    """返回深色主题的 Plotly layout 配置。"""
    # 曲线 > 4 条时 legend 放右侧纵向，否则放底部横向
    if n_traces > 4:
        legend_cfg = dict(
            font=dict(size=12, color="#E6EDF3"),
            orientation="v",
            yanchor="top",
            y=1.0,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(0,0,0,0)",
        )
        margin = dict(l=40, r=120, t=50, b=40)
    else:
        legend_cfg = dict(
            font=dict(size=12, color="#E6EDF3"),
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
        )
        margin = dict(l=40, r=30, t=50, b=80)

    return dict(
        plot_bgcolor=BG_CONTENT,
        paper_bgcolor=BG_CONTENT,
        height=height,
        margin=margin,
        font=dict(color="#E6EDF3", family="Microsoft YaHei, PingFang SC, sans-serif", size=13),
        title=dict(text=title, font=dict(size=14, color=TEXT_MAIN)),
        xaxis=dict(gridcolor=BORDER_MAIN, zerolinecolor=BORDER_MAIN, showgrid=True, gridwidth=1),
        yaxis=dict(gridcolor=BORDER_MAIN, zerolinecolor=BORDER_MAIN, showgrid=True, gridwidth=1),
        legend=legend_cfg,
        hovermode="x unified",
    )


def _series_to_x(series: pd.Series):
    """将 Series 的索引转为 x 轴数据。"""
    if isinstance(series.index, pd.DatetimeIndex):
        return series.index
    return list(range(len(series)))


def _hex_to_rgb(hex_color: str) -> str:
    """将 #RRGGBB 转为 'R, G, B' 字符串。"""
    h = hex_color.lstrip("#")
    return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"


# ════════════════════════════════════════════════════════════
# 特征名中文化
# ════════════════════════════════════════════════════════════

def simplify_feature_name(col_name: str, module_prefix: str) -> str:
    """将特征列名简化为中文显示名。

    例: execution_control__valve_position_change_rate → 阀位 · 变化率
    """
    prefix = module_prefix + "__"
    name = col_name
    if name.startswith(prefix):
        name = name[len(prefix):]

    # 匹配后缀（从长到短匹配）
    suffix_cn = ""
    sorted_suffixes = sorted(_SUFFIX_CN.items(), key=lambda x: len(x[0]), reverse=True)
    for suffix, cn in sorted_suffixes:
        if name.endswith(suffix):
            suffix_cn = cn
            name = name[:-len(suffix)]
            break

    # 变量名中文映射
    var_cn = _VAR_NAME_CN.get(name, name)

    # 组合
    if suffix_cn:
        return f"{var_cn} · {suffix_cn}"
    return var_cn


# ════════════════════════════════════════════════════════════
# 特征分类
# ════════════════════════════════════════════════════════════

def classify_feature_columns(columns: list[str], module_prefix: str) -> dict[str, list[str]]:
    """将模块特征列按后缀分为 5 类（用 endswith 匹配，避免子串误匹配）。"""
    result: dict[str, list[str]] = {cat: [] for cat in _CATEGORY_SUFFIXES}

    for col in columns:
        # 去掉模块前缀
        name = col
        prefix = module_prefix + "__"
        if name.startswith(prefix):
            name = name[len(prefix):]

        matched = False
        for category, suffixes in _CATEGORY_SUFFIXES.items():
            for suffix in suffixes:
                if name.endswith(suffix):
                    result[category].append(col)
                    matched = True
                    break
            if matched:
                break

        if not matched:
            result["原始变量"].append(col)

    return result


def get_top_features_by_variance(df: pd.DataFrame, columns: list[str], top_k: int = 6) -> list[str]:
    """按方差取前 K 个特征列名。"""
    if len(columns) <= top_k:
        return columns
    variances = df[columns].var()
    return list(variances.nlargest(top_k).index)


# ════════════════════════════════════════════════════════════
# 单线 / 多线图表
# ════════════════════════════════════════════════════════════

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
    fig.update_layout(**_get_base_layout(title, height, n_traces=1))
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
    display_names: dict[str, str] | None = None,
) -> None:
    """渲染多线趋势图（全宽）。"""
    if df.empty or not columns:
        st.info(f"暂无 {title} 数据")
        return

    if colors is None:
        colors = PALETTE
    if display_names is None:
        display_names = {}

    x = _series_to_x(df[columns[0]])
    fig = go.Figure()
    for i, col in enumerate(columns):
        color = colors[i % len(colors)]
        display_name = display_names.get(col, _MODULE_CN.get(col, col))
        fig.add_trace(go.Scattergl(
            x=x,
            y=df[col].values,
            mode="lines",
            name=display_name,
            line=dict(color=color, width=2),
        ))
    fig.update_layout(**_get_base_layout(title, height, n_traces=len(columns)))
    if y_label:
        fig.update_yaxes(title_text=y_label)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════
# 分类绘图
# ════════════════════════════════════════════════════════════

def render_category_chart(
    df: pd.DataFrame,
    columns: list[str],
    category_name: str,
    module_prefix: str,
    max_lines: int = 8,
    height: int = 380,
) -> None:
    """按分类渲染特征趋势图，自动控制曲线数量和 legend。"""
    if not columns:
        st.info(f"暂无 {category_name} 数据")
        return

    # 控制曲线数量
    if len(columns) > max_lines:
        display_cols = get_top_features_by_variance(df, columns, max_lines)
        st.caption(f"显示方差最大的 {max_lines}/{len(columns)} 条曲线，共 {len(columns)} 个特征")
    else:
        display_cols = columns

    # 构建中文名映射
    display_names = {col: simplify_feature_name(col, module_prefix) for col in display_cols}

    render_multi_line_chart(
        df,
        columns=display_cols,
        title=f"{category_name}趋势",
        height=height,
        display_names=display_names,
    )


# ════════════════════════════════════════════════════════════
# 趋势监测 Tab 内容
# ════════════════════════════════════════════════════════════

def render_trend_tab_content(df: pd.DataFrame) -> None:
    """渲染首页趋势监测 tab：风险分数 + 健康指数 + 模块评分。"""
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

    # 模块评分趋势（动态计算）
    _render_module_score_trend(df)


def _render_module_score_trend(df: pd.DataFrame) -> None:
    """动态计算并渲染四模块评分趋势。"""
    from src.domain_framework.module_scoring import ModuleScorer

    module_prefixes = [
        "execution_control",
        "energy_input",
        "environmental_constraint",
        "state_maintenance",
    ]

    scores_data = {}
    for mod in module_prefixes:
        cols = [c for c in df.columns if c.startswith(f"{mod}__")]
        if cols:
            scores_data[_MODULE_CN.get(mod, mod)] = df[cols].apply(
                lambda row: ModuleScorer.compute_module_score(row), axis=1
            )

    if not scores_data:
        return

    scores_df = pd.DataFrame(scores_data)
    render_multi_line_chart(
        scores_df.tail(200),
        columns=list(scores_df.columns),
        title="模块评分趋势",
        y_label="评分",
    )
