"""算法参考页面 — 模型公式、数据流、诊断图表。"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.shared import (
    ROOT, load_model_results, load_fused_features, get_current_status,
    get_coupling_graph, ModuleScorer, PCAMonitor,
    render_kpi_card, render_diagnosis_card,
    ACCENT_BLUE, RISK_RED, HEALTH_GREEN, WARN_AMBER,
    TEXT_MAIN, TEXT_SECONDARY, TEXT_MUTED, BG_CONTENT, BORDER_MAIN,
    FONT_FAMILY, FONT_MONO,
    _get_base_layout,
)


def render_algorithm_reference_page() -> None:
    from src.visualization.model_formulas import MODEL_FORMULAS, render_formula_card_html
    from src.visualization.model_details_charts import (
        render_scree_plot, render_loading_plot, render_t2_spe_scatter,
        render_pca_2d_scatter, render_hi_waterfall, render_risk_waterfall,
        render_model_flow_sankey, render_correlation_heatmap,
        render_coupling_strength_matrix,
    )

    st.markdown("# 算法参考")
    st.caption("展示所有模型的数学公式、参数配置、数据流关系和内部诊断图表")

    df = load_model_results()
    fused_df = load_fused_features()
    status = get_current_status()
    graph = get_coupling_graph()
    module_scores = status.get("module_scores", {})

    # ── 模型概览 ──
    st.markdown("## 模型概览")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_kpi_card("PCA 监测", "已加载", status="normal")
    with m2:
        render_kpi_card("Isolation Forest", "已加载", status="normal")
    with m3:
        render_kpi_card("健康指数", "已启用", status="normal")
    with m4:
        render_kpi_card("风险融合", "已启用", status="normal")
    st.markdown("---")

    # ── 模型数据流 ──
    st.markdown("## 模型数据流")
    st.caption("从原始特征到诊断预警的完整数据处理链路")
    render_model_flow_sankey()
    st.markdown("---")

    # ── 模型详情 Tabs ──
    st.markdown("## 模型详情")
    tab_pca, tab_if, tab_hi, tab_risk, tab_mod = st.tabs(
        ["PCA 监测", "Isolation Forest", "健康指数", "风险融合", "模块级 PCA"]
    )

    # PCA Tab
    with tab_pca:
        st.markdown(render_formula_card_html("pca_monitor"), unsafe_allow_html=True)
        pca_path = ROOT / "outputs" / "models" / "pca_monitor.joblib"
        if pca_path.exists():
            import joblib
            pca_data = joblib.load(pca_path)
            pca_model = pca_data.get("pca")
            feature_names = pca_data.get("feature_names", [])
            t2_th = pca_data.get("t2_threshold", 0)
            spe_th = pca_data.get("spe_threshold", 0)

            if pca_model is not None:
                st.markdown("### PCA 内部诊断")
                d1, d2 = st.columns(2)
                with d1:
                    render_scree_plot(pca_model)
                with d2:
                    if feature_names:
                        render_loading_plot(pca_model, feature_names, top_n=15)

                if not df.empty and "pca_t2" in df.columns and "pca_spe" in df.columns:
                    is_anom = df["pca_anomaly_score"].values > 1.0 if "pca_anomaly_score" in df.columns else None
                    render_t2_spe_scatter(
                        df["pca_t2"].values, df["pca_spe"].values,
                        t2_th, spe_th,
                        is_anomaly=is_anom.astype(int) if is_anom is not None else None,
                    )

                if not fused_df.empty:
                    numeric_cols = fused_df.select_dtypes(include=[np.number]).columns.tolist()
                    if numeric_cols:
                        X = fused_df[numeric_cols].fillna(0).values
                        scaler = pca_data.get("scaler")
                        if scaler is not None:
                            X_scaled = scaler.transform(X)
                            scores_2d = pca_model.transform(X_scaled)[:, :2]
                            is_anom_2d = df["pca_anomaly_score"].values > 1.0 if "pca_anomaly_score" in df.columns and len(df) == len(scores_2d) else None
                            render_pca_2d_scatter(
                                scores_2d,
                                is_anomaly=is_anom_2d.astype(int) if is_anom_2d is not None else None,
                                explained_var=list(pca_model.explained_variance_ratio_[:2]),
                            )
        else:
            st.info("PCA 模型文件未找到。请先运行 `scripts/04_train_baseline_models.py` 训练模型。")

    # IF Tab
    with tab_if:
        st.markdown(render_formula_card_html("isolation_forest"), unsafe_allow_html=True)
        if not df.empty and "if_anomaly_score" in df.columns:
            st.markdown("### IF 异常分数分布")
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=df["if_anomaly_score"], nbinsx=50, marker_color=ACCENT_BLUE, opacity=0.7))
            fig.add_vline(x=0.7, line_dash="dash", line_color=RISK_RED, annotation_text="异常阈值 (0.7)", annotation_font_color=RISK_RED)
            layout = _get_base_layout("IF 异常分数分布", height=300, n_traces=1)
            layout["xaxis"]["title"] = "异常分数"
            layout["yaxis"]["title"] = "样本数"
            fig.update_layout(**layout)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # HI Tab
    with tab_hi:
        st.markdown(render_formula_card_html("health_index"), unsafe_allow_html=True)
        st.markdown("### 健康指数分解")
        if not df.empty:
            last = df.iloc[-1]
            pca_anom = float(last.get("pca_anomaly_score", 0))
            if_anom = float(last.get("if_anomaly_score", 0))
            mod_scores = {}
            for mod in ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]:
                cols = [c for c in df.columns if c.startswith(f"{mod}__")]
                if cols:
                    mod_scores[mod] = float(ModuleScorer.compute_module_score(df[cols].iloc[-1]))
            mod_mean = np.mean(list(mod_scores.values())) if mod_scores else 80.0
            hi_val = float(last.get("health_index", 0))
            cfg_weights = {"pca_score": 0.25, "isolation_forest_score": 0.25, "module_scores": 0.35, "event_penalty": 0.15}
            render_hi_waterfall(max(0, (1 - pca_anom)) * 100, max(0, (1 - if_anom)) * 100,
                               mod_mean, 100.0, cfg_weights, hi_val)

    # Risk Tab
    with tab_risk:
        st.markdown(render_formula_card_html("risk_fusion"), unsafe_allow_html=True)
        st.markdown("### 风险分数分解")
        if not df.empty:
            last = df.iloc[-1]
            rs_val = float(last.get("risk_score", 0))
            hi_val = float(last.get("health_index", 100))
            pca_anom = float(last.get("pca_anomaly_score", 0))
            if_anom = float(last.get("if_anomaly_score", 0))
            anomaly = max(pca_anom, if_anom)
            mw = {"execution_control": 0.15, "energy_input": 0.20, "environmental_constraint": 0.20, "state_maintenance": 0.45}
            weighted_health = sum(module_scores.get(m, 80) * w for m, w in mw.items()) / sum(mw.values())
            module_risk = 100 - weighted_health
            render_risk_waterfall(module_risk, anomaly, 100 - hi_val, 0.0, rs_val)

        st.markdown("### 模块权重配置")
        mw = {"执行控制": 0.15, "能量输入": 0.20, "环境约束": 0.20, "状态维持": 0.45}
        fig = go.Figure(go.Pie(
            labels=list(mw.keys()), values=list(mw.values()), hole=0.4,
            marker=dict(colors=[ACCENT_BLUE, HEALTH_GREEN, WARN_AMBER, RISK_RED]),
            textinfo="label+percent", textfont=dict(size=12, color=TEXT_MAIN),
        ))
        layout = _get_base_layout("模块风险权重分配", height=300, n_traces=1)
        fig.update_layout(**layout)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # Module PCA Tab
    with tab_mod:
        st.markdown(render_formula_card_html("module_level_pca"), unsafe_allow_html=True)
        st.markdown("### 四模块评分")
        if module_scores:
            mod_cn = {"execution_control": "执行控制", "energy_input": "能量输入",
                     "environmental_constraint": "环境约束", "state_maintenance": "状态维持"}
            mod_data = []
            for mod_id, score in sorted(module_scores.items(), key=lambda x: x[1]):
                mod_data.append({
                    "模块": mod_cn.get(mod_id, mod_id), "评分": f"{score:.1f}",
                    "状态": "健康" if score > 80 else ("亚健康" if score > 60 else ("异常" if score > 40 else "严重异常")),
                })
            st.dataframe(pd.DataFrame(mod_data), width="stretch", hide_index=True)

    st.markdown("---")

    # ── 耦合分析 ──
    st.markdown("## 耦合分析")
    c_corr, c_coup = st.columns(2)
    with c_corr:
        st.markdown("### 变量相关性矩阵")
        if not fused_df.empty:
            render_correlation_heatmap(fused_df, top_n=20)
        else:
            st.info("暂无融合特征数据")
    with c_coup:
        st.markdown("### 模块耦合强度")
        render_coupling_strength_matrix(module_scores, graph)

    st.markdown("---")

    # ── 阈值参考表 ──
    st.markdown("## 阈值与配置参考")
    from src.utils.config_loader import load_model_config
    cfg = load_model_config()
    threshold_rows = []
    pca_cfg = cfg.get("pca", {})
    threshold_rows = [
        {"模型": "PCA", "参数": "n_components", "当前值": str(pca_cfg.get("n_components", 0.95)), "说明": "方差保留比例"},
        {"模型": "PCA", "参数": "threshold_percentile", "当前值": str(pca_cfg.get("anomaly_threshold_percentile", 99)), "说明": "异常阈值百分位"},
    ]
    if_cfg = cfg.get("isolation_forest", {})
    threshold_rows += [
        {"模型": "IF", "参数": "n_estimators", "当前值": str(if_cfg.get("n_estimators", 200)), "说明": "隔离树数量"},
        {"模型": "IF", "参数": "contamination", "当前值": str(if_cfg.get("contamination", 0.05)), "说明": "预期异常比例"},
    ]
    hi_weights = cfg.get("health_index", {}).get("weights", {})
    for k, v in hi_weights.items():
        threshold_rows.append({"模型": "健康指数", "参数": f"weight.{k}", "当前值": str(v), "说明": "融合权重"})
    risk_thresh = cfg.get("risk_fusion", {}).get("risk_thresholds", {})
    for k, v in risk_thresh.items():
        threshold_rows.append({"模型": "风险融合", "参数": f"threshold.{k}", "当前值": str(v), "说明": "风险等级阈值"})
    st.dataframe(pd.DataFrame(threshold_rows), width="stretch", hide_index=True)
