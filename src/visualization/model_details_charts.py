"""模型详情页图表模块。

为"算法参考"页面提供 PCA 内部诊断、瀑布图、桑基图、热力图等 Plotly 图表。
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
    HEALTH_GREEN,
    WARN_AMBER,
    FONT_FAMILY,
    FONT_MONO,
)
from src.visualization.plotly_charts import _get_base_layout, _hex_to_rgb


# ════════════════════════════════════════════════════════════
# PCA 内部诊断图表
# ════════════════════════════════════════════════════════════

def _simplify_var_name(col_name: str) -> str:
    """将特征列名简化为中文显示名。"""
    from src.visualization.plotly_charts import simplify_feature_name, _MODULE_CN
    # 去掉模块前缀
    name = col_name
    module = ""
    for prefix in ["execution_control__", "energy_input__",
                   "environmental_constraint__", "state_maintenance__"]:
        if name.startswith(prefix):
            module = prefix.rstrip("__")
            name = name[len(prefix):]
            break
    return simplify_feature_name(col_name, module) if module else name


def render_scree_plot(pca_model) -> None:
    """PCA 碎石图：各主成分方差解释比 + 累积曲线。"""
    ev = pca_model.explained_variance_ratio_
    n = len(ev)
    x = [f"PC{i+1}" for i in range(n)]
    cum = np.cumsum(ev)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x, y=ev, name="单成分方差比",
        marker_color=ACCENT_BLUE, opacity=0.8,
    ))
    fig.add_trace(go.Scatter(
        x=x, y=cum, name="累积方差比",
        mode="lines+markers",
        line=dict(color=RISK_RED, width=2),
        marker=dict(size=6),
    ))
    fig.add_hline(y=0.95, line_dash="dash", line_color=WARN_AMBER,
                  annotation_text="95% 保留阈值", annotation_font_color=WARN_AMBER)

    layout = _get_base_layout("PCA 碎石图 — 特征值谱", height=420, n_traces=2)
    layout["yaxis"]["title"] = "方差解释比"
    layout["yaxis"]["range"] = [0, 1.05]
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_loading_plot(pca_model, feature_names: list[str], top_n: int = 12) -> None:
    """PCA 载荷热力图：特征与主成分的关系。"""
    components = pca_model.components_
    n_pcs = min(5, components.shape[0])

    # 选取载荷绝对值最大的 top_n 个特征
    max_loading = np.max(np.abs(components[:n_pcs]), axis=0)
    top_idx = np.argsort(max_loading)[::-1][:top_n]
    selected_names = [feature_names[i] for i in top_idx]
    selected_loadings = components[:n_pcs, top_idx]

    # 中文变量名
    cn_names = [_simplify_var_name(n) for n in selected_names]
    pc_labels = [f"PC{i+1}" for i in range(n_pcs)]

    fig = go.Figure(data=go.Heatmap(
        z=selected_loadings,
        x=cn_names,
        y=pc_labels,
        colorscale="RdBu_r",
        zmid=0,
        text=np.round(selected_loadings, 2),
        texttemplate="%{text}",
        textfont=dict(size=11, color=TEXT_MAIN),
        hovertemplate="特征: %{x}<br>主成分: %{y}<br>载荷: %{z:.3f}<extra></extra>",
    ))

    layout = _get_base_layout(f"PCA 载荷矩阵 — Top {top_n} 特征", height=400, n_traces=1)
    layout["xaxis"]["tickangle"] = -35
    layout["xaxis"]["tickfont"] = dict(size=11, color=TEXT_SECONDARY)
    layout["yaxis"]["tickfont"] = dict(size=12, color=TEXT_SECONDARY)
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_t2_spe_scatter(
    t2: np.ndarray,
    spe: np.ndarray,
    threshold_t2: float,
    threshold_spe: float,
    is_anomaly: np.ndarray | None = None,
) -> None:
    """T² vs SPE 散点图，标注阈值线和异常象限。"""
    colors = np.where(is_anomaly == 1, RISK_RED, ACCENT_BLUE) if is_anomaly is not None else ACCENT_BLUE

    fig = go.Figure()

    # 异常象限阴影
    fig.add_shape(type="rect", x0=threshold_spe, x1=max(spe.max() * 1.1, threshold_spe * 1.5),
                  y0=threshold_t2, y1=max(t2.max() * 1.1, threshold_t2 * 1.5),
                  fillcolor=f"rgba({_hex_to_rgb(RISK_RED)},0.06)", line_width=0)

    fig.add_trace(go.Scattergl(
        x=spe, y=t2, mode="markers",
        marker=dict(color=colors, size=4, opacity=0.6),
        name="样本",
        hovertemplate="SPE: %{x:.2f}<br>T²: %{y:.2f}<extra></extra>",
    ))

    # 阈值线
    fig.add_hline(y=threshold_t2, line_dash="dash", line_color=WARN_AMBER, line_width=1.5,
                  annotation_text=f"T²_th={threshold_t2:.1f}", annotation_font_color=WARN_AMBER)
    fig.add_vline(x=threshold_spe, line_dash="dash", line_color=WARN_AMBER, line_width=1.5,
                  annotation_text=f"SPE_th={threshold_spe:.1f}", annotation_font_color=WARN_AMBER)

    layout = _get_base_layout("T² vs SPE 联合监测图", height=480, n_traces=1)
    layout["xaxis"]["title"] = "SPE 统计量"
    layout["yaxis"]["title"] = "T² 统计量"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_pca_2d_scatter(
    scores: np.ndarray,
    is_anomaly: np.ndarray | None = None,
    explained_var: list[float] | None = None,
) -> None:
    """PC1 vs PC2 得分空间散点图。"""
    if scores.shape[1] < 2:
        st.info("PCA 成分数量不足 2，无法绘制二维散点图")
        return

    colors = np.where(is_anomaly == 1, RISK_RED, ACCENT_BLUE) if is_anomaly is not None else ACCENT_BLUE

    x_label = "PC1"
    y_label = "PC2"
    if explained_var and len(explained_var) >= 2:
        x_label = f"PC1 ({explained_var[0]*100:.1f}%)"
        y_label = f"PC2 ({explained_var[1]*100:.1f}%)"

    fig = go.Figure()
    fig.add_trace(go.Scattergl(
        x=scores[:, 0], y=scores[:, 1], mode="markers",
        marker=dict(color=colors, size=4, opacity=0.6),
        name="样本",
        hovertemplate=f"{x_label}: %{{x:.2f}}<br>{y_label}: %{{y:.2f}}<extra></extra>",
    ))

    layout = _get_base_layout("PCA 得分空间（PC1 vs PC2）", height=480, n_traces=1)
    layout["xaxis"]["title"] = x_label
    layout["yaxis"]["title"] = y_label
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════
# 瀑布图 — 健康指数 / 风险分数分解
# ════════════════════════════════════════════════════════════

def render_hi_waterfall(
    pca_health: float,
    if_health: float,
    mod_health: float,
    event_health: float,
    weights: dict[str, float],
    final_hi: float,
) -> None:
    """健康指数分解瀑布图。"""
    pca_contrib = weights.get("pca_score", 0.25) * pca_health
    if_contrib = weights.get("isolation_forest_score", 0.25) * if_health
    mod_contrib = weights.get("module_scores", 0.35) * mod_health
    event_contrib = weights.get("event_penalty", 0.15) * event_health

    measures = ["relative", "relative", "relative", "relative", "total"]
    x_labels = ["PCA 异常分", "IF 异常分", "模块均分", "事件惩罚", "健康指数"]
    y_vals = [pca_contrib, if_contrib, mod_contrib, event_contrib, final_hi]
    text_vals = [f"{v:.1f}" for v in y_vals]

    fig = go.Figure(go.Waterfall(
        x=x_labels, y=y_vals, measure=measures,
        textposition="outside", text=text_vals,
        connector=dict(line=dict(color=BORDER_MAIN)),
        increasing=dict(marker=dict(color=HEALTH_GREEN)),
        decreasing=dict(marker=dict(color=RISK_RED)),
        totals=dict(marker=dict(color=ACCENT_BLUE)),
    ))

    layout = _get_base_layout("健康指数分解瀑布图", height=360, n_traces=1)
    layout["yaxis"]["title"] = "贡献值"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_risk_waterfall(
    module_risk: float,
    anomaly_score: float,
    hi_deficit: float,
    event_penalty: float,
    final_risk: float,
) -> None:
    """风险分数分解瀑布图。"""
    measures = ["relative", "relative", "relative", "relative", "total"]
    x_labels = ["模块风险 (50%)", "异常分数 (30%)", "健康缺失 (20%)", "事件惩罚", "综合风险"]
    y_vals = [
        0.5 * module_risk,
        0.3 * anomaly_score,
        0.2 * hi_deficit,
        event_penalty * 10,
        final_risk,
    ]
    text_vals = [f"{v:.1f}" for v in y_vals]

    fig = go.Figure(go.Waterfall(
        x=x_labels, y=y_vals, measure=measures,
        textposition="outside", text=text_vals,
        connector=dict(line=dict(color=BORDER_MAIN)),
        increasing=dict(marker=dict(color=RISK_RED)),
        decreasing=dict(marker=dict(color=HEALTH_GREEN)),
        totals=dict(marker=dict(color=ACCENT_BLUE)),
    ))

    layout = _get_base_layout("风险分数分解瀑布图", height=360, n_traces=1)
    layout["yaxis"]["title"] = "贡献值"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════
# 桑基图 — 模型数据流
# ════════════════════════════════════════════════════════════

def render_model_flow_sankey() -> None:
    """模型数据流桑基图。"""
    from src.visualization.model_formulas import MODEL_FLOW_NODES, MODEL_FLOW_LINKS

    node_colors = [
        "#4B5563",  # 原始特征
        "#6B7280",  # 特征工程
        ACCENT_BLUE,  # PCA
        ACCENT_BLUE,  # IF
        ACCENT_BLUE,  # 模块 PCA
        "#6B7280",  # 事件特征
        HEALTH_GREEN,  # 健康指数
        WARN_AMBER,  # 风险融合
        RISK_RED,   # 诊断预警
    ]

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            pad=20, thickness=25, line=dict(color=BORDER_MAIN, width=1),
            label=MODEL_FLOW_NODES,
            color=node_colors,
        ),
        link=dict(
            source=[l[0] for l in MODEL_FLOW_LINKS],
            target=[l[1] for l in MODEL_FLOW_LINKS],
            value=[l[2] for l in MODEL_FLOW_LINKS],
            color=[f"rgba({_hex_to_rgb(l[3])},0.3)" for l in MODEL_FLOW_LINKS],
        ),
    ))

    layout = _get_base_layout("模型数据流全景图", height=400, n_traces=1)
    layout["font"]["size"] = 12
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ════════════════════════════════════════════════════════════
# 热力图 — 相关性矩阵 / 耦合强度矩阵
# ════════════════════════════════════════════════════════════

def render_correlation_heatmap(df: pd.DataFrame, top_n: int = 20) -> None:
    """变量相关性热力图（取方差最大的 top_n 个特征）。"""
    if df.empty:
        st.info("暂无特征数据")
        return

    # 选取方差最大的列
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # 排除模型输出列
    exclude = {"pca_anomaly_score", "pca_t2", "pca_spe", "if_anomaly_score",
               "health_index", "risk_score", "pls_anomaly_score",
               "root_cause_contribution"}
    numeric_cols = [c for c in numeric_cols if c not in exclude]
    if len(numeric_cols) > top_n:
        variances = df[numeric_cols].var()
        numeric_cols = list(variances.nlargest(top_n).index)

    corr = df[numeric_cols].corr()

    # 中文变量名
    short_names = [_simplify_var_name(c) for c in numeric_cols]

    fig = go.Figure(data=go.Heatmap(
        z=corr.values,
        x=short_names,
        y=short_names,
        colorscale="RdBu_r",
        zmid=0, zmin=-1, zmax=1,
        hovertemplate="%{x} vs %{y}: %{z:.3f}<extra></extra>",
    ))

    layout = _get_base_layout(f"变量相关性矩阵（Top {top_n}）", height=500, n_traces=1)
    layout["xaxis"]["tickangle"] = -45
    layout["xaxis"]["tickfont"] = dict(size=9, color=TEXT_SECONDARY)
    layout["yaxis"]["tickfont"] = dict(size=9, color=TEXT_SECONDARY)
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_root_cause_waterfall(root_cause_result: dict) -> None:
    """异常根因贡献度瀑布图 — Top-10 变量贡献。"""
    causes = root_cause_result.get("root_causes", [])
    if not causes:
        st.info("暂无根因数据")
        return

    # 取前 10 个
    causes = causes[:10]
    labels = [f"{c['variable']} ({c['module_cn']})" for c in causes]
    values = [c["contribution"] for c in causes]
    colors = [RISK_RED if v > 0 else ACCENT_BLUE for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors, opacity=0.85,
        text=[f"{v:.3f}" for v in values],
        textposition="outside",
        textfont=dict(size=11, color=TEXT_SECONDARY),
    ))

    layout = _get_base_layout("异常根因贡献度（Top-10 变量）", height=max(300, len(causes) * 35 + 80), n_traces=1)
    layout["xaxis"]["title"] = "贡献值（正=偏高，负=偏低）"
    layout["yaxis"]["autorange"] = "reversed"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_trend_prediction(
    series: pd.Series,
    predicted_values: list[float],
    confidence_band: list[tuple[float, float]],
    title: str = "趋势预测",
    threshold_high: float | None = None,
    threshold_low: float | None = None,
) -> None:
    """趋势预测图：历史数据 + 预测线 + 置信带。"""
    if series.empty or not predicted_values:
        st.info("暂无预测数据")
        return

    fig = go.Figure()
    n_hist = len(series)
    n_pred = len(predicted_values)

    # 历史数据
    x_hist = list(range(n_hist))
    fig.add_trace(go.Scattergl(
        x=x_hist, y=series.values,
        mode="lines", name="历史数据",
        line=dict(color=ACCENT_BLUE, width=2),
    ))

    # 预测线
    x_pred = list(range(n_hist - 1, n_hist + n_pred))
    y_pred = [series.iloc[-1]] + predicted_values
    fig.add_trace(go.Scattergl(
        x=x_pred, y=y_pred,
        mode="lines+markers", name="预测趋势",
        line=dict(color=WARN_AMBER, width=2, dash="dash"),
        marker=dict(size=4),
    ))

    # 置信带
    upper = [series.iloc[-1]] + [c[1] for c in confidence_band]
    lower = [series.iloc[-1]] + [c[0] for c in confidence_band]
    fig.add_trace(go.Scatter(
        x=x_pred + x_pred[::-1],
        y=upper + lower[::-1],
        fill="toself", fillcolor=f"rgba({_hex_to_rgb(WARN_AMBER)},0.1)",
        line=dict(width=0), name="95% 置信带",
        hoverinfo="skip",
    ))

    # 阈值线
    if threshold_high is not None:
        fig.add_hline(y=threshold_high, line_dash="dot", line_color=RISK_RED,
                      annotation_text=f"上限 {threshold_high}", annotation_font_color=RISK_RED)
    if threshold_low is not None:
        fig.add_hline(y=threshold_low, line_dash="dot", line_color=HEALTH_GREEN,
                      annotation_text=f"下限 {threshold_low}", annotation_font_color=HEALTH_GREEN)

    layout = _get_base_layout(title, height=350, n_traces=3)
    layout["xaxis"]["title"] = "样本序号"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_model_health_gauge(psi: float, ks: float, model_name: str) -> None:
    """模型健康度仪表盘 — 显示 PSI 和 KS 指标。"""
    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=psi,
        title=dict(text=f"{model_name} - PSI", font=dict(size=13, color=TEXT_SECONDARY)),
        number=dict(font=dict(size=20, color=TEXT_MAIN)),
        gauge=dict(
            axis=dict(range=[0, 0.5], tickfont=dict(size=10, color=TEXT_MUTED)),
            bar=dict(color=ACCENT_BLUE, thickness=0.3),
            bgcolor=BG_CONTENT,
            borderwidth=1, bordercolor=BORDER_MAIN,
            steps=[
                {"range": [0, 0.1], "color": f"rgba({_hex_to_rgb(HEALTH_GREEN)},0.2)"},
                {"range": [0.1, 0.25], "color": f"rgba({_hex_to_rgb(WARN_AMBER)},0.15)"},
                {"range": [0.25, 0.5], "color": f"rgba({_hex_to_rgb(RISK_RED)},0.15)"},
            ],
            threshold=dict(line=dict(color=RISK_RED, width=2), thickness=0.8, value=psi),
        ),
        domain=dict(row=0, column=0),
    ))

    layout = _get_base_layout(f"{model_name} 模型健康度", height=250, n_traces=1)
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_comparison_bars(
    results: list,
) -> None:
    """历史对比柱状图 — 两个时间段的指标对比。"""
    if not results:
        st.info("暂无对比数据")
        return

    metrics = [r.metric for r in results]
    means_a = [r.period_a.mean for r in results]
    means_b = [r.period_b.mean for r in results]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=metrics, y=means_a, name="时间段 A",
        marker_color=ACCENT_BLUE, opacity=0.7,
    ))
    fig.add_trace(go.Bar(
        x=metrics, y=means_b, name="时间段 B",
        marker_color=RISK_RED, opacity=0.7,
    ))

    layout = _get_base_layout("历史对比 — 均值比较", height=350, n_traces=2)
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "均值"
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_module_contribution_pie(module_contributions: dict[str, float]) -> None:
    """模块异常贡献饼图。"""
    if not module_contributions:
        st.info("暂无模块贡献数据")
        return

    from src.visualization.dashboard_components import MODULE_SHORT_CHINESE

    labels = [MODULE_SHORT_CHINESE.get(k, k) for k in module_contributions.keys()]
    values = list(module_contributions.values())
    colors = [ACCENT_BLUE, HEALTH_GREEN, WARN_AMBER, RISK_RED][:len(values)]

    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo="label+percent",
        textfont=dict(size=12, color=TEXT_MAIN),
    ))

    layout = _get_base_layout("模块异常贡献分布", height=300, n_traces=1)
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def render_coupling_strength_matrix(
    module_scores: dict[str, float],
    coupling_graph=None,
) -> None:
    """4×4 模块耦合强度矩阵热力图。"""
    from src.domain_framework.module_scoring import ModuleScorer
    from src.visualization.dashboard_components import MODULE_SHORT_CHINESE

    if coupling_graph is None:
        from src.domain_framework.coupling_graph import CouplingGraph
        coupling_graph = CouplingGraph()

    # 使用 compute_edge_contributions 获取耦合强度数据
    edge_data = ModuleScorer.compute_edge_contributions(module_scores, coupling_graph)

    modules = ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]
    mod_cn = [MODULE_SHORT_CHINESE.get(m, m) for m in modules]
    n = len(modules)

    # 构建 4×4 矩阵
    matrix = np.zeros((n, n))
    for ed in edge_data:
        eid = ed["id"]
        parts = eid.split("__")
        if len(parts) == 2 and parts[0] in modules and parts[1] in modules:
            i = modules.index(parts[0])
            j = modules.index(parts[1])
            matrix[i, j] = ed["coupling_strength"]

    # 对角线置为 1.0（自身耦合）
    np.fill_diagonal(matrix, 1.0)

    # 文本标注
    text = np.array([[f"{v:.2f}" if v > 0 else "-" for v in row] for row in matrix])

    fig = go.Figure(data=go.Heatmap(
        z=matrix, x=mod_cn, y=mod_cn,
        colorscale="YlOrRd", zmin=0, zmax=1,
        text=text, texttemplate="%{text}",
        textfont=dict(size=13, color=TEXT_MAIN),
        hovertemplate="%{y} → %{x}: %{z:.3f}<extra></extra>",
    ))

    layout = _get_base_layout("模块耦合强度矩阵", height=350, n_traces=1)
    layout["xaxis"]["tickfont"] = dict(size=12, color=TEXT_SECONDARY)
    layout["yaxis"]["tickfont"] = dict(size=12, color=TEXT_SECONDARY)
    fig.update_layout(**layout)
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
