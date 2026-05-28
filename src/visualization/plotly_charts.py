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
    "#60A5FA",  # 冷蓝
    "#F87171",  # 红橙
    "#34D399",  # 青绿
    "#FBBF24",  # 琥珀
    "#A78BFA",  # 紫
    "#D7BA7D",  # 棕
    "#D1D5DB",  # 灰
    "#9CA3AF",  # 深灰
]

# 模块中文名映射
_MODULE_CN = {
    "execution_control": "执行控制",
    "energy_input": "能量输入",
    "environmental_constraint": "环境约束",
    "state_maintenance": "状态维持",
}

# ── 变量名中文映射（覆盖实际 CSV 中的变量名）──
_VAR_NAME_CN = {
    # 执行控制
    "control_mode": "控制模式",
    "setpoint_temperature": "温度设定值",
    "setpoint_pressure": "压力设定值",
    "valve_position_main": "主阀阀位",
    "valve_position_cooling": "冷却阀阀位",
    "interlock_status": "联锁状态",
    "actuator_feedback": "执行器反馈",
    "valve_position": "阀位",
    # 能量输入
    "supply_voltage": "供电电压",
    "supply_current": "供电电流",
    "active_power": "有功功率",
    "reactive_power": "无功功率",
    "power_factor": "功率因数",
    "energy_efficiency": "能量利用效率",
    "power_frequency": "电源频率",
    "voltage": "电压",
    "current": "电流",
    "power": "功率",
    # 环境约束
    "cooling_water_flow": "冷却水流量",
    "cooling_water_temp_in": "冷却水进水温度",
    "cooling_water_temp_out": "冷却水出水温度",
    "cooling_water_pressure": "冷却水压力",
    "vacuum_pressure": "真空度",
    "ambient_pressure": "环境气压",
    "ambient_humidity": "环境湿度",
    "cooling_water_temp": "冷却水温度",
    # 状态维持
    "furnace_temp_1": "炉温1区",
    "furnace_temp_2": "炉温2区",
    "furnace_temp_3": "炉温3区",
    "furnace_pressure": "炉内压力",
    "vibration_x": "X向振动",
    "vibration_y": "Y向振动",
    "temp_stability_index": "温度稳定性指标",
    "degradation_index": "退化指标",
    "vibration": "振动",
    "temperature": "温度",
    "pressure": "压力",
    # 模型输出
    "pca_anomaly_score": "PCA异常分数",
    "pca_t2": "T²统计量",
    "pca_spe": "SPE残差统计量",
    "if_anomaly_score": "IF异常分数",
    "health_index": "健康指数",
    "risk_score": "风险分数",
    "risk_level": "风险等级",
    # 通用
    "flow_rate": "流量",
    "humidity": "湿度",
    "speed": "转速",
    "frequency": "频率",
    "efficiency": "效率",
    "degradation_index": "退化指标",
    "stability_index": "稳定性指标",
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


# ════════════════════════════════════════════════════════════
# 趋势图组系统 — 按页面自动展开
# ════════════════════════════════════════════════════════════

def select_columns_by_keywords(df: pd.DataFrame, keywords: list[str]) -> list[str]:
    """从 df 列名中匹配包含关键词的列。"""
    matched = []
    for col in df.columns:
        col_lower = col.lower()
        for kw in keywords:
            if kw.lower() in col_lower:
                matched.append(col)
                break
    return matched


def get_page_trend_groups(page_name: str, module_name: str | None = None) -> list[dict]:
    """返回指定页面的趋势图组定义。"""
    if page_name == "首页":
        return [
            {"title": "综合风险分数趋势", "keywords": ["risk_score"], "desc": "系统总体异常风险变化"},
            {"title": "健康指数趋势", "keywords": ["health_index"], "desc": "设备综合健康状态"},
            {"title": "异常分数趋势", "keywords": ["pca_anomaly_score", "if_anomaly_score", "pca_t2", "pca_spe"], "desc": "PCA/IF 模型异常检测统计量"},
        ]
    if page_name == "执行控制":
        return [
            {"title": "设定值与控制指令趋势", "keywords": ["setpoint", "control_command"], "desc": "控制回路设定值与指令"},
            {"title": "控制模式趋势", "keywords": ["control_mode", "interlock"], "desc": "控制模式与联锁状态"},
            {"title": "执行器反馈趋势", "keywords": ["valve_position", "actuator", "feedback"], "desc": "执行器阀位与反馈信号"},
        ]
    if page_name == "能量输入":
        return [
            {"title": "电压电流趋势", "keywords": ["voltage", "current"], "desc": "供电电压与电流"},
            {"title": "功率与能量趋势", "keywords": ["active_power", "reactive_power", "power_factor", "energy_efficiency"], "desc": "有功/无功功率与能量效率"},
            {"title": "电源频率趋势", "keywords": ["power_frequency", "frequency"], "desc": "电源频率变化"},
        ]
    if page_name == "环境约束":
        return [
            {"title": "冷却条件趋势", "keywords": ["cooling_water"], "desc": "冷却水流量/温度/压力"},
            {"title": "压力与真空趋势", "keywords": ["vacuum_pressure", "ambient_pressure"], "desc": "环境压力与真空度"},
            {"title": "环境湿度趋势", "keywords": ["ambient_humidity", "humidity"], "desc": "环境湿度变化"},
        ]
    if page_name == "状态维持":
        return [
            {"title": "温度状态趋势", "keywords": ["furnace_temp", "temperature"], "desc": "炉温各区温度状态"},
            {"title": "压力状态趋势", "keywords": ["furnace_pressure", "pressure"], "desc": "炉内压力状态"},
            {"title": "振动状态趋势", "keywords": ["vibration"], "desc": "各方向振动状态"},
            {"title": "稳定性与退化趋势", "keywords": ["stability", "degradation"], "desc": "温度稳定性与退化指标"},
        ]
    if page_name == "特征分析" and module_name:
        return [
            {"title": "原始变量趋势", "category": "原始变量", "desc": "各变量原始值"},
            {"title": "统计特征趋势", "category": "统计特征", "desc": "均值/标准差/极差等"},
            {"title": "动态变化特征趋势", "category": "动态变化", "desc": "变化率/斜率/滞后项等"},
            {"title": "事件模式特征趋势", "category": "事件模式", "desc": "跳变/超限/模式切换等"},
            {"title": "异常健康特征趋势", "category": "异常健康", "desc": "异常分数/残差等"},
        ]
    if page_name == "模型训练":
        return [
            {"title": "PCA 统计量趋势", "keywords": ["pca_t2", "pca_spe", "pca_anomaly"], "desc": "PCA 模型 T² 和 SPE 统计量"},
            {"title": "Isolation Forest 异常分数趋势", "keywords": ["if_anomaly"], "desc": "IF 模型异常分数"},
            {"title": "健康指数与风险分数趋势", "keywords": ["health_index", "risk_score"], "desc": "综合评估结果"},
        ]
    if page_name == "在线监测":
        return [
            {"title": "实时风险分数趋势", "keywords": ["risk_score"], "desc": "实时综合风险"},
            {"title": "实时健康指数趋势", "keywords": ["health_index"], "desc": "实时健康状态"},
        ]
    if page_name == "预警记录":
        return [
            {"title": "风险等级趋势", "keywords": ["risk_score", "risk_level"], "desc": "风险分数与等级变化"},
            {"title": "异常分数趋势", "keywords": ["pca_anomaly_score", "if_anomaly_score"], "desc": "模型异常分数变化"},
        ]
    if page_name == "健康趋势":
        return [
            {"title": "健康指数趋势", "keywords": ["health_index"], "desc": "综合健康指数变化"},
            {"title": "退化指标趋势", "keywords": ["degradation"], "desc": "设备退化趋势"},
            {"title": "稳定性指标趋势", "keywords": ["stability"], "desc": "系统稳定性变化"},
        ]
    return []


def render_all_trend_groups(
    page_name: str,
    df: pd.DataFrame,
    module_name: str | None = None,
    tail_n: int = 200,
) -> None:
    """按页面类型自动渲染所有趋势图组，无需用户手动选择。"""
    groups = get_page_trend_groups(page_name, module_name)
    if not groups:
        return

    plot_df = df if tail_n == 0 else df.tail(tail_n)

    for group in groups:
        st.markdown(f"### {group['title']}")

        if "category" in group:
            # 特征分析页面：按分类匹配
            if module_name:
                module_cols = [c for c in plot_df.columns if c.startswith(f"{module_name}__")]
                categories = classify_feature_columns(module_cols, module_name)
                cols = categories.get(group["category"], [])
            else:
                cols = []
        else:
            cols = select_columns_by_keywords(plot_df, group["keywords"])

        if not cols:
            st.caption("当前数据中未找到相关变量")
            continue

        # 限制曲线数量
        cols = get_top_features_by_variance(plot_df, cols, top_k=8)

        # 构建中文名映射
        display_names = {c: simplify_feature_name(c, module_name or "") for c in cols}

        render_multi_line_chart(
            plot_df,
            columns=cols,
            title=group["title"],
            display_names=display_names,
        )

        if group.get("desc"):
            st.caption(group["desc"])
        if len(cols) >= 8:
            st.caption("仅展示前 8 个代表变量")


# ════════════════════════════════════════════════════════════
# 仪表盘 / 表盘
# ════════════════════════════════════════════════════════════

def render_gauge_chart(
    value: float,
    title: str,
    max_val: float = 100,
    height: int = 260,
) -> None:
    """渲染仪表盘/表盘图。0-30 绿色（健康），30-70 琥珀（关注），70-100 红色（风险）。"""
    from src.visualization.theme import HEALTH_GREEN, WARN_AMBER, RISK_RED

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(
            font=dict(size=36, color=TEXT_MAIN, family=FONT_FAMILY),
            valueformat=".1f",
        ),
        title=dict(
            text=title,
            font=dict(size=14, color=TEXT_SECONDARY, family=FONT_FAMILY),
        ),
        gauge=dict(
            axis=dict(range=[0, max_val], tickwidth=1, tickcolor=BORDER_MAIN,
                      tickfont=dict(size=11, color=TEXT_MUTED)),
            bar=dict(color=ACCENT_BLUE, thickness=0.3),
            bgcolor=BG_CONTENT,
            borderwidth=1, bordercolor=BORDER_MAIN,
            steps=[
                {"range": [0, 30], "color": f"rgba({_hex_to_rgb(HEALTH_GREEN)},0.15)"},
                {"range": [30, 70], "color": f"rgba({_hex_to_rgb(WARN_AMBER)},0.12)"},
                {"range": [70, 100], "color": f"rgba({_hex_to_rgb(RISK_RED)},0.12)"},
            ],
            threshold=dict(
                line=dict(color=RISK_RED, width=2),
                thickness=0.8,
                value=value,
            ),
        ),
    ))

    fig.update_layout(
        paper_bgcolor=BG_CONTENT,
        plot_bgcolor=BG_CONTENT,
        height=height,
        margin=dict(l=30, r=30, t=60, b=20),
        font=dict(family=FONT_FAMILY),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════
# 异常事件时间线
# ════════════════════════════════════════════════════════════

def render_anomaly_timeline(
    df: pd.DataFrame,
    height: int = 300,
) -> None:
    """异常事件时间线：标记 PCA/IF 异常发生时刻。"""
    if df.empty:
        st.info("暂无异常数据")
        return

    fig = go.Figure()
    x = list(range(len(df)))

    # PCA 异常
    if "pca_anomaly_score" in df.columns:
        pca_anom = df["pca_anomaly_score"] > 1.0
        if pca_anom.any():
            x_vals = [x[i] for i in range(len(df)) if pca_anom.iloc[i]]
            fig.add_trace(go.Scattergl(
                x=x_vals, y=[1] * len(x_vals),
                mode="markers",
                name="PCA 异常",
                marker=dict(color=RISK_RED, size=8, symbol="diamond",
                            line=dict(width=1, color="#fff")),
                hovertemplate="PCA 异常<br>样本 %{x}<extra></extra>",
            ))

    # IF 异常
    if "if_anomaly_score" in df.columns:
        if_anom = df["if_anomaly_score"] > 0.7
        if if_anom.any():
            x_vals = [x[i] for i in range(len(df)) if if_anom.iloc[i]]
            fig.add_trace(go.Scattergl(
                x=x_vals, y=[0.5] * len(x_vals),
                mode="markers",
                name="IF 异常",
                marker=dict(color=WARN_AMBER, size=7, symbol="triangle-up",
                            line=dict(width=1, color="#fff")),
                hovertemplate="IF 异常<br>样本 %{x}<extra></extra>",
            ))

    # 风险等级变化
    if "risk_level" in df.columns:
        level_colors = {"normal": ACCENT_BLUE, "attention": WARN_AMBER,
                        "warning": WARN_AMBER, "severe": RISK_RED}
        level_cn = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}
        for level, color in level_colors.items():
            mask = df["risk_level"] == level
            if mask.any():
                x_vals = [x[i] for i in range(len(df)) if mask.iloc[i]]
                fig.add_trace(go.Scattergl(
                    x=x_vals, y=[0] * len(x_vals),
                    mode="markers",
                    name=f"风险:{level_cn.get(level, level)}",
                    marker=dict(color=color, size=5, opacity=0.5),
                    hovertemplate=f"风险等级: {level_cn.get(level, level)}<br>样本 %{{x}}<extra></extra>",
                ))

    layout = _get_base_layout("异常事件时间线", height=height, n_traces=4)
    layout["yaxis"]["showticklabels"] = False
    layout["yaxis"]["range"] = [-0.2, 1.5]
    layout["yaxis"]["title"] = ""
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════
# 退化轨迹图
# ════════════════════════════════════════════════════════════

def render_degradation_trajectory(
    df: pd.DataFrame,
    col: str = "health_index",
    window: int = 50,
    height: int = 400,
) -> None:
    """退化轨迹图：滚动均值 + 置信带，按健康等级分段着色。"""
    if col not in df.columns:
        st.info(f"暂无 {col} 数据")
        return

    series = df[col].dropna()
    if len(series) < window:
        st.info(f"数据量不足（需要至少 {window} 个样本）")
        return

    # 使用位置索引作为 x 轴，避免重复值索引问题
    x = list(range(len(series)))
    rolling_mean = series.rolling(window=window, center=True).mean()
    rolling_std = series.rolling(window=window, center=True).std()
    upper = rolling_mean + 2 * rolling_std
    lower = rolling_mean - 2 * rolling_std

    fig = go.Figure()

    # 置信带
    fig.add_trace(go.Scatter(
        x=list(x) + list(x)[::-1],
        y=list(upper.values) + list(lower.values)[::-1],
        fill="toself",
        fillcolor=f"rgba({_hex_to_rgb(ACCENT_BLUE)},0.08)",
        line=dict(width=0),
        name="95% 置信带",
        hoverinfo="skip",
    ))

    # 滚动均值线
    fig.add_trace(go.Scattergl(
        x=x, y=rolling_mean.values,
        mode="lines",
        name=f"滚动均值 (w={window})",
        line=dict(color=ACCENT_BLUE, width=2.5),
    ))

    # 原始数据点（按健康等级着色）
    level_ranges = [
        (80, 100, HEALTH_GREEN, "健康"),
        (60, 80, WARN_AMBER, "亚健康"),
        (40, 60, "#FF8C00", "异常"),
        (0, 40, RISK_RED, "严重异常"),
    ]
    for lo, hi, color, label in level_ranges:
        mask = (series >= lo) & (series < hi)
        if mask.any():
            fig.add_trace(go.Scattergl(
                x=[xi for xi, m in zip(x, mask) if m],
                y=series[mask].values,
                mode="markers",
                name=label,
                marker=dict(color=color, size=3, opacity=0.5),
            ))

    # 阈值线
    for y_val, lbl, clr in [(80, "健康阈值", HEALTH_GREEN), (60, "亚健康阈值", WARN_AMBER),
                             (40, "异常阈值", "#FF8C00")]:
        fig.add_hline(y=y_val, line_dash="dot", line_color=clr, line_width=1,
                      annotation_text=lbl, annotation_font_color=clr, annotation_font_size=10)

    layout = _get_base_layout("健康退化轨迹", height=height, n_traces=6)
    layout["yaxis"]["title"] = "健康指数"
    layout["yaxis"]["range"] = [0, 105]
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
