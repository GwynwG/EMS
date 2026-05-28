"""共享状态和工具函数。

所有页面模块从此模块导入共享资源，避免循环导入和重复代码。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.domain_framework.coupling_graph import CouplingGraph
from src.domain_framework.module_schema import ModuleType, get_module_meta
from src.domain_framework.module_scoring import ModuleScorer
from src.models.health_index import HealthIndexCalculator
from src.models.risk_fusion import RiskFusion
from src.online_monitoring.alarm_service import AlarmService
from src.utils.config_loader import load_app_config, load_alarm_rules
from src.utils.file_utils import load_csv
from src.visualization.four_module_graph import (
    render_four_module_graph_svg,
    get_module_detail,
    get_edge_detail,
)
from src.visualization.dashboard_components import (
    render_metric_card,
    render_risk_badge,
    render_module_score_bar,
    render_alarm_item,
    render_kpi_card,
    render_kpi_card_3layer,
    render_system_status_summary_blocks,
    render_relationship_status_table,
    render_contribution_variables_table,
    render_contribution_dataframe,
    render_diagnosis_card,
    render_threshold_panel,
    render_relation_summary,
    render_kv_panel,
    format_coupling_text,
    MODULE_ID_TO_CHINESE,
    MODULE_SHORT_CHINESE,
)
from src.visualization.plotly_charts import (
    render_single_line_chart,
    render_multi_line_chart,
    render_trend_tab_content,
    render_all_trend_groups,
    simplify_feature_name,
    render_gauge_chart,
    render_anomaly_timeline,
    render_degradation_trajectory,
    _get_base_layout,
)
from src.visualization.theme import (
    BG_MAIN, BG_SIDEBAR, BG_CONTENT, BG_CARD, BG_CARD_SOFT,
    BORDER_MAIN, BORDER_SOFT,
    TEXT_MAIN, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_BLUE, RISK_RED, HEALTH_GREEN, WARN_AMBER,
    STATUS_COLORS, FONT_FAMILY, FONT_MONO,
)


# ── 数据加载（带缓存）──
@st.cache_data
def load_model_results() -> pd.DataFrame:
    path = ROOT / "data" / "processed" / "model_results.csv"
    if path.exists():
        return load_csv(path, index_col=0, parse_dates=True)
    return pd.DataFrame()


@st.cache_data
def load_fused_features() -> pd.DataFrame:
    for name in ["fused_features_selected.csv", "fused_features.csv"]:
        path = ROOT / "data" / "processed" / name
        if path.exists():
            return load_csv(path, index_col=0, parse_dates=True)
    return pd.DataFrame()


@st.cache_resource
def get_coupling_graph():
    return CouplingGraph()


@st.cache_data(ttl=60)
def _compute_var_contribs(module_scores_tuple: tuple) -> list[dict]:
    return ModuleScorer.compute_variable_contributions(
        dict(module_scores_tuple), str(ROOT / "configs" / "variable_dictionary.yaml")
    )


@st.cache_data(ttl=60)
def _compute_edge_contribs(module_scores_tuple: tuple) -> list[dict]:
    graph = get_coupling_graph()
    return ModuleScorer.compute_edge_contributions(dict(module_scores_tuple), graph)


def get_current_status() -> dict:
    df = load_model_results()
    if df.empty:
        return {
            "risk_score": 0.0, "risk_level": "normal", "health_index": 100.0,
            "sample_count": 0, "main_abnormal_module": "state_maintenance",
            "main_abnormal_coupling": "state_maintenance ↔ execution_control",
            "module_scores": {
                "execution_control": 85.0, "energy_input": 82.0,
                "environmental_constraint": 88.0, "state_maintenance": 75.0,
            },
        }

    last = df.iloc[-1]
    module_scores = {}
    for mod in ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]:
        cols = [c for c in df.columns if c.startswith(f"{mod}__")]
        if cols:
            module_scores[mod] = float(ModuleScorer.compute_module_score(df[cols].iloc[-1]))
        else:
            module_scores[mod] = 80.0

    return {
        "risk_score": float(last.get("risk_score", 0)),
        "risk_level": str(last.get("risk_level", "normal")),
        "health_index": float(last.get("health_index", 100)),
        "sample_count": len(df),
        "main_abnormal_module": min(module_scores, key=module_scores.get),
        "main_abnormal_coupling": "state_maintenance ↔ execution_control",
        "module_scores": module_scores,
    }


# ── 导航配置 ──
PAGES = ["首页", "执行控制", "能量输入", "环境约束", "状态维持",
         "数据接入", "特征分析", "模型训练", "在线监测",
         "预警记录", "健康趋势", "算法参考"]

PANEL_BUTTONS = [
    {"id": "execution_control", "label": "执行控制", "type": "node"},
    {"id": "energy_input", "label": "能量输入", "type": "node"},
    {"id": "environmental_constraint", "label": "环境约束", "type": "node"},
    {"id": "state_maintenance", "label": "状态维持", "type": "node"},
    {"id": "diagnosis_layer", "label": "诊断层", "type": "node"},
    {"id": "coupling_residual", "label": "耦合残差", "type": "coupling"},
    {"id": "model_residual", "label": "模型残差", "type": "residual"},
    {"id": "intelligent_model", "label": "智能模型", "type": "intelligent_model"},
]

MODULE_IDS = {"execution_control", "energy_input", "environmental_constraint", "state_maintenance"}
