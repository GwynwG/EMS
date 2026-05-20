"""特种材料制备设备状态监测与智能预警系统 - Streamlit 主应用。"""
from __future__ import annotations

import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import json
import numpy as np
import pandas as pd
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
)
from src.visualization.theme import (
    BG_MAIN,
    BG_SIDEBAR,
    BG_CARD,
    BG_CARD_SOFT,
    BORDER_MAIN,
    BORDER_SOFT,
    TEXT_MAIN,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_BLUE,
    RISK_RED,
    STATUS_COLORS,
    FONT_FAMILY,
    FONT_MONO,
)

# ── 页面配置 ──
st.set_page_config(
    page_title="设备状态监测与智能预警系统",
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
    background: #2A2D33 !important;
    color: #D4D4D4 !important;
    border: 1px solid #3A3F46 !important;
    border-radius: 6px !important;
    margin-bottom: 2px;
    transition: all 0.2s ease;
    font-family: {FONT_FAMILY};
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: #333842 !important;
    color: #F1F5F9 !important;
    border-color: #4B5563 !important;
}}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {{
    background: #333842 !important;
    color: #F1F5F9 !important;
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
    background: #333842 !important;
    color: {TEXT_MAIN} !important;
    border: 1px solid {ACCENT_BLUE} !important;
}}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="stBaseButton-secondary"] {{
    background: {BG_CARD_SOFT} !important;
    color: {TEXT_SECONDARY} !important;
    border: 1px solid {BORDER_MAIN} !important;
}}
.stButton > button:hover {{
    background: #303640 !important;
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
    background: #1F232A;
    border-radius: 12px;
    padding: 8px;
    gap: 8px;
    border: 1px solid #3A3F46;
}}
.stTabs [data-baseweb="tab"] {{
    background: #2A2D33 !important;
    color: #A7B0BD !important;
    border-radius: 10px;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 17px !important;
    font-weight: 600 !important;
    padding: 12px 28px !important;
    min-height: 48px !important;
    border: 1px solid transparent;
    transition: all 0.2s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{
    background: #333842 !important;
    color: #E6EDF3 !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, #2B3A4A, #333842) !important;
    color: #F1F5F9 !important;
    border: 1px solid rgba(79,193,255,0.3) !important;
    border-bottom: 3px solid #4FC1FF !important;
    box-shadow: 0 2px 12px rgba(79,193,255,0.2);
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

PAGES = ["首页", "执行控制", "能量输入", "环境约束", "状态维持", "数据接入", "特征分析", "模型训练", "在线监测", "预警记录", "健康趋势"]

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
        <div style="font-size: 18px; font-weight: 600; color: #D4D4D4; font-family: {FONT_FAMILY};">设备监测系统</div>
        <div style="font-size: 11px; color: #858585; margin-top: 2px; font-family: {FONT_MONO};">EQUIPMENT MONITORING</div>
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
# 首页 - 设备状态监测与智能预警驾驶舱
# ════════════════════════════════════════════════════════════
def render_home_page() -> None:
    from datetime import datetime
    from src.domain_framework.module_scoring import ModuleScorer

    status = get_current_status()
    df = load_model_results()
    graph = get_coupling_graph()
    module_scores = status.get("module_scores", {})

    # ── Section 1: 页面标题区 ──
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"""
    <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end;">
        <div>
            <div style="font-size: 12px; color: {TEXT_MUTED}; text-transform: uppercase; letter-spacing: 0.1em; font-family: {FONT_MONO}; margin-bottom: 4px;">
                EQUIPMENT MONITORING COCKPIT
            </div>
            <div style="font-size: 30px; font-weight: 700; color: {TEXT_MAIN}; font-family: {FONT_FAMILY}; letter-spacing: -0.01em;">
                特种材料制备设备状态监测与智能预警系统
            </div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 12px; color: {TEXT_MUTED}; font-family: {FONT_MONO};">运行模式: Mock DCS 模拟</div>
            <div style="font-size: 12px; color: {TEXT_SECONDARY}; font-family: {FONT_MONO};">{now_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Section 2: KPI 总览区（2行×4列）──
    risk_status = status["risk_level"]
    hi = status["health_index"]
    hi_status = "normal" if hi > 80 else ("attention" if hi > 60 else ("warning" if hi > 40 else "severe"))
    rs = status["risk_score"]
    rs_status = "severe" if rs > 70 else ("warning" if rs > 50 else ("attention" if rs > 30 else "normal"))
    abnormal_module_cn = MODULE_ID_TO_CHINESE.get(status["main_abnormal_module"], status["main_abnormal_module"])
    abnormal_coupling_cn = format_coupling_text(status["main_abnormal_coupling"])
    level_labels = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}

    # Row 1: 总体状态
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card_3layer("综合风险分数", f"{rs:.1f}", "基于四模块加权融合", rs_status)
    with c2:
        render_kpi_card_3layer("当前预警等级", level_labels.get(risk_status, risk_status), "综合风险与事件规则判定", risk_status)
    with c3:
        render_kpi_card_3layer("健康指数", f"{hi:.1f}", "综合健康评估指标", hi_status)
    with c4:
        render_kpi_card_3layer("在线样本数", str(status["sample_count"]), "累计监测数据样本", "normal")

    # Row 2: 解释来源
    # 找主要贡献变量
    var_contribs = _compute_var_contribs(tuple(sorted(module_scores.items())))
    top_var_cn = var_contribs[0]["chinese_name"] if var_contribs else "无"
    top_var_module = MODULE_SHORT_CHINESE.get(var_contribs[0]["module"], "") if var_contribs else ""
    model_status_text = "PCA/IF/HI 已加载"

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        render_kpi_card_3layer("主异常模块", abnormal_module_cn, "评分最低的核心模块", "warning")
    with c6:
        render_kpi_card_3layer("主异常耦合关系", abnormal_coupling_cn, "残差最大的模块关系", "attention")
    with c7:
        render_kpi_card_3layer("主要贡献变量", top_var_cn, f"所属: {top_var_module}", "attention")
    with c8:
        render_kpi_card_3layer("当前模型状态", model_status_text, "PCA/IF/HI 模型运行状态", "normal")

    st.markdown("---")

    # ── Section 3: 系统状态摘要区 ──
    summary_data = ModuleScorer.compute_system_status_summary(status, df)
    render_system_status_summary_blocks(summary_data)

    st.markdown("---")

    # ── Section 4: 四模块领域模型关系图 ──
    sel_obj = st.session_state.selected_object
    selected_id = sel_obj.get("id", "state_maintenance")

    render_four_module_graph_svg(selected_id, module_scores)

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

    st.markdown(f"# {meta.chinese_name}")
    st.markdown(f"*{meta.description}*")

    col1, col2, col3 = st.columns(3)
    with col1:
        render_kpi_card("模块评分", f"{score:.1f}", status="normal" if score > 80 else ("attention" if score > 60 else "warning"))
    with col2:
        risk_level = ModuleScorer.determine_risk_level(100 - score)
        level_labels = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}
        render_kpi_card("风险等级", level_labels.get(risk_level, risk_level), status=risk_level)
    with col3:
        render_kpi_card("变量数", str(len(meta.variables)), status="normal")

    st.markdown("---")

    st.markdown("### 模块变量")
    from src.utils.config_loader import get_variable_by_module
    var_list = get_variable_by_module(module_type.value)
    if var_list:
        var_df = pd.DataFrame(var_list)
        st.dataframe(var_df[["standard_name", "chinese_name", "unit", "raw_tag", "data_type", "sampling_rate"]], width="stretch")

    st.markdown("### 模块特征趋势分析")
    st.caption(f"当前模块：{meta.chinese_name}")
    df = load_fused_features()
    if not df.empty:
        module_cols = [c for c in df.columns if c.startswith(f"{module_type.value}__")]
        if module_cols:
            st.dataframe(df[module_cols].tail(50), width="stretch")
            # 模块页面名映射
            _module_page_names = {
                "execution_control": "执行控制",
                "energy_input": "能量输入",
                "environmental_constraint": "环境约束",
                "state_maintenance": "状态维持",
            }
            page_name = _module_page_names.get(module_type.value, module_type.value)
            render_all_trend_groups(page_name, df[module_cols].tail(200), module_name=module_type.value, tail_n=0)
        else:
            st.info("该模块暂无特征数据")

    st.markdown("### 模块配置")
    st.markdown(f"- 模块类型: {module_type.value}")
    st.markdown(f"- 变量数量: {len(meta.variables)}")
    st.markdown("- 状态: 已启用")


# ════════════════════════════════════════════════════════════
# 数据接入页面
# ════════════════════════════════════════════════════════════
def render_data_page() -> None:
    st.markdown("# 数据接入")
    st.markdown("支持 Excel 历史数据导入和 DCS 实时数据连接。")

    tab1, tab2 = st.tabs(["Excel 导入", "DCS 连接"])

    with tab1:
        st.markdown("### Excel 数据导入")
        uploaded = st.file_uploader("上传 Excel 文件", type=["xlsx"], key="excel_upload")
        if uploaded is not None:
            df = pd.read_excel(uploaded, engine="openpyxl")
            st.dataframe(df.head(20), width="stretch")
            st.info(f"共 {len(df)} 行 × {len(df.columns)} 列")

        st.markdown("### 已导入数据")
        processed_path = ROOT / "data" / "processed" / "imported_data.csv"
        if processed_path.exists():
            df = load_csv(processed_path, index_col=0, parse_dates=True)
            st.dataframe(df.tail(20), width="stretch")
            st.info(f"共 {len(df)} 行 × {len(df.columns)} 列")
        else:
            st.warning("暂无已导入数据")

    with tab2:
        st.markdown("### DCS 实时数据连接")
        st.info("当前使用 MockDCSConnector 模拟实时数据流。")
        st.markdown("- 连接类型: Mock")
        st.markdown("- 数据源: data/processed/cleaned_data.csv")
        st.markdown("- 轮询间隔: 2.0s")
        st.markdown("- 缓冲区大小: 500")


# ════════════════════════════════════════════════════════════
# 特征分析页面
# ════════════════════════════════════════════════════════════
def render_feature_page() -> None:
    st.markdown("# 特征分析")
    df = load_fused_features()
    if df.empty:
        st.warning("暂无特征数据，请先运行特征构建脚本。")
        return

    st.info(f"融合特征: {df.shape[0]} 行 × {df.shape[1]} 列")

    tab1, tab2, tab3, tab4 = st.tabs(["执行控制", "能量输入", "环境约束", "状态维持"])
    tabs = [tab1, tab2, tab3, tab4]
    modules = ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]

    for tab, mod in zip(tabs, modules):
        with tab:
            cols = [c for c in df.columns if c.startswith(f"{mod}__")]
            if cols:
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

    st.info(f"模型结果: {len(df)} 条")
    render_all_trend_groups("模型训练", df.tail(200))


# ════════════════════════════════════════════════════════════
# 在线监测页面
# ════════════════════════════════════════════════════════════
def render_online_page() -> None:
    st.markdown("# 在线监测")
    st.info("当前使用 MockDCSConnector 模拟在线监测。")

    status = get_current_status()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card("风险分数", f"{status['risk_score']:.1f}", status="normal")
    with col2:
        hi = status['health_index']
        hi_status = "normal" if hi > 80 else ("attention" if hi > 60 else "warning")
        render_kpi_card("健康指数", f"{hi:.1f}", status=hi_status)
    with col3:
        render_kpi_card("样本数", str(status["sample_count"]), status="normal")
    with col4:
        level_labels = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}
        render_kpi_card("风险等级", level_labels.get(status["risk_level"], status["risk_level"]), status=status["risk_level"])

    st.markdown("---")

    st.markdown("### 四模块状态评分")
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
    df = load_model_results()
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

    if "risk_level" in df.columns:
        alarms = df[df["risk_level"].isin(["warning", "severe"])]
        st.info(f"共 {len(alarms)} 条预警记录")
        if not alarms.empty:
            display_cols = []
            for c in ["risk_score", "risk_level", "health_index", "pca_anomaly_score", "if_anomaly_score"]:
                if c in alarms.columns:
                    display_cols.append(c)
            st.dataframe(alarms[display_cols].tail(50), width="stretch")
        else:
            st.success("暂无预警记录，设备状态正常。")

    st.markdown("---")
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

    if "health_index" in df.columns:
        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card("平均健康指数", f"{df['health_index'].mean():.1f}", status="normal")
        with col2:
            render_kpi_card("最低健康指数", f"{df['health_index'].min():.1f}", status="warning")
        with col3:
            render_kpi_card("当前健康指数", f"{df['health_index'].iloc[-1]:.1f}", status="normal")

    render_all_trend_groups("健康趋势", df)


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
else:
    render_home_page()
