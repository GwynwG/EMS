"""参数调优模拟器页面。

通过滑块调节模型权重和阈值，实时观察风险分数和健康指数的变化。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.shared import (
    ROOT, load_model_results, get_current_status,
    ACCENT_BLUE, RISK_RED, HEALTH_GREEN, WARN_AMBER,
    TEXT_MAIN, TEXT_SECONDARY, TEXT_MUTED, BG_CONTENT, BORDER_MAIN,
    FONT_FAMILY, _get_base_layout,
    render_kpi_card,
)


def render_simulator_page() -> None:
    st.markdown("# 参数调优模拟器")
    st.caption("调节模型权重和阈值，实时观察风险分数和健康指数的变化")

    df = load_model_results()
    status = get_current_status()

    if df.empty:
        st.warning("暂无数据")
        return

    last = df.iloc[-1]
    pca_anom = float(last.get("pca_anomaly_score", 0))
    if_anom = float(last.get("if_anomaly_score", 0))

    # 模块评分
    from src.domain_framework.module_scoring import ModuleScorer
    module_scores = {}
    for mod in ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]:
        cols = [c for c in df.columns if c.startswith(f"{mod}__")]
        if cols:
            module_scores[mod] = float(ModuleScorer.compute_module_score(df[cols].iloc[-1]))
        else:
            module_scores[mod] = 80.0

    # ═══ 健康指数权重调节 ═══
    st.markdown("## 健康指数权重调节")

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.markdown("### 权重配置")
        w_pca = st.slider("PCA 异常分数权重", 0.0, 0.5, 0.25, 0.05, key="w_pca")
        w_if = st.slider("IF 异常分数权重", 0.0, 0.5, 0.25, 0.05, key="w_if")
        w_mod = st.slider("模块健康均分权重", 0.0, 0.7, 0.35, 0.05, key="w_mod")
        w_evt = st.slider("事件惩罚权重", 0.0, 0.3, 0.15, 0.05, key="w_evt")

        # 权重归一化
        total_w = w_pca + w_if + w_mod + w_evt
        if total_w > 0:
            w_pca_n, w_if_n, w_mod_n, w_evt_n = w_pca/total_w, w_if/total_w, w_mod/total_w, w_evt/total_w
        else:
            w_pca_n = w_if_n = w_mod_n = w_evt_n = 0.25

        st.caption(f"归一化权重: PCA={w_pca_n:.2f}, IF={w_if_n:.2f}, 模块={w_mod_n:.2f}, 事件={w_evt_n:.2f}")

    with col_w2:
        st.markdown("### 实时计算结果")
        # 计算健康指数
        pca_health = max(0, 1 - pca_anom) * 100
        if_health = max(0, 1 - if_anom) * 100
        mod_health = np.mean(list(module_scores.values()))
        event_health = 100.0  # 默认无事件

        hi_new = (w_pca_n * pca_health + w_if_n * if_health +
                  w_mod_n * mod_health + w_evt_n * event_health)
        hi_new = np.clip(hi_new, 0, 100)

        hi_original = float(last.get("health_index", 100))
        delta = hi_new - hi_original

        hi_status = "normal" if hi_new > 80 else ("attention" if hi_new > 60 else ("warning" if hi_new > 40 else "severe"))
        render_kpi_card("模拟健康指数", f"{hi_new:.1f}", status=hi_status)
        st.metric("与当前值差异", f"{delta:+.1f}", delta=f"{delta:+.1f}")

        # 分项贡献
        st.markdown("**分项贡献:**")
        contrib_data = [
            {"分项": "PCA 异常分", "原始分": f"{pca_health:.1f}", "权重": f"{w_pca_n:.2f}", "贡献": f"{w_pca_n * pca_health:.1f}"},
            {"分项": "IF 异常分", "原始分": f"{if_health:.1f}", "权重": f"{w_if_n:.2f}", "贡献": f"{w_if_n * if_health:.1f}"},
            {"分项": "模块均分", "原始分": f"{mod_health:.1f}", "权重": f"{w_mod_n:.2f}", "贡献": f"{w_mod_n * mod_health:.1f}"},
            {"分项": "事件惩罚", "原始分": f"{event_health:.1f}", "权重": f"{w_evt_n:.2f}", "贡献": f"{w_evt_n * event_health:.1f}"},
        ]
        st.dataframe(pd.DataFrame(contrib_data), hide_index=True, width="stretch")

    st.markdown("---")

    # ═══ 风险阈值调节 ═══
    st.markdown("## 风险等级阈值调节")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("### 阈值配置")
        th_normal = st.slider("正常 → 关注", 0, 100, 30, 5, key="th_normal")
        th_attention = st.slider("关注 → 预警", 0, 100, 50, 5, key="th_attention")
        th_warning = st.slider("预警 → 严重", 0, 100, 70, 5, key="th_warning")
        th_severe = st.slider("严重阈值", 0, 100, 85, 5, key="th_severe")

    with col_t2:
        st.markdown("### 阈值影响分析")
        rs = float(last.get("risk_score", 0))

        # 当前等级
        if rs >= th_severe:
            level = "严重"
            color = RISK_RED
        elif rs >= th_warning:
            level = "预警"
            color = WARN_AMBER
        elif rs >= th_normal:
            level = "关注"
            color = WARN_AMBER
        else:
            level = "正常"
            color = HEALTH_GREEN

        st.markdown(f"**当前风险分数 {rs:.1f} → 等级: <span style='color:{color}'>{level}</span>**",
                   unsafe_allow_html=True)

        # 模拟全量数据的等级分布
        if "risk_score" in df.columns:
            scores = df["risk_score"]
            dist = {
                "正常": int(((scores < th_normal)).sum()),
                "关注": int(((scores >= th_normal) & (scores < th_attention)).sum()),
                "预警": int(((scores >= th_attention) & (scores < th_warning)).sum()),
                "严重": int((scores >= th_warning).sum()),
            }

            fig = go.Figure(go.Bar(
                x=list(dist.keys()),
                y=list(dist.values()),
                marker_color=[HEALTH_GREEN, WARN_AMBER, WARN_AMBER, RISK_RED],
                text=list(dist.values()),
                textposition="outside",
            ))
            layout = _get_base_layout("调整阈值后的等级分布", height=280, n_traces=1)
            layout["yaxis"]["title"] = "样本数"
            fig.update_layout(**layout)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown("---")

    # ═══ 模块权重调节 ═══
    st.markdown("## 模块风险权重调节")

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        mw_ec = st.slider("执行控制权重", 0.0, 0.5, 0.15, 0.05, key="mw_ec")
        mw_ei = st.slider("能量输入权重", 0.0, 0.5, 0.20, 0.05, key="mw_ei")
        mw_env = st.slider("环境约束权重", 0.0, 0.5, 0.20, 0.05, key="mw_env")
        mw_st = st.slider("状态维持权重", 0.0, 0.5, 0.45, 0.05, key="mw_st")

        total_mw = mw_ec + mw_ei + mw_env + mw_st
        if total_mw > 0:
            mw = {"execution_control": mw_ec/total_mw, "energy_input": mw_ei/total_mw,
                  "environmental_constraint": mw_env/total_mw, "state_maintenance": mw_st/total_mw}
        else:
            mw = {k: 0.25 for k in module_scores}

    with col_m2:
        # 模拟风险分数
        weighted_health = sum(module_scores.get(m, 80) * w for m, w in mw.items())
        module_risk = 100 - weighted_health
        anomaly = max(pca_anom, if_anom)
        hi_val = float(last.get("health_index", 100))
        risk_new = 0.5 * module_risk + 0.3 * anomaly + 0.2 * (100 - hi_val)
        risk_new = np.clip(risk_new, 0, 100)

        rs_original = float(last.get("risk_score", 0))
        risk_delta = risk_new - rs_original

        risk_status = "severe" if risk_new > 70 else ("warning" if risk_new > 50 else ("attention" if risk_new > 30 else "normal"))
        render_kpi_card("模拟风险分数", f"{risk_new:.1f}", status=risk_status)
        st.metric("与当前值差异", f"{risk_delta:+.1f}", delta=f"{risk_delta:+.1f}")

        # 模块贡献饼图
        mod_cn = {"execution_control": "执行控制", "energy_input": "能量输入",
                 "environmental_constraint": "环境约束", "state_maintenance": "状态维持"}
        fig = go.Figure(go.Pie(
            labels=[mod_cn.get(k, k) for k in mw.keys()],
            values=list(mw.values()),
            hole=0.4,
            marker=dict(colors=[ACCENT_BLUE, HEALTH_GREEN, WARN_AMBER, RISK_RED]),
            textinfo="label+percent",
            textfont=dict(size=11, color=TEXT_MAIN),
        ))
        layout = _get_base_layout("模拟模块权重分配", height=280, n_traces=1)
        fig.update_layout(**layout)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
