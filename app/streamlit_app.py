"""面向生产场景的多元异构数据智能诊断系统 - Streamlit 主应用。"""
from __future__ import annotations

import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import json
from datetime import datetime
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
    BG_MAIN,
    BG_SIDEBAR,
    BG_CONTENT,
    BG_CARD,
    BG_CARD_SOFT,
    BORDER_MAIN,
    BORDER_SOFT,
    TEXT_MAIN,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_BLUE,
    RISK_RED,
    HEALTH_GREEN,
    WARN_AMBER,
    STATUS_COLORS,
    FONT_FAMILY,
    FONT_MONO,
)

# ── 页面配置 ──
st.set_page_config(
    page_title="多元异构数据智能诊断系统",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 全局深色工业监测驾驶舱主题 CSS ──
st.markdown(f"""
<style>
/* ── 全局背景 ── */
.stApp {{
    background: {BG_MAIN} !important;
    color: {TEXT_MAIN} !important;
}}
[data-testid="stAppViewContainer"] {{
    background: {BG_MAIN} !important;
}}
[data-testid="stHeader"] {{
    background: {BG_MAIN} !important;
}}

/* ── 侧边栏 ── */
[data-testid="stSidebar"] {{
    background: {BG_SIDEBAR} !important;
    border-right: 1px solid {BORDER_MAIN};
}}
[data-testid="stSidebar"] [data-testid="stMarkdown"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h3 {{
    color: {TEXT_MAIN} !important;
}}
[data-testid="stSidebar"] .stButton > button {{
    background: {BG_CARD} !important;
    color: {TEXT_SECONDARY} !important;
    border: 1px solid {BORDER_MAIN} !important;
    border-radius: 6px !important;
    margin-bottom: 2px;
    transition: all 0.2s ease;
    font-family: {FONT_FAMILY};
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: {BG_CARD_SOFT} !important;
    color: {TEXT_MAIN} !important;
    border-color: {BORDER_SOFT} !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {{
    background: {BG_CARD_SOFT} !important;
    color: {TEXT_MAIN} !important;
    border-color: {ACCENT_BLUE} !important;
    border-left: 3px solid {ACCENT_BLUE} !important;
}}

/* ── 主内容区标题 ── */
[data-testid="stMarkdownContainer"] h1 {{
    color: {TEXT_MAIN} !important;
    font-family: {FONT_FAMILY};
    font-weight: 700;
    letter-spacing: -0.01em;
}}
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{
    color: {TEXT_MAIN} !important;
    font-family: {FONT_FAMILY};
}}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {{
    color: {TEXT_SECONDARY} !important;
}}
[data-testid="stMarkdownContainer"] strong {{
    color: {TEXT_MAIN} !important;
}}

/* ── 分隔线 ── */
hr {{
    border-color: {BORDER_MAIN} !important;
    opacity: 0.6;
}}

/* ── 按钮通用 ── */
.stButton > button {{
    font-family: {FONT_FAMILY} !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {{
    background: {BG_CARD_SOFT} !important;
    color: {TEXT_MAIN} !important;
    border: 1px solid {ACCENT_BLUE} !important;
}}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="stBaseButton-secondary"] {{
    background: {BG_CARD} !important;
    color: {TEXT_SECONDARY} !important;
    border: 1px solid {BORDER_MAIN} !important;
}}
.stButton > button:hover {{
    background: {BG_CARD_SOFT} !important;
    border-color: {ACCENT_BLUE}88 !important;
    color: {TEXT_MAIN} !important;
}}

/* ── Selectbox / Input ── */
[data-testid="stSelectbox"] > div > div {{
    background: {BG_CARD} !important;
    border-color: {BORDER_MAIN} !important;
    color: {TEXT_MAIN} !important;
}}
[data-testid="stTextInput"] > div > div > input {{
    background: {BG_CARD} !important;
    border-color: {BORDER_MAIN} !important;
    color: {TEXT_MAIN} !important;
}}

/* ── DataFrame / Table ── */
[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER_MAIN};
    border-radius: 8px;
    overflow: hidden;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: {BG_CONTENT};
    border-radius: 12px;
    padding: 8px;
    gap: 8px;
    border: 1px solid {BORDER_MAIN};
}}
.stTabs [data-baseweb="tab"] {{
    background: {BG_CARD} !important;
    color: {TEXT_MUTED} !important;
    border-radius: 10px;
    font-family: {FONT_FAMILY};
    font-size: 17px !important;
    font-weight: 600 !important;
    padding: 12px 28px !important;
    min-height: 48px !important;
    border: 1px solid transparent;
    transition: all 0.2s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{
    background: {BG_CARD_SOFT} !important;
    color: {TEXT_SECONDARY} !important;
}}
.stTabs [aria-selected="true"] {{
    background: {BG_CARD_SOFT} !important;
    color: {TEXT_MAIN} !important;
    border: 1px solid {ACCENT_BLUE}55 !important;
    border-bottom: 3px solid {ACCENT_BLUE} !important;
    box-shadow: 0 2px 12px {ACCENT_BLUE}33;
}}
.stTabs [data-baseweb="tab-highlight"] {{
    background-color: transparent !important;
}}
.stTabs [data-baseweb="tab-border"] {{
    background-color: transparent !important;
}}

/* ── Metric ── */
[data-testid="stMetric"] {{
    background: {BG_CARD};
    border: 1px solid {BORDER_MAIN};
    border-radius: 10px;
    padding: 14px 18px;
}}
[data-testid="stMetricLabel"] {{
    color: {TEXT_SECONDARY} !important;
    font-family: {FONT_FAMILY} !important;
}}
[data-testid="stMetricValue"] {{
    color: {TEXT_MAIN} !important;
    font-family: {FONT_MONO} !important;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {BG_MAIN}; }}
::-webkit-scrollbar-thumb {{ background: {BORDER_MAIN}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: #4A5060; }}

/* ── 图表背景修正 ── */
.stPlotlyChart, .stPyplot {{
    background: {BG_CARD} !important;
    border-radius: 8px;
    padding: 8px;
}}
</style>
""", unsafe_allow_html=True)

# ── Session State 初始化 ──
if "current_page" not in st.session_state:
    st.session_state.current_page = "首页"
if "selected_object" not in st.session_state:
    st.session_state.selected_object = {"type": "node", "id": "state_maintenance"}
if "selected_panel_tab" not in st.session_state:
    st.session_state.selected_panel_tab = "state_maintenance"
if "selected_module" not in st.session_state:
    st.session_state.selected_module = "state_maintenance"
if "selected_relation" not in st.session_state:
    st.session_state.selected_relation = None
if "highlighted_relation_id" not in st.session_state:
    st.session_state.highlighted_relation_id = None
if "trend_metric_override" not in st.session_state:
    st.session_state.trend_metric_override = None

PAGES = ["首页", "执行控制", "能量输入", "环境约束", "状态维持", "数据接入", "特征分析", "模型训练", "在线监测", "预警记录", "健康趋势", "算法参考"]

# ── 按钮组配置 ──
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


# ── 统一状态管理 ──
# 节点 → 趋势指标映射
_NODE_TREND_METRIC = {
    "execution_control": "risk_score",
    "energy_input": "risk_score",
    "environmental_constraint": "risk_score",
    "state_maintenance": "health_index",
    "diagnosis_layer": "health_index",
    "coupling_residual": "pca_anomaly_score",
    "model_residual": "pca_anomaly_score",
    "intelligent_model": "if_anomaly_score",
}


def update_selected_object(sel_type: str, sel_id: str) -> None:
    """统一更新选中对象状态。"""
    st.session_state.selected_object = {"type": sel_type, "id": sel_id}

    # 更新趋势图指标
    st.session_state.trend_metric_override = _NODE_TREND_METRIC.get(sel_id)

    if sel_id in MODULE_IDS:
        st.session_state.selected_module = sel_id
        st.session_state.selected_panel_tab = sel_id
        st.session_state.selected_relation = None
        st.session_state.highlighted_relation_id = None
    elif sel_id == "diagnosis_layer":
        st.session_state.selected_panel_tab = "diagnosis_layer"
        st.session_state.selected_relation = None
        st.session_state.highlighted_relation_id = None
    elif sel_id == "coupling_residual":
        st.session_state.selected_panel_tab = "coupling_residual"
        st.session_state.selected_relation = "coupling_residual"
        st.session_state.highlighted_relation_id = None
    elif sel_id == "model_residual":
        st.session_state.selected_panel_tab = "model_residual"
        st.session_state.selected_relation = "model_residual"
        st.session_state.highlighted_relation_id = None
    elif sel_id == "intelligent_model":
        st.session_state.selected_panel_tab = "intelligent_model"
        st.session_state.selected_relation = "intelligent_model"
        st.session_state.highlighted_relation_id = None
    elif sel_type == "edge":
        st.session_state.selected_relation = sel_id
        st.session_state.highlighted_relation_id = sel_id
        if "coupling" in sel_id or "residual" in sel_id:
            st.session_state.selected_panel_tab = "coupling_residual"
        elif "intelligent" in sel_id:
            st.session_state.selected_panel_tab = "intelligent_model"


# ── 加载数据 ──
@st.cache_data
def load_model_results() -> pd.DataFrame:
    """加载模型结果数据。"""
    path = ROOT / "data" / "processed" / "model_results.csv"
    if path.exists():
        return load_csv(path, index_col=0, parse_dates=True)
    return pd.DataFrame()


@st.cache_data
def load_fused_features() -> pd.DataFrame:
    """加载融合特征。"""
    for name in ["fused_features_selected.csv", "fused_features.csv"]:
        path = ROOT / "data" / "processed" / name
        if path.exists():
            return load_csv(path, index_col=0, parse_dates=True)
    return pd.DataFrame()


@st.cache_resource
def get_coupling_graph():
    """缓存 CouplingGraph 实例（跨会话共享）。"""
    return CouplingGraph()


@st.cache_data(ttl=60)
def _compute_var_contribs(module_scores_tuple: tuple) -> list[dict]:
    """缓存变量贡献计算结果。"""
    return ModuleScorer.compute_variable_contributions(
        dict(module_scores_tuple), str(ROOT / "configs" / "variable_dictionary.yaml")
    )


@st.cache_data(ttl=60)
def _compute_edge_contribs(module_scores_tuple: tuple) -> list[dict]:
    """缓存耦合边贡献计算结果。"""
    graph = get_coupling_graph()
    return ModuleScorer.compute_edge_contributions(dict(module_scores_tuple), graph)


@st.cache_data(ttl=60)
def get_current_status() -> dict:
    """获取当前系统状态（从模型结果中取最新值）。"""
    df = load_model_results()
    if df.empty:
        return {
            "risk_score": 0.0,
            "risk_level": "normal",
            "health_index": 100.0,
            "sample_count": 0,
            "main_abnormal_module": "state_maintenance",
            "main_abnormal_coupling": "state_maintenance ↔ execution_control",
            "module_scores": {
                "execution_control": 85.0,
                "energy_input": 82.0,
                "environmental_constraint": 88.0,
                "state_maintenance": 75.0,
            },
        }

    last = df.iloc[-1]
    module_scores = {}
    for mod in ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]:
        cols = [c for c in df.columns if c.startswith(f"{mod}__")]
        if cols:
            vals = df[cols].iloc[-1]
            score = ModuleScorer.compute_module_score(vals)
            module_scores[mod] = score
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


# ── 详情面板渲染函数 ──
def render_node_detail(node_id: str, status: dict, graph: CouplingGraph) -> None:
    """渲染节点详情（增强版：模块信息 + 变量状态 + 模型信息）。"""
    detail = get_module_detail(node_id, status["module_scores"])

    # 模块说明
    st.markdown(f"**{detail.get('name', node_id)}**")
    st.caption(detail.get("description", ""))
    if "score" in detail:
        score = detail["score"]
        color = "#FF6B6B" if score < 40 else "#4FC1FF"
        st.markdown(f"**模块评分:** <span style='color:{color}; font-size:20px; font-weight:700;'>{score:.1f}</span>", unsafe_allow_html=True)
    if "risk_level" in detail:
        st.markdown(render_risk_badge(detail["risk_level"]), unsafe_allow_html=True)

    # 关键变量状态
    variables = detail.get("variables", [])
    if variables:
        st.markdown("**关键变量状态:**")
        # 加载变量字典获取中文名和单位
        var_dict_path = ROOT / "configs" / "variable_dictionary.yaml"
        var_info = {}
        if var_dict_path.exists():
            import yaml
            with open(var_dict_path, "r", encoding="utf-8") as f:
                vdata = yaml.safe_load(f)
            for v in vdata.get("variables", []):
                var_info[v["standard_name"]] = v

        for v in variables[:5]:
            vi = var_info.get(v, {})
            cn = vi.get("chinese_name", v)
            unit = vi.get("unit", "")
            st.markdown(f"- {cn} ({unit})")

    # 对应模型
    model_map = {
        "execution_control": "PCA 控制偏差监测 / 规则引擎",
        "energy_input": "PCA 能量异常监测 / PLS 能效建模",
        "environmental_constraint": "PCA 环境偏差监测 / IF 异常检测",
        "state_maintenance": "PCA 状态监测 / IF 异常检测 / HI 健康评估",
        "diagnosis_layer": "风险融合引擎 / 预警规则",
        "coupling_residual": "多源残差聚合",
        "model_residual": "PCA-SPE / T² 统计量",
        "intelligent_model": "XGBoost / Autoencoder",
    }
    st.markdown(f"**关联模型:** {model_map.get(node_id, '综合模型')}")

    # 跳转按钮
    module_pages = {
        "execution_control": "执行控制",
        "energy_input": "能量输入",
        "environmental_constraint": "环境约束",
        "state_maintenance": "状态维持",
    }
    target_page = module_pages.get(node_id)
    if target_page:
        if st.button(f"进入 {target_page} 配置", key="goto_module_config"):
            st.session_state.current_page = target_page
            st.rerun()


def render_edge_detail(edge_id: str, graph: CouplingGraph) -> None:
    """渲染边详情（增强版）。"""
    parts = edge_id.split("__")
    if len(parts) == 2:
        edge_detail = get_edge_detail(parts[0], parts[1], graph)
        st.markdown(f"**{edge_detail.get('name', '')}**")
        src_cn = MODULE_SHORT_CHINESE.get(edge_detail.get("source", ""), edge_detail.get("source", ""))
        tgt_cn = MODULE_SHORT_CHINESE.get(edge_detail.get("target", ""), edge_detail.get("target", ""))
        st.markdown(f"**起点:** {src_cn}")
        st.markdown(f"**终点:** {tgt_cn}")

        cs = edge_detail.get("coupling_strength", 0)
        rl = edge_detail.get("residual_level", 0)
        st.markdown(f"**耦合强度:** {cs:.2f}")
        st.progress(min(1.0, cs))
        st.markdown(f"**残差水平:** {rl:.2f}")
        st.progress(min(1.0, rl))

        edge_type = edge_detail.get("edge_type", "")
        type_labels = {"main": "主关系", "feedback": "反馈关系", "auxiliary": "辅助关系"}
        st.markdown(f"**关系类型:** {type_labels.get(edge_type, edge_type)}")

        if edge_detail.get("description"):
            st.caption(edge_detail["description"])
    else:
        st.warning("无法解析边信息")


def render_coupling_detail(coupling_id: str) -> None:
    """渲染耦合残差详情（增强版）。"""
    st.markdown("**复杂耦合/残差**")
    st.caption("多源耦合残差处理模块，整合各模块间的耦合效应残差。")

    st.markdown("**涉及模块:**")
    st.markdown("- 执行控制模块")
    st.markdown("- 能量输入模块")
    st.markdown("- 环境约束模块")

    st.markdown("**耦合关系:**")
    st.markdown("- 执行控制 → 耦合残差")
    st.markdown("- 能量输入 → 耦合残差")
    st.markdown("- 环境约束 → 耦合残差")

    st.markdown("**当前残差水平:** 0.35")
    st.progress(0.35)

    st.markdown("**智能补偿状态:** 待训练")
    st.markdown("**主要贡献变量:** 工艺温度、输入功率、冷却水流量")


def render_residual_detail(residual_id: str) -> None:
    """渲染模型残差详情（增强版）。"""
    st.markdown("**模型残差**")
    st.caption("基础统计模型（PCA/PLS）输出的残差，用于残差监测和异常检测。")

    st.markdown("**机理/统计模型输出:**")
    st.markdown("- PCA T² 统计量: 2.35")
    st.markdown("- PCA SPE 统计量: 0.82")
    st.markdown("- Isolation Forest 异常分数: 0.15")

    st.markdown("**残差水平:** 0.42")
    st.progress(0.42)

    st.markdown("**预警阈值:** SPE > 1.0 触发预警")
    st.markdown("**当前状态:** <span style='color:#4FC1FF;'>正常</span>", unsafe_allow_html=True)

    st.markdown("**输出:** 残差特征 → 智能补偿模型")


def render_intelligent_model_detail() -> None:
    """渲染智能补偿模型详情（增强版）。"""
    st.markdown("**智能补偿模型**")
    st.caption("基于 XGBoost / Autoencoder 的智能异常补偿。")

    st.markdown("**模型类型:** XGBoost 回归 + Autoencoder 重构")
    st.markdown("**输入特征:** 四模块融合特征 + 耦合残差 + 模型残差")
    st.markdown("**输出异常分数:** 0.18")
    st.progress(0.18)

    st.markdown("**模型状态:** <span style='color:#6B7280;'>待训练</span>", unsafe_allow_html=True)
    st.markdown("**最近训练时间:** --")
    st.markdown("**模型说明:** 用于捕获模块间复杂非线性耦合关系，补偿基础统计模型的不足。")


def render_selected_object_detail(status: dict, graph: CouplingGraph) -> None:
    """根据 selected_object 动态渲染详情面板。"""
    selected = st.session_state.selected_object
    obj_type = selected.get("type", "node")
    obj_id = selected.get("id", "state_maintenance")

    if obj_type == "node":
        render_node_detail(obj_id, status, graph)
    elif obj_type == "edge":
        render_edge_detail(selected.get("id", ""), graph)
    elif obj_type == "coupling":
        render_coupling_detail(obj_id)
    elif obj_type == "residual":
        render_residual_detail(obj_id)
    elif obj_type == "intelligent_model":
        render_intelligent_model_detail()
    else:
        st.info(f"未知对象类型: {obj_type}")


# ── 侧边栏导航 ──
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 8px 0 16px 0;">
        <div style="font-size: 11px; color: #858585; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px; font-family: {FONT_FAMILY};">SYSTEM</div>
        <div style="font-size: 18px; font-weight: 600; color: #D4D4D4; font-family: {FONT_FAMILY};">智能诊断系统</div>
        <div style="font-size: 11px; color: #858585; margin-top: 2px; font-family: {FONT_MONO};">MULTI-SOURCE DIAGNOSTICS</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    for page in PAGES:
        is_active = (page == st.session_state.current_page)
        btn_type = "primary" if is_active else "secondary"
        if st.sidebar.button(page, key=f"nav_btn_{page}", type=btn_type, width="stretch"):
            if not is_active:
                st.session_state.current_page = page
                st.rerun()
    st.markdown("---")
    st.caption("v1.0.0 | 四模块领域模型")


# ════════════════════════════════════════════════════════════
# 首页 - 多源异构数据智能诊断驾驶舱
# ════════════════════════════════════════════════════════════
def render_home_page() -> None:
    from src.domain_framework.module_scoring import ModuleScorer

    status = get_current_status()
    df = load_model_results()
    fused_df = load_fused_features()
    graph = get_coupling_graph()
    module_scores = status.get("module_scores", {})

    # ── Section 1: 页面标题区 ──
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"""
    <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
            <div style="font-size: 12px; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.1em; font-family: {FONT_MONO}; margin-bottom: 4px;">
                MULTI-SOURCE DIAGNOSTICS COCKPIT
            </div>
            <div style="font-size: 30px; font-weight: 700; color: {TEXT_MAIN}; font-family: {FONT_FAMILY}; letter-spacing: -0.01em;">
                面向生产场景的多元异构数据智能诊断系统
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 12px; color: {TEXT_MUTED}; font-family: {FONT_MONO};">运行模式: Mock DCS 模拟</div>
            <div style="font-size: 12px; color: {TEXT_SECONDARY}; font-family: {FONT_MONO};">{now_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Section 2: KPI 总览区（3行布局）──
    risk_status = status["risk_level"]
    hi = status["health_index"]
    hi_status = "normal" if hi > 80 else ("attention" if hi > 60 else ("warning" if hi > 40 else "severe"))
    rs = status["risk_score"]
    rs_status = "severe" if rs > 70 else ("warning" if rs > 50 else ("attention" if rs > 30 else "normal"))
    abnormal_module_cn = MODULE_ID_TO_CHINESE.get(status["main_abnormal_module"], status["main_abnormal_module"])
    abnormal_coupling_cn = format_coupling_text(status["main_abnormal_coupling"])
    level_labels = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}

    # Row 1: 核心指标（3列）
    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card_3layer("综合风险分数", f"{rs:.1f}", "基于四模块加权融合", rs_status)
    with c2:
        render_kpi_card_3layer("当前预警等级", level_labels.get(risk_status, risk_status), "综合风险与事件规则判定", risk_status)
    with c3:
        render_kpi_card_3layer("健康指数", f"{hi:.1f}", "综合健康评估指标", hi_status)

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # Row 2: 来源分析（3列）
    var_contribs = _compute_var_contribs(tuple(sorted(module_scores.items())))
    top_var_cn = var_contribs[0]["chinese_name"] if var_contribs else "无"
    top_var_module = MODULE_SHORT_CHINESE.get(var_contribs[0]["module"], "") if var_contribs else ""
    model_status_text = "PCA/IF/HI 已加载"

    c4, c5, c6 = st.columns(3)
    with c4:
        render_kpi_card_3layer("主异常模块", abnormal_module_cn, "评分最低的核心模块", "warning")
    with c5:
        render_kpi_card_3layer("主异常耦合关系", abnormal_coupling_cn, "残差最大的模块关系", "attention")
    with c6:
        render_kpi_card_3layer("主要贡献变量", top_var_cn, f"所属: {top_var_module}", "attention")

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # Row 3: 状态信息（2列）
    c7, c8 = st.columns(2)
    with c7:
        render_kpi_card_3layer("在线样本数", str(status["sample_count"]), "累计监测数据样本", "normal")
    with c8:
        render_kpi_card_3layer("当前模型状态", model_status_text, "PCA/IF/HI 模型运行状态", "normal")

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # Row 4: 仪表盘图
    g1, g2 = st.columns(2)
    with g1:
        render_gauge_chart(rs, "综合风险分数")
    with g2:
        render_gauge_chart(hi, "健康指数")

    st.markdown("---")

    # ── Section 3: 系统状态摘要区 ──
    summary_data = ModuleScorer.compute_system_status_summary(status, df)
    render_system_status_summary_blocks(summary_data)

    st.markdown("---")

    # ── Section 3.5: 诊断结论 + 模块评分表 ──
    # 诊断结论
    risk_desc = "正常" if rs < 30 else ("关注" if rs < 50 else ("预警" if rs < 70 else "严重"))
    recommended = summary_data.get("recommended_focus", {}).get("module", "状态维持")
    recommended_cn = MODULE_SHORT_CHINESE.get(recommended, recommended)
    render_diagnosis_card(
        conclusion=f"当前系统总体状态为「{risk_desc}」，综合风险分数 {rs:.1f}，健康指数 {hi:.1f}。",
        risk_source=abnormal_module_cn,
        key_vars=top_var_cn,
        suggestion=f"建议重点关注{recommended_cn}模块及相关变量变化趋势。",
        status=risk_status,
    )

    # 四模块评分表
    st.markdown("#### 四模块评分概览")
    mod_score_data = []
    for mod_id, mod_score in module_scores.items():
        mod_risk = ModuleScorer.determine_risk_level(100 - mod_score)
        mod_vars = [v for v in var_contribs if v.get("module") == mod_id]
        mod_top_var = mod_vars[0]["chinese_name"] if mod_vars else "—"
        mod_score_data.append({
            "模块": MODULE_SHORT_CHINESE.get(mod_id, mod_id),
            "评分": f"{mod_score:.1f}",
            "风险等级": level_labels.get(mod_risk, mod_risk),
            "主要异常变量": mod_top_var,
        })
    st.dataframe(pd.DataFrame(mod_score_data), width="stretch", hide_index=True)

    st.markdown("---")

    # ── Section 4: 四模块领域模型关系图 ──
    st.markdown("### 四模块状态监测关系图")
    st.caption("面向生产场景的多元异构数据智能诊断系统的模块关系与诊断链路")
    sel_obj = st.session_state.selected_object
    selected_id = sel_obj.get("id", "state_maintenance")

    # 计算耦合矩阵用于拓扑图标注
    _coupling_mat = None
    if not fused_df.empty:
        _coupling_mat = graph.compute_coupling_matrix(fused_df)

    render_four_module_graph_svg(selected_id, module_scores, coupling_matrix=_coupling_mat)

    # ── Section 5: 选择监测对象按钮组 ──
    st.markdown(f"""
    <div style="margin: 12px 0 8px 0;">
        <span style="font-size: 12px; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.08em; font-family: {FONT_FAMILY};">选择监测对象</span>
    </div>
    """, unsafe_allow_html=True)
    btn_cols = st.columns(4)
    current_tab = st.session_state.selected_panel_tab

    for i, btn_cfg in enumerate(PANEL_BUTTONS):
        with btn_cols[i % 4]:
            btn_id = btn_cfg["id"]
            btn_label = btn_cfg["label"]
            is_selected = (btn_id == current_tab)
            btn_type = "primary" if is_selected else "secondary"
            if st.button(btn_label, key=f"panel_btn_{btn_id}", type=btn_type, width="stretch"):
                if not is_selected:
                    update_selected_object(btn_cfg["type"], btn_id)
                    st.rerun()

    st.markdown("---")

    # ── Section 6: 选中对象详情区 ──
    st.markdown(f"""
    <div style="margin-bottom: 12px;">
        <span style="font-size: 12px; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.08em; font-family: {FONT_MONO};">Detail</span>
        <div style="font-size: 16px; color: {TEXT_MAIN}; font-weight: 600; margin-top: 2px; font-family: {FONT_FAMILY};">选中对象详情</div>
    </div>
    """, unsafe_allow_html=True)
    render_selected_object_detail(status, graph)

    st.markdown("---")

    # ── Section 7: 模块间耦合关系状态表 ──
    st.markdown(f"""
    <div style="margin-bottom: 12px;">
        <span style="font-size: 12px; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.08em; font-family: {FONT_MONO};">Relations</span>
        <div style="font-size: 16px; color: {TEXT_MAIN}; font-weight: 600; margin-top: 2px; font-family: {FONT_FAMILY};">模块间耦合关系状态</div>
    </div>
    """, unsafe_allow_html=True)
    edges_data = _compute_edge_contribs(tuple(sorted(module_scores.items())))
    highlighted_relation = st.session_state.highlighted_relation_id or ""
    render_relationship_status_table(edges_data, highlighted_relation)

    st.markdown("---")

    # ── Section 8: 趋势监测 / 贡献变量 / 预警记录 ──
    st.markdown(f"""
    <div style="margin-bottom: 12px;">
        <span style="font-size: 12px; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.08em; font-family: {FONT_MONO};">Analysis</span>
        <div style="font-size: 16px; color: {TEXT_MAIN}; font-weight: 600; margin-top: 2px; font-family: {FONT_FAMILY};">数据分析</div>
    </div>
    """, unsafe_allow_html=True)

    tab_trend, tab_contrib, tab_alarm = st.tabs(["趋势监测", "贡献变量", "预警记录"])

    with tab_trend:
        if not df.empty:
            render_trend_tab_content(df)
        else:
            st.info("暂无模型结果数据，请先运行训练脚本")

    with tab_contrib:
        selected_module = st.session_state.selected_module or ""
        render_contribution_dataframe(var_contribs, selected_module)

    with tab_alarm:
        if not df.empty:
            if "risk_level" in df.columns:
                alarm_df = df[df["risk_level"].isin(["warning", "severe"])]
                if not alarm_df.empty:
                    st.info(f"共 {len(alarm_df)} 条预警记录")
                    display_cols = [c for c in ["risk_score", "risk_level", "health_index", "pca_anomaly_score"] if c in alarm_df.columns]
                    st.dataframe(alarm_df[display_cols].tail(50), width="stretch", hide_index=True)
                else:
                    st.success("暂无预警记录，设备状态正常。")
            else:
                st.info("暂无预警数据")
        else:
            st.info("暂无预警数据")


# ════════════════════════════════════════════════════════════
# 模块页面
# ════════════════════════════════════════════════════════════
def render_module_page(module_type: ModuleType) -> None:
    meta = get_module_meta(module_type)
    status = get_current_status()
    score = status["module_scores"].get(module_type.value, 100.0)
    level_labels = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}

    st.markdown(f"# {meta.chinese_name}")
    st.markdown(f"*{meta.description}*")

    # ═══ 板块 1: 模块总览区 ═══
    st.markdown("## 模块总览")
    risk_level = ModuleScorer.determine_risk_level(100 - score)

    # 找主要异常变量
    var_contribs = _compute_var_contribs(tuple(sorted(status.get("module_scores", {}).items())))
    module_vars = [v for v in var_contribs if v.get("module") == module_type.value]
    top_var = module_vars[0]["chinese_name"] if module_vars else "无"
    top_var_status = module_vars[0].get("status", "正常") if module_vars else "正常"

    # 找主要关联模块
    graph = get_coupling_graph()
    edge_contribs = _compute_edge_contribs(tuple(sorted(status.get("module_scores", {}).items())))
    related_edges = [e for e in edge_contribs if module_type.value in e.get("source", "") or module_type.value in e.get("target", "")]
    related_module = ""
    if related_edges:
        e = related_edges[0]
        src = e.get("source", "")
        tgt = e.get("target", "")
        other = tgt if src == module_type.value else src
        related_module = MODULE_SHORT_CHINESE.get(other, other)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("模块评分", f"{score:.1f}", status="normal" if score > 80 else ("attention" if score > 60 else "warning"))
    with c2:
        render_kpi_card("风险等级", level_labels.get(risk_level, risk_level), status=risk_level)
    with c3:
        render_kpi_card("主要异常变量", top_var, subtext=top_var_status, status="attention")
    with c4:
        render_kpi_card("主要关联模块", related_module or "无", subtext="耦合关系最强", status="normal")

    st.markdown("<div style='height: 16px'></div>", unsafe_allow_html=True)

    # 诊断结论卡
    score_desc = "健康" if score > 80 else ("亚健康" if score > 60 else ("异常" if score > 40 else "严重异常"))
    render_diagnosis_card(
        conclusion=f"{meta.chinese_name}当前状态为「{score_desc}」，模块评分 {score:.1f}，风险等级 {level_labels.get(risk_level, risk_level)}。",
        risk_source=top_var,
        key_vars=", ".join([v.get("chinese_name", "") for v in module_vars[:3]]) if module_vars else "无",
        suggestion=f"关注{top_var}变化趋势及{related_module or '关联模块'}耦合状态。",
        status=risk_level,
    )

    st.markdown("---")

    # ═══ 板块 2: 核心变量趋势区 ═══
    st.markdown("## 核心变量趋势")
    _module_page_names = {
        "execution_control": "执行控制",
        "energy_input": "能量输入",
        "environmental_constraint": "环境约束",
        "state_maintenance": "状态维持",
    }
    page_name = _module_page_names.get(module_type.value, module_type.value)
    df = load_fused_features()
    if not df.empty:
        module_cols = [c for c in df.columns if c.startswith(f"{module_type.value}__")]
        if module_cols:
            render_all_trend_groups(page_name, df[module_cols].tail(200), module_name=module_type.value, tail_n=0)
        else:
            st.info("该模块暂无特征数据")
    else:
        st.info("暂无特征数据")

    st.markdown("---")

    # ═══ 阈值与规则面板 ═══
    st.markdown("## 阈值与规则状态")
    threshold_data = []
    if module_vars:
        for v in module_vars[:6]:
            val = v.get("current_value", 0)
            contrib = v.get("contribution_degree", 0)
            exceeded = contrib > 0.5
            threshold_data.append({
                "name": v.get("chinese_name", ""),
                "current": f"{val:.2f}" if isinstance(val, (int, float)) else str(val),
                "threshold": "贡献度 > 0.5",
                "exceeded": exceeded,
                "status": "超限" if exceeded else "正常",
            })
    render_threshold_panel(threshold_data)

    st.markdown("---")

    # ═══ 板块 3: 特征与贡献分析区 ═══
    st.markdown("## 特征与贡献分析")

    # Top 贡献变量条形图
    if module_vars:
        top8 = module_vars[:8]
        var_names = [v.get("chinese_name", v.get("variable", "")) for v in top8]
        var_degrees = [v.get("contribution_degree", 0) for v in top8]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=var_names[::-1],
            x=var_degrees[::-1],
            orientation="h",
            marker_color=ACCENT_BLUE,
            text=[f"{d:.2f}" for d in var_degrees[::-1]],
            textposition="outside",
        ))
        fig.update_layout(
            title="模块内变量贡献度排名",
            plot_bgcolor=BG_CONTENT,
            paper_bgcolor=BG_CONTENT,
            font=dict(color=TEXT_SECONDARY, family="Microsoft YaHei", size=12),
            height=max(300, len(top8) * 40),
            margin=dict(l=120, r=40, t=40, b=40),
            xaxis=dict(gridcolor=BORDER_MAIN, title="贡献度"),
            yaxis=dict(gridcolor=BORDER_MAIN),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # 变量统计摘要表
    from src.utils.config_loader import get_variable_by_module
    var_list = get_variable_by_module(module_type.value)
    if var_list:
        st.markdown("### 变量字典")
        var_df = pd.DataFrame(var_list)
        st.dataframe(var_df[["chinese_name", "standard_name", "unit", "data_type", "sampling_rate"]], width="stretch")

    st.markdown("---")

    # ═══ 板块 4: 模型诊断区 ═══
    st.markdown("## 模型诊断")
    model_df = load_model_results()
    if not model_df.empty:
        # 模块相关模型统计量
        module_model_keywords = {
            "execution_control": ["pca_anomaly_score", "pca_t2", "pca_spe"],
            "energy_input": ["pca_anomaly_score", "pca_t2", "if_anomaly_score"],
            "environmental_constraint": ["pca_anomaly_score", "pca_spe", "if_anomaly_score"],
            "state_maintenance": ["pca_anomaly_score", "pca_t2", "pca_spe", "if_anomaly_score", "health_index"],
        }
        keywords = module_model_keywords.get(module_type.value, ["pca_anomaly_score", "if_anomaly_score"])
        avail_cols = [c for c in keywords if c in model_df.columns]
        if avail_cols:
            display_names = {
                "pca_anomaly_score": "PCA异常分数",
                "pca_t2": "T²统计量",
                "pca_spe": "SPE残差统计量",
                "if_anomaly_score": "IF异常分数",
                "health_index": "健康指数",
            }
            render_multi_line_chart(
                model_df[avail_cols].tail(200),
                columns=avail_cols,
                title=f"{meta.chinese_name} — 模型诊断统计量",
                display_names=display_names,
            )
        else:
            st.info("暂无模型诊断数据")
    else:
        st.info("暂无模型结果数据")

    st.markdown("---")

    # ═══ 异常解释卡 ═══
    st.markdown("## 异常解释")
    if module_vars:
        abnormal_vars = [v for v in module_vars if v.get("status") in ("预警", "严重")]
        if abnormal_vars:
            top_abnormal = abnormal_vars[0]
            anomaly_type = "统计异常" if top_abnormal.get("contribution_degree", 0) > 0.3 else "轻微偏离"
            render_diagnosis_card(
                conclusion=f"当前主要异常来自「{top_abnormal.get('chinese_name', '')}」，贡献度 {top_abnormal.get('contribution_degree', 0):.2f}，属于{anomaly_type}。",
                risk_source=f"{meta.chinese_name}模块内变量",
                key_vars=", ".join([v.get("chinese_name", "") for v in abnormal_vars[:3]]),
                suggestion=f"优先排查{top_abnormal.get('chinese_name', '')}的工艺参数是否偏离正常范围。",
                status="warning",
            )
        else:
            render_diagnosis_card(
                conclusion=f"{meta.chinese_name}当前无异常变量，所有指标均在正常范围内。",
                status="normal",
            )

    st.markdown("---")

    # ═══ 板块 5: 模块关系与建议区 ═══
    st.markdown("## 模块关系与建议")

    upstream = []
    downstream = []
    for e in edge_contribs:
        src = e.get("source", "")
        tgt = e.get("target", "")
        if tgt == module_type.value:
            upstream.append(MODULE_SHORT_CHINESE.get(src, src))
        if src == module_type.value:
            downstream.append(MODULE_SHORT_CHINESE.get(tgt, tgt))

    coupling_status = related_edges[0].get("status", "正常") if related_edges else ""
    coupling_strength = related_edges[0].get("coupling_strength", 0.0) if related_edges else 0.0
    direction = f"{meta.chinese_name} → {downstream[0]}" if downstream else "待分析"

    render_relation_summary(
        upstream=upstream,
        downstream=downstream,
        coupling=coupling_status,
        strength=coupling_strength,
        direction=direction,
    )

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # 建议关注
    if module_vars:
        abnormal_vars = [v for v in module_vars if v.get("status") in ("预警", "严重")]
        if abnormal_vars:
            st.warning(f"当前有 {len(abnormal_vars)} 个异常变量需要关注")
            for v in abnormal_vars[:3]:
                st.markdown(f"- **{v.get('chinese_name', '')}** ({v.get('status', '')}): 贡献度 {v.get('contribution_degree', 0):.2f}")
        else:
            st.success("当前模块所有变量状态正常")
    st.markdown(f"**建议处置方向**: 关注{meta.chinese_name}相关变量变化趋势，必要时调整工艺参数")


# ════════════════════════════════════════════════════════════
# 数据接入页面
# ════════════════════════════════════════════════════════════
def render_data_page() -> None:
    st.markdown("# 数据接入")
    st.markdown("支持 Excel 历史数据导入和 DCS 实时数据连接。")

    # ═══ 数据源概况 ═══
    st.markdown("## 数据源概况")
    processed_path = ROOT / "data" / "processed" / "imported_data.csv"
    if processed_path.exists():
        raw_df = load_csv(processed_path, index_col=0, parse_dates=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card("总行数", f"{len(raw_df):,}", status="normal")
        with c2:
            render_kpi_card("变量数", str(len(raw_df.columns)), status="normal")
        with c3:
            missing_rate = raw_df.isnull().sum().sum() / (raw_df.shape[0] * raw_df.shape[1]) * 100
            render_kpi_card("整体缺失率", f"{missing_rate:.2f}%", status="normal" if missing_rate < 1 else "warning")
        with c4:
            render_kpi_card("数据状态", "已导入", status="normal")
    else:
        st.warning("暂无已导入数据")

    st.markdown("---")

    # ═══ 数据质量概览 ═══
    st.markdown("## 数据质量概览")
    if processed_path.exists():
        quality_data = []
        for col in raw_df.columns:
            col_missing = raw_df[col].isnull().sum()
            col_missing_rate = col_missing / len(raw_df) * 100
            quality_data.append({
                "变量名": col,
                "缺失数": col_missing,
                "缺失率": f"{col_missing_rate:.2f}%",
                "数据类型": str(raw_df[col].dtype),
                "唯一值数": raw_df[col].nunique(),
            })
        quality_df = pd.DataFrame(quality_data)
        st.dataframe(quality_df, width="stretch")

        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

        # 数据质量结论卡
        high_missing = [q for q in quality_data if float(q["缺失率"].replace("%","")) > 5]
        if high_missing:
            render_diagnosis_card(
                conclusion=f"数据整体缺失率 {missing_rate:.2f}%，其中有 {len(high_missing)} 个变量缺失率超过 5%。",
                risk_source=", ".join([q["变量名"] for q in high_missing[:3]]),
                suggestion="建议对高缺失率变量进行插值或剔除处理。",
                status="warning",
            )
        else:
            render_diagnosis_card(
                conclusion=f"数据质量良好，整体缺失率 {missing_rate:.2f}%，所有变量缺失率均在 5% 以内。",
                status="normal",
            )

        # 样本构造参数
        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
        from src.utils.config_loader import load_feature_config
        feat_cfg = load_feature_config()
        window = feat_cfg.get("sliding_window", {}).get("window_length", "N/A")
        step = feat_cfg.get("sliding_window", {}).get("step", "N/A")
        render_kv_panel([
            ("滑动窗口长度", str(window)),
            ("滑动步长", str(step)),
            ("变量总数", str(len(raw_df.columns))),
            ("样本总数", f"{len(raw_df):,}"),
        ], title="样本构造参数")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Excel 导入", "DCS 连接", "数据字典"])

    with tab1:
        st.markdown("### Excel 数据导入")
        uploaded = st.file_uploader("上传 Excel 文件", type=["xlsx"], key="excel_upload")
        if uploaded is not None:
            df = pd.read_excel(uploaded, engine="openpyxl")
            st.dataframe(df.head(20), width="stretch")
            st.info(f"共 {len(df)} 行 × {len(df.columns)} 列")

        st.markdown("### 已导入数据")
        if processed_path.exists():
            st.dataframe(raw_df.tail(20), width="stretch")
            st.info(f"共 {len(raw_df)} 行 × {len(raw_df.columns)} 列")
        else:
            st.warning("暂无已导入数据")

    with tab2:
        st.markdown("### DCS 实时数据连接")
        st.info("当前使用 MockDCSConnector 模拟实时数据流。")
        st.markdown("- 连接类型: Mock")
        st.markdown("- 数据源: data/processed/cleaned_data.csv")
        st.markdown("- 轮询间隔: 2.0s")
        st.markdown("- 缓冲区大小: 500")

    with tab3:
        st.markdown("### 数据字典预览")
        from src.utils.config_loader import load_variable_dictionary
        var_dict = load_variable_dictionary()
        if var_dict:
            dict_df = pd.DataFrame(var_dict)
            display_cols = [c for c in ["chinese_name", "standard_name", "raw_tag", "unit", "module", "data_type", "sampling_rate", "usage"] if c in dict_df.columns]
            st.dataframe(dict_df[display_cols], width="stretch")
        else:
            st.info("暂无数据字典")


# ════════════════════════════════════════════════════════════
# 特征分析页面
# ════════════════════════════════════════════════════════════
def render_feature_page() -> None:
    st.markdown("# 特征分析")
    df = load_fused_features()
    if df.empty:
        st.warning("暂无特征数据，请先运行特征构建脚本。")
        return

    # ═══ 特征概览 ═══
    st.markdown("## 特征概览")
    modules = ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]
    module_cn = {
        "execution_control": "执行控制",
        "energy_input": "能量输入",
        "environmental_constraint": "环境约束",
        "state_maintenance": "状态维持",
    }
    c1, c2, c3, c4 = st.columns(4)
    total_features = 0
    for col, mod in zip([c1, c2, c3, c4], modules):
        mod_cols = [c for c in df.columns if c.startswith(f"{mod}__")]
        total_features += len(mod_cols)
        with col:
            render_kpi_card(f"{module_cn[mod]}特征数", str(len(mod_cols)), status="normal")

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # 特征分析结论卡
    render_diagnosis_card(
        conclusion=f"当前融合特征共 {len(df.columns)} 列，其中入模特征 {total_features} 个，覆盖 4 个模块。",
        risk_source="特征选择后保留方差最大、相关性最低的特征",
        suggestion="关注各模块特征方差分布，确保关键变量被保留。",
        status="normal",
    )

    st.markdown("---")

    # ═══ 特征重要性排序 ═══
    st.markdown("## 特征方差排序（全局 Top 20）")
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        variances = df[numeric_cols].var().sort_values(ascending=False).head(20)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=[c.split("__", 1)[1] if "__" in c else c for c in variances.index[::-1]],
            x=variances.values[::-1],
            orientation="h",
            marker_color=ACCENT_BLUE,
        ))
        fig.update_layout(
            plot_bgcolor=BG_CONTENT,
            paper_bgcolor=BG_CONTENT,
            font=dict(color=TEXT_SECONDARY, family="Microsoft YaHei", size=11),
            height=500,
            margin=dict(l=200, r=40, t=20, b=40),
            xaxis=dict(gridcolor=BORDER_MAIN, title="方差"),
            yaxis=dict(gridcolor=BORDER_MAIN),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["执行控制", "能量输入", "环境约束", "状态维持"])
    tabs = [tab1, tab2, tab3, tab4]

    for tab, mod in zip(tabs, modules):
        with tab:
            cols = [c for c in df.columns if c.startswith(f"{mod}__")]
            if cols:
                st.markdown(f"### {module_cn[mod]}模块特征数据")
                st.dataframe(df[cols].tail(100), width="stretch")
                render_all_trend_groups("特征分析", df[cols].tail(200), module_name=mod, tail_n=0)
            else:
                st.info(f"该模块暂无特征")


# ════════════════════════════════════════════════════════════
# 模型训练页面
# ════════════════════════════════════════════════════════════
def render_model_page() -> None:
    st.markdown("# 模型训练")
    df = load_model_results()
    if df.empty:
        st.warning("暂无模型结果，请先运行训练脚本 (04_train_baseline_models.py)。")
        return

    # ═══ 模型清单 ═══
    st.markdown("## 当前模型清单")
    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card("PCA 监测模型", "已加载", subtext="n_components=0.95", status="normal")
    with c2:
        render_kpi_card("Isolation Forest", "已加载", subtext="n_estimators=200", status="normal")
    with c3:
        render_kpi_card("健康指数计算器", "已启用", subtext="四因子加权融合", status="normal")

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # 模型运行说明卡
    render_diagnosis_card(
        conclusion="当前系统加载 PCA 监测模型和 Isolation Forest 异常检测模型，健康指数由四因子加权融合计算。",
        risk_source="PCA T²/SPE 统计量 + IF 异常分数 + 模块评分 + 事件惩罚",
        suggestion="关注 PCA 统计量和 IF 异常分数的联合变化趋势。",
        status="normal",
    )

    st.markdown("---")

    # ═══ 模型配置 ═══
    st.markdown("## 模型超参数配置")
    from src.utils.config_loader import load_model_config
    model_cfg = load_model_config()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### PCA 配置")
        pca_cfg = model_cfg.get("pca", {})
        st.markdown(f"- n_components: {pca_cfg.get('n_components', 'N/A')}")
        st.markdown(f"- anomaly_threshold_percentile: {pca_cfg.get('anomaly_threshold_percentile', 'N/A')}")
        st.markdown("### Isolation Forest 配置")
        if_cfg = model_cfg.get("isolation_forest", {})
        st.markdown(f"- n_estimators: {if_cfg.get('n_estimators', 'N/A')}")
        st.markdown(f"- contamination: {if_cfg.get('contamination', 'N/A')}")
    with col_b:
        st.markdown("### 健康指数权重")
        hi_weights = model_cfg.get("health_index", {}).get("weights", {})
        for k, v in hi_weights.items():
            st.markdown(f"- {k}: {v}")
        st.markdown("### 风险融合模块权重")
        rf_weights = model_cfg.get("risk_fusion", {}).get("module_weights", {})
        for k, v in rf_weights.items():
            st.markdown(f"- {MODULE_SHORT_CHINESE.get(k, k)}: {v}")

    st.markdown("---")

    # ═══ 训练结果统计 ═══
    st.markdown("## 训练结果统计摘要")
    st.info(f"模型结果: {len(df)} 条记录")
    stat_cols = ["pca_anomaly_score", "pca_t2", "pca_spe", "if_anomaly_score", "health_index", "risk_score"]
    avail = [c for c in stat_cols if c in df.columns]
    if avail:
        stat_df = df[avail].describe().T
        stat_df.index = ["PCA异常分数", "T²统计量", "SPE统计量", "IF异常分数", "健康指数", "风险分数"][:len(avail)]
        st.dataframe(stat_df, width="stretch")

    st.markdown("---")

    # ═══ 趋势图 ═══
    st.markdown("## 模型输出趋势")
    render_all_trend_groups("模型训练", df.tail(200))


# ════════════════════════════════════════════════════════════
# 在线监测页面
# ════════════════════════════════════════════════════════════
def render_online_page() -> None:
    st.markdown("# 在线监测")
    st.info("当前使用 MockDCSConnector 模拟在线监测。")

    status = get_current_status()
    level_labels = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}

    # ═══ 实时状态卡片 ═══
    st.markdown("## 实时状态")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card("风险分数", f"{status['risk_score']:.1f}", status=status["risk_level"])
    with col2:
        hi = status['health_index']
        hi_status = "normal" if hi > 80 else ("attention" if hi > 60 else "warning")
        render_kpi_card("健康指数", f"{hi:.1f}", status=hi_status)
    with col3:
        render_kpi_card("样本数", str(status["sample_count"]), status="normal")
    with col4:
        render_kpi_card("风险等级", level_labels.get(status["risk_level"], status["risk_level"]), status=status["risk_level"])

    st.markdown("---")

    # ═══ 模块状态评分 ═══
    st.markdown("## 四模块状态评分")
    module_names = {
        "execution_control": "执行控制",
        "energy_input": "能量输入",
        "environmental_constraint": "环境约束",
        "state_maintenance": "状态维持",
    }
    for mod, name in module_names.items():
        score = status["module_scores"].get(mod, 100.0)
        render_module_score_bar(mod, score, name)

    st.markdown("---")

    # ═══ 主异常链路 ═══
    st.markdown("## 当前主异常链路")
    abnormal_module = MODULE_ID_TO_CHINESE.get(status["main_abnormal_module"], status["main_abnormal_module"])
    abnormal_coupling = format_coupling_text(status["main_abnormal_coupling"])

    df = load_model_results()

    # 实时异常解释卡
    rs = status["risk_score"]
    risk_desc = "正常" if rs < 30 else ("关注" if rs < 50 else ("预警" if rs < 70 else "严重"))
    render_diagnosis_card(
        conclusion=f"当前系统状态为「{risk_desc}」，主异常来源为{abnormal_module}，主耦合异常为{abnormal_coupling}。",
        risk_source=abnormal_module,
        key_vars=abnormal_coupling,
        suggestion=f"重点关注{abnormal_module}的实时数据变化。",
        status=status["risk_level"],
    )

    st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

    # 模块风险排名表
    st.markdown("### 模块风险排名")
    module_scores = status.get("module_scores", {})
    rank_data = []
    for mod_id, mod_score in sorted(module_scores.items(), key=lambda x: x[1]):
        mod_risk = ModuleScorer.determine_risk_level(100 - mod_score)
        rank_data.append({
            "模块": MODULE_SHORT_CHINESE.get(mod_id, mod_id),
            "评分": f"{mod_score:.1f}",
            "风险等级": level_labels.get(mod_risk, mod_risk),
        })
    st.dataframe(pd.DataFrame(rank_data), width="stretch", hide_index=True)

    # 最近预警
    if not df.empty and "risk_level" in df.columns:
        recent_alarms = df[df["risk_level"].isin(["warning", "severe"])].tail(5)
        if not recent_alarms.empty:
            st.markdown("### 最近预警")
            alarm_cols = [c for c in ["risk_score", "risk_level", "health_index", "pca_anomaly_score"] if c in recent_alarms.columns]
            st.dataframe(recent_alarms[alarm_cols], width="stretch")

    st.markdown("---")

    # ═══ 异常根因分析 ═══
    st.markdown("## 异常根因分析")
    if not df.empty and "pca_anomaly_score" in df.columns:
        # 找到最新的异常样本
        anomalous = df[df["pca_anomaly_score"] > 1.0]
        if not anomalous.empty:
            last_anom = anomalous.iloc[-1]
            st.caption(f"最近异常样本: 索引 {anomalous.index[-1]}, PCA异常分数 {last_anom['pca_anomaly_score']:.2f}")

            # 尝试加载 PCA 模型获取贡献度
            pca_path = ROOT / "outputs" / "models" / "pca_monitor.joblib"
            if pca_path.exists():
                import joblib
                from src.models.root_cause_analyzer import RootCauseAnalyzer

                pca_data = joblib.load(pca_path)
                pca_model_inst = PCAMonitor()
                pca_model_inst.pca = pca_data["pca"]
                pca_model_inst.scaler = pca_data["scaler"]
                pca_model_inst.t2_threshold = pca_data["t2_threshold"]
                pca_model_inst.spe_threshold = pca_data["spe_threshold"]
                pca_model_inst._feature_names = pca_data.get("feature_names", [])
                pca_model_inst._is_fitted = True

                # 取异常样本的特征列
                feature_cols = [c for c in df.columns if c not in
                               ["pca_anomaly_score", "pca_t2", "pca_spe",
                                "if_anomaly_score", "health_index", "risk_score",
                                "risk_level", "pls_anomaly_score",
                                "root_cause_variable", "root_cause_module",
                                "root_cause_contribution"]]
                if feature_cols:
                    X_anom = anomalous[feature_cols].iloc[-1:]
                    X_scaled = pca_model_inst.scaler.transform(X_anom)
                    contributions = pca_model_inst._compute_contributions(X_scaled)

                    if contributions is not None:
                        rca = RootCauseAnalyzer()
                        analysis = rca.analyze_sample(
                            contributions[0], feature_cols, X_anom.iloc[0], top_k=8
                        )

                        # 根因贡献度瀑布图
                        from src.visualization.model_details_charts import render_root_cause_waterfall, render_module_contribution_pie

                        rc1, rc2 = st.columns([2, 1])
                        with rc1:
                            render_root_cause_waterfall(analysis)
                        with rc2:
                            render_module_contribution_pie(analysis["module_contributions"])

                        # 根因明细表
                        st.markdown("### 根因明细")
                        rc_df = pd.DataFrame(analysis["root_causes"])
                        if not rc_df.empty:
                            display_cols = ["rank", "variable", "module_cn", "contribution", "trend"]
                            display_cols = [c for c in display_cols if c in rc_df.columns]
                            st.dataframe(rc_df[display_cols], width="stretch", hide_index=True)

                        # 主因结论
                        top1 = analysis["root_causes"][0] if analysis["root_causes"] else {}
                        render_diagnosis_card(
                            conclusion=f"异常主因: {top1.get('variable', '未知')}（{top1.get('module_cn', '')}），贡献度 {top1.get('abs_contribution', 0):.3f}",
                            risk_source=f"主因模块: {analysis['main_module_cn']}，贡献占比 {analysis['module_contributions'].get(analysis['main_module'], 0)*100:.1f}%",
                            suggestion=f"建议重点监测{analysis['main_module_cn']}模块的{top1.get('variable', '')}变量变化趋势。",
                            status="warning",
                        )
            else:
                st.info("PCA 模型文件未找到，无法进行根因分析。请先运行训练脚本。")
        else:
            st.success("当前无异常样本，所有数据均在正常范围内。")
    else:
        st.info("暂无异常检测数据")

    st.markdown("---")

    # ═══ 趋势图 ═══
    st.markdown("## 实时趋势")
    if not df.empty:
        render_all_trend_groups("在线监测", df.tail(200))


# ════════════════════════════════════════════════════════════
# 预警记录页面
# ════════════════════════════════════════════════════════════
def render_alarm_page() -> None:
    st.markdown("# 预警记录")

    df = load_model_results()
    if df.empty:
        st.warning("暂无预警数据。")
        return

    # ═══ 预警统计 ═══
    st.markdown("## 预警统计")
    if "risk_level" in df.columns:
        alarms = df[df["risk_level"].isin(["warning", "severe"])]
        level_counts = df["risk_level"].value_counts()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card("总记录数", f"{len(df):,}", status="normal")
        with c2:
            render_kpi_card("预警记录", str(len(alarms)), status="warning" if len(alarms) > 0 else "normal")
        with c3:
            severe_count = level_counts.get("severe", 0)
            render_kpi_card("严重预警", str(severe_count), status="severe" if severe_count > 0 else "normal")
        with c4:
            warning_count = level_counts.get("warning", 0)
            render_kpi_card("一般预警", str(warning_count), status="warning" if warning_count > 0 else "normal")

        st.markdown("---")

        # 异常事件时间线
        st.markdown("## 异常事件时间线")
        render_anomaly_timeline(df)

        st.markdown("---")

        # 风险等级分布
        st.markdown("## 风险等级分布")
        level_map = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}
        dist_data = {level_map.get(k, k): v for k, v in level_counts.items()}
        fig = go.Figure()
        colors = {"正常": ACCENT_BLUE, "关注": WARN_AMBER, "预警": WARN_AMBER, "严重": RISK_RED}
        fig.add_trace(go.Bar(
            x=list(dist_data.keys()),
            y=list(dist_data.values()),
            marker_color=[colors.get(k, TEXT_MUTED) for k in dist_data.keys()],
            text=list(dist_data.values()),
            textposition="outside",
        ))
        fig.update_layout(
            plot_bgcolor=BG_CONTENT,
            paper_bgcolor=BG_CONTENT,
            font=dict(color=TEXT_SECONDARY, family="Microsoft YaHei", size=12),
            height=300,
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(gridcolor=BORDER_MAIN),
            yaxis=dict(gridcolor=BORDER_MAIN, title="记录数"),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

        # 预警结论卡
        if len(alarms) > 0:
            severe_pct = severe_count / len(alarms) * 100 if len(alarms) > 0 else 0
            render_diagnosis_card(
                conclusion=f"共 {len(alarms)} 条预警记录，其中严重预警 {severe_count} 条（{severe_pct:.1f}%），一般预警 {warning_count} 条。",
                risk_source="融合判定结果 + 规则引擎",
                suggestion="建议优先处理严重预警，排查对应模块变量的工艺参数。",
                status="warning" if severe_count == 0 else "severe",
            )
        else:
            render_diagnosis_card(
                conclusion="当前无预警记录，设备状态正常。",
                status="normal",
            )

        st.markdown("---")

        # 预警记录表
        st.markdown("## 预警记录明细")
        if not alarms.empty:
            display_cols = []
            for c in ["risk_score", "risk_level", "health_index", "pca_anomaly_score", "if_anomaly_score"]:
                if c in alarms.columns:
                    display_cols.append(c)
            st.dataframe(alarms[display_cols].tail(50), width="stretch")
        else:
            st.success("暂无预警记录，设备状态正常。")

    st.markdown("---")

    # ═══ 趋势图 ═══
    st.markdown("## 预警趋势")
    render_all_trend_groups("预警记录", df.tail(200))


# ════════════════════════════════════════════════════════════
# 健康趋势页面
# ════════════════════════════════════════════════════════════
def render_health_trend_page() -> None:
    st.markdown("# 健康趋势")
    df = load_model_results()
    if df.empty:
        st.warning("暂无健康趋势数据。")
        return

    # ═══ 导出报告 ═══
    status = get_current_status()
    col_btn, col_spacer = st.columns([1, 3])
    with col_btn:
        if st.button("导出 PDF 诊断报告", type="primary", key="export_pdf_btn"):
            try:
                from src.reporting.pdf_report import generate_pdf_report
                from src.models.root_cause_analyzer import RootCauseAnalyzer
                import joblib as _joblib

                # 准备根因数据
                rca_result = None
                pca_path = ROOT / "outputs" / "models" / "pca_monitor.joblib"
                if pca_path.exists() and "pca_anomaly_score" in df.columns:
                    anomalous = df[df["pca_anomaly_score"] > 1.0]
                    if not anomalous.empty:
                        pca_data = _joblib.load(pca_path)
                        feature_cols = [c for c in df.columns if c not in
                                       ["pca_anomaly_score", "pca_t2", "pca_spe",
                                        "if_anomaly_score", "health_index", "risk_score",
                                        "risk_level", "pls_anomaly_score",
                                        "root_cause_variable", "root_cause_module",
                                        "root_cause_contribution"]]
                        if feature_cols:
                            X_anom = anomalous[feature_cols].iloc[-1:]
                            scaler = pca_data["scaler"]
                            pca_obj = pca_data["pca"]
                            X_scaled = scaler.transform(X_anom)
                            T = pca_obj.transform(X_scaled)
                            X_reconstructed = pca_obj.inverse_transform(T)
                            contributions = X_scaled - X_reconstructed
                            rca = RootCauseAnalyzer()
                            rca_result = rca.analyze_sample(contributions[0], feature_cols, X_anom.iloc[0])

                pdf_path = ROOT / "outputs" / "reports" / f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                generate_pdf_report(df, status, pdf_path, root_cause_result=rca_result)
                st.success(f"报告已生成: {pdf_path}")
            except Exception as e:
                st.error(f"报告生成失败: {e}")

    # ═══ 健康概览 ═══
    st.markdown("## 健康概览")
    if "health_index" in df.columns:
        hi = df["health_index"]
        hi_current = hi.iloc[-1]
        hi_status = "normal" if hi_current > 80 else ("attention" if hi_current > 60 else ("warning" if hi_current > 40 else "severe"))

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_kpi_card("当前健康指数", f"{hi_current:.1f}", status=hi_status)
        with c2:
            render_kpi_card("平均健康指数", f"{hi.mean():.1f}", status="normal")
        with c3:
            render_kpi_card("最低健康指数", f"{hi.min():.1f}", status="warning")
        with c4:
            render_kpi_card("健康趋势", "下降" if hi.iloc[-1] < hi.iloc[-50] else "稳定", status="attention" if hi.iloc[-1] < hi.iloc[-50] else "normal")

        st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)

        # 健康诊断卡
        hi_level = "健康" if hi_current > 80 else ("亚健康" if hi_current > 60 else ("异常" if hi_current > 40 else "严重异常"))
        trend_desc = "下降趋势" if hi.iloc[-1] < hi.iloc[-50] else "稳定"
        render_diagnosis_card(
            conclusion=f"当前健康指数 {hi_current:.1f}，健康等级为「{hi_level}」，近期呈{trend_desc}。",
            risk_source=f"最低健康指数 {hi.min():.1f}，平均 {hi.mean():.1f}",
            suggestion="关注健康指数下降趋势，必要时安排预防性维护。",
            status=hi_status,
        )

    st.markdown("---")

    # ═══ 退化轨迹 ═══
    st.markdown("## 退化轨迹")
    render_degradation_trajectory(df, col="health_index", window=50)

    st.markdown("---")

    # ═══ 模块健康贡献 ═══
    st.markdown("## 模块健康贡献")
    status = get_current_status()
    module_scores = status.get("module_scores", {})
    if module_scores:
        mod_cn = {
            "execution_control": "执行控制",
            "energy_input": "能量输入",
            "environmental_constraint": "环境约束",
            "state_maintenance": "状态维持",
        }
        fig = go.Figure()
        names = [mod_cn.get(k, k) for k in module_scores.keys()]
        scores = list(module_scores.values())
        bar_colors = [ACCENT_BLUE if s > 80 else (WARN_AMBER if s > 60 else RISK_RED) for s in scores]
        fig.add_trace(go.Bar(
            x=names,
            y=scores,
            marker_color=bar_colors,
            text=[f"{s:.1f}" for s in scores],
            textposition="outside",
        ))
        fig.update_layout(
            title="四模块健康评分",
            plot_bgcolor=BG_CONTENT,
            paper_bgcolor=BG_CONTENT,
            font=dict(color=TEXT_SECONDARY, family="Microsoft YaHei", size=12),
            height=300,
            margin=dict(l=40, r=40, t=50, b=40),
            xaxis=dict(gridcolor=BORDER_MAIN),
            yaxis=dict(gridcolor=BORDER_MAIN, title="评分", range=[0, 105]),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown("---")

    # ═══ 风险-健康联动 ═══
    if "risk_score" in df.columns and "health_index" in df.columns:
        st.markdown("## 风险-健康联动")
        fig = go.Figure()
        fig.add_trace(go.Scattergl(
            x=df["health_index"].tail(500),
            y=df["risk_score"].tail(500),
            mode="markers",
            marker=dict(color=ACCENT_BLUE, size=4, opacity=0.6),
            name="样本点",
        ))
        fig.update_layout(
            title="健康指数 vs 风险分数",
            plot_bgcolor=BG_CONTENT,
            paper_bgcolor=BG_CONTENT,
            font=dict(color=TEXT_SECONDARY, family="Microsoft YaHei", size=12),
            height=380,
            margin=dict(l=40, r=40, t=50, b=40),
            xaxis=dict(gridcolor=BORDER_MAIN, title="健康指数"),
            yaxis=dict(gridcolor=BORDER_MAIN, title="风险分数"),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    st.markdown("---")

    # ═══ 维护建议 ═══
    st.markdown("## 维护建议")
    status = get_current_status()
    hi_val = status.get("health_index", 100)
    if hi_val > 80:
        maintenance_level = "正常巡检"
        maintenance_desc = "设备健康状态良好，维持常规巡检频率。"
    elif hi_val > 60:
        maintenance_level = "加强监测"
        maintenance_desc = "设备健康状态一般，建议增加监测频率，关注退化趋势。"
    elif hi_val > 40:
        maintenance_level = "预防性维护"
        maintenance_desc = "设备健康状态异常，建议安排预防性维护，排查关键变量。"
    else:
        maintenance_level = "紧急维护"
        maintenance_desc = "设备健康状态严重异常，建议立即安排维护。"

    render_kv_panel([
        ("维护等级", maintenance_level),
        ("当前健康指数", f"{hi_val:.1f}"),
        ("建议", maintenance_desc),
    ], title="维护建议")

    st.markdown("---")

    # ═══ 趋势图 ═══
    st.markdown("## 健康趋势详情")
    render_all_trend_groups("健康趋势", df)


# ════════════════════════════════════════════════════════════
# 算法参考页面
# ════════════════════════════════════════════════════════════
def render_algorithm_reference_page() -> None:
    from src.visualization.model_formulas import MODEL_FORMULAS, render_formula_card_html
    from src.visualization.model_details_charts import (
        render_scree_plot,
        render_loading_plot,
        render_t2_spe_scatter,
        render_pca_2d_scatter,
        render_hi_waterfall,
        render_risk_waterfall,
        render_model_flow_sankey,
        render_correlation_heatmap,
        render_coupling_strength_matrix,
    )

    st.markdown("# 算法参考")
    st.caption("展示所有模型的数学公式、参数配置、数据流关系和内部诊断图表")

    df = load_model_results()
    fused_df = load_fused_features()
    status = get_current_status()
    graph = get_coupling_graph()
    module_scores = status.get("module_scores", {})

    # ── Section 1: 模型概览 ──
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

    # ── Section 2: 模型数据流 ──
    st.markdown("## 模型数据流")
    st.caption("从原始特征到诊断预警的完整数据处理链路")
    render_model_flow_sankey()

    st.markdown("---")

    # ── Section 3: 模型详情 Tabs ──
    st.markdown("## 模型详情")
    tab_pca, tab_if, tab_hi, tab_risk, tab_mod = st.tabs(
        ["PCA 监测", "Isolation Forest", "健康指数", "风险融合", "模块级 PCA"]
    )

    # PCA Tab
    with tab_pca:
        st.markdown(render_formula_card_html("pca_monitor"), unsafe_allow_html=True)

        # 尝试加载 PCA 模型做诊断图
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

                # T² vs SPE 散点图
                if not df.empty and "pca_t2" in df.columns and "pca_spe" in df.columns:
                    is_anom = df["pca_anomaly_score"].values > 1.0 if "pca_anomaly_score" in df.columns else None
                    render_t2_spe_scatter(
                        df["pca_t2"].values,
                        df["pca_spe"].values,
                        t2_th, spe_th,
                        is_anomaly=is_anom.astype(int) if is_anom is not None else None,
                    )

                # PCA 2D 散点
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
            fig.add_trace(go.Histogram(
                x=df["if_anomaly_score"], nbinsx=50,
                marker_color=ACCENT_BLUE, opacity=0.7,
            ))
            fig.add_vline(x=0.7, line_dash="dash", line_color=RISK_RED,
                          annotation_text="异常阈值 (0.7)", annotation_font_color=RISK_RED)
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

            # 计算模块均分
            mod_scores = {}
            for mod in ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]:
                cols = [c for c in df.columns if c.startswith(f"{mod}__")]
                if cols:
                    mod_scores[mod] = float(ModuleScorer.compute_module_score(df[cols].iloc[-1]))
            mod_mean = np.mean(list(mod_scores.values())) if mod_scores else 80.0

            hi_val = float(last.get("health_index", 0))
            cfg_weights = {"pca_score": 0.25, "isolation_forest_score": 0.25, "module_scores": 0.35, "event_penalty": 0.15}

            render_hi_waterfall(
                pca_health=max(0, (1 - pca_anom)) * 100,
                if_health=max(0, (1 - if_anom)) * 100,
                mod_health=mod_mean,
                event_health=100.0,  # 无事件数据时默认 100
                weights=cfg_weights,
                final_hi=hi_val,
            )

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

            # 模块加权健康
            mw = {"execution_control": 0.15, "energy_input": 0.20,
                  "environmental_constraint": 0.20, "state_maintenance": 0.45}
            weighted_health = sum(module_scores.get(m, 80) * w for m, w in mw.items()) / sum(mw.values())
            module_risk = 100 - weighted_health

            render_risk_waterfall(
                module_risk=module_risk,
                anomaly_score=anomaly,
                hi_deficit=100 - hi_val,
                event_penalty=0.0,
                final_risk=rs_val,
            )

        # 模块权重饼图
        st.markdown("### 模块权重配置")
        mw = {"执行控制": 0.15, "能量输入": 0.20, "环境约束": 0.20, "状态维持": 0.45}
        fig = go.Figure(go.Pie(
            labels=list(mw.keys()),
            values=list(mw.values()),
            hole=0.4,
            marker=dict(colors=[ACCENT_BLUE, HEALTH_GREEN, WARN_AMBER, RISK_RED]),
            textinfo="label+percent",
            textfont=dict(size=12, color=TEXT_MAIN),
        ))
        layout = _get_base_layout("模块风险权重分配", height=300, n_traces=1)
        fig.update_layout(**layout)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # Module PCA Tab
    with tab_mod:
        st.markdown(render_formula_card_html("module_level_pca"), unsafe_allow_html=True)

        st.markdown("### 四模块评分")
        if module_scores:
            mod_cn = {
                "execution_control": "执行控制",
                "energy_input": "能量输入",
                "environmental_constraint": "环境约束",
                "state_maintenance": "状态维持",
            }
            mod_data = []
            for mod_id, score in sorted(module_scores.items(), key=lambda x: x[1]):
                mod_data.append({
                    "模块": mod_cn.get(mod_id, mod_id),
                    "评分": f"{score:.1f}",
                    "状态": "健康" if score > 80 else ("亚健康" if score > 60 else ("异常" if score > 40 else "严重异常")),
                })
            st.dataframe(pd.DataFrame(mod_data), width="stretch", hide_index=True)

    st.markdown("---")

    # ── Section 4: 耦合分析 ──
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

    # ── Section 5: 阈值参考表 ──
    st.markdown("## 阈值与配置参考")
    from src.utils.config_loader import load_model_config
    cfg = load_model_config()

    threshold_rows = []
    # PCA
    pca_cfg = cfg.get("pca", {})
    threshold_rows.append({"模型/组件", "参数", "当前值", "说明"})
    threshold_rows = [
        {"模型": "PCA", "参数": "n_components", "当前值": str(pca_cfg.get("n_components", 0.95)), "说明": "方差保留比例"},
        {"模型": "PCA", "参数": "threshold_percentile", "当前值": str(pca_cfg.get("anomaly_threshold_percentile", 99)), "说明": "异常阈值百分位"},
    ]
    # IF
    if_cfg = cfg.get("isolation_forest", {})
    threshold_rows += [
        {"模型": "IF", "参数": "n_estimators", "当前值": str(if_cfg.get("n_estimators", 200)), "说明": "隔离树数量"},
        {"模型": "IF", "参数": "contamination", "当前值": str(if_cfg.get("contamination", 0.05)), "说明": "预期异常比例"},
    ]
    # HI
    hi_weights = cfg.get("health_index", {}).get("weights", {})
    for k, v in hi_weights.items():
        threshold_rows.append({"模型": "健康指数", "参数": f"weight.{k}", "当前值": str(v), "说明": "融合权重"})
    # Risk
    risk_thresh = cfg.get("risk_fusion", {}).get("risk_thresholds", {})
    for k, v in risk_thresh.items():
        threshold_rows.append({"模型": "风险融合", "参数": f"threshold.{k}", "当前值": str(v), "说明": "风险等级阈值"})

    st.dataframe(pd.DataFrame(threshold_rows), width="stretch", hide_index=True)


# ════════════════════════════════════════════════════════════
# 路由
# ════════════════════════════════════════════════════════════
page = st.session_state.current_page

if page == "首页":
    render_home_page()
elif page == "执行控制":
    render_module_page(ModuleType.EXECUTION_CONTROL)
elif page == "能量输入":
    render_module_page(ModuleType.ENERGY_INPUT)
elif page == "环境约束":
    render_module_page(ModuleType.ENVIRONMENTAL_CONSTRAINT)
elif page == "状态维持":
    render_module_page(ModuleType.STATE_MAINTENANCE)
elif page == "数据接入":
    render_data_page()
elif page == "特征分析":
    render_feature_page()
elif page == "模型训练":
    render_model_page()
elif page == "在线监测":
    render_online_page()
elif page == "预警记录":
    render_alarm_page()
elif page == "健康趋势":
    render_health_trend_page()
elif page == "算法参考":
    render_algorithm_reference_page()
else:
    render_home_page()
