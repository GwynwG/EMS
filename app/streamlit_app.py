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
    format_coupling_text,
    MODULE_ID_TO_CHINESE,
    MODULE_SHORT_CHINESE,
    STATUS_COLORS,
)

# ── 页面配置 ──
st.set_page_config(
    page_title="设备状态监测与智能预警系统",
    page_icon="⚙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 全局深色工业主题 CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');

/* ── 全局背景 ── */
.stApp {
    background: #0B1120 !important;
    color: #E2E8F0 !important;
}
[data-testid="stAppViewContainer"] {
    background: #0B1120 !important;
}
[data-testid="stHeader"] {
    background: rgba(11,17,32,0.8) !important;
    backdrop-filter: blur(12px);
}

/* ── 侧边栏 ── */
[data-testid="stSidebar"] {
    background: #0F1729 !important;
    border-right: 1px solid #1E2D4A;
}
[data-testid="stSidebar"] [data-testid="stMarkdown"] h1,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h2,
[data-testid="stSidebar"] [data-testid="stMarkdown"] h3 {
    color: #E2E8F0 !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #151D2E !important;
    color: #94A3B8 !important;
    border: 1px solid #1E2D4A !important;
    border-radius: 6px !important;
    margin-bottom: 2px;
    transition: all 0.2s ease;
    font-family: 'Fira Sans', sans-serif;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #1C2640 !important;
    color: #22D3EE !important;
    border-color: #22D3EE44 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #0E2A3D, #163350) !important;
    color: #22D3EE !important;
    border-color: #22D3EE !important;
    box-shadow: 0 0 12px rgba(34,211,238,0.15);
}

/* ── 主内容区标题 ── */
[data-testid="stMarkdownContainer"] h1 {
    color: #F1F5F9 !important;
    font-family: 'Fira Sans', sans-serif;
    font-weight: 600;
    letter-spacing: -0.02em;
}
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: #CBD5E1 !important;
    font-family: 'Fira Sans', sans-serif;
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #94A3B8 !important;
}
[data-testid="stMarkdownContainer"] strong {
    color: #E2E8F0 !important;
}

/* ── 分隔线 ── */
hr {
    border-color: #1E2D4A !important;
    opacity: 0.6;
}

/* ── 按钮通用 ── */
.stButton > button {
    font-family: 'Fira Sans', sans-serif !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #0E2A3D, #163350) !important;
    color: #22D3EE !important;
    border: 1px solid #22D3EE !important;
    box-shadow: 0 0 16px rgba(34,211,238,0.12);
}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="stBaseButton-secondary"] {
    background: #151D2E !important;
    color: #8B9DC3 !important;
    border: 1px solid #1E2D4A !important;
}
.stButton > button:hover {
    border-color: #22D3EE88 !important;
    box-shadow: 0 0 12px rgba(34,211,238,0.1);
}

/* ── Selectbox / Input ── */
[data-testid="stSelectbox"] > div > div {
    background: #151D2E !important;
    border-color: #2A3650 !important;
    color: #E2E8F0 !important;
}
[data-testid="stTextInput"] > div > div > input {
    background: #151D2E !important;
    border-color: #2A3650 !important;
    color: #E2E8F0 !important;
}

/* ── DataFrame / Table ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1E2D4A;
    border-radius: 8px;
    overflow: hidden;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0F1729;
    border-radius: 8px;
    padding: 4px;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #8B9DC3 !important;
    border-radius: 6px;
    font-family: 'Fira Sans', sans-serif;
}
.stTabs [aria-selected="true"] {
    background: #1C2640 !important;
    color: #22D3EE !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0B1120; }
::-webkit-scrollbar-thumb { background: #2A3650; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3B4D6B; }

/* ── Plotly / 图表背景修正 ── */
.stPlotlyChart, .stPyplot {
    background: #0F1729 !important;
    border-radius: 8px;
    padding: 8px;
}
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
def update_selected_object(sel_type: str, sel_id: str) -> None:
    """统一更新选中对象状态。"""
    st.session_state.selected_object = {"type": sel_type, "id": sel_id}

    if sel_id in MODULE_IDS:
        st.session_state.selected_module = sel_id
        st.session_state.selected_panel_tab = sel_id
        st.session_state.selected_relation = None
    elif sel_id == "diagnosis_layer":
        st.session_state.selected_panel_tab = "diagnosis_layer"
        st.session_state.selected_relation = None
    elif sel_id == "coupling_residual":
        st.session_state.selected_panel_tab = "coupling_residual"
        st.session_state.selected_relation = "coupling_residual"
    elif sel_id == "model_residual":
        st.session_state.selected_panel_tab = "model_residual"
        st.session_state.selected_relation = "model_residual"
    elif sel_id == "intelligent_model":
        st.session_state.selected_panel_tab = "intelligent_model"
        st.session_state.selected_relation = "intelligent_model"
    elif sel_type == "edge":
        st.session_state.selected_relation = sel_id
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
    """渲染节点详情。"""
    detail = get_module_detail(node_id, status["module_scores"])
    st.markdown(f"**{detail.get('name', node_id)}**")
    st.caption(detail.get("description", ""))
    if "score" in detail:
        st.metric("模块评分", f"{detail['score']:.1f}")
    if "variables" in detail:
        st.markdown(f"**关键变量 ({len(detail['variables'])}):**")
        for v in detail["variables"][:5]:
            st.markdown(f"- {v}")
    if "risk_level" in detail:
        st.markdown(render_risk_badge(detail["risk_level"]), unsafe_allow_html=True)

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
    """渲染边详情。"""
    parts = edge_id.split("__")
    if len(parts) == 2:
        edge_detail = get_edge_detail(parts[0], parts[1], graph)
        st.markdown(f"**{edge_detail.get('name', '')}**")
        src_cn = MODULE_SHORT_CHINESE.get(edge_detail.get("source", ""), edge_detail.get("source", ""))
        tgt_cn = MODULE_SHORT_CHINESE.get(edge_detail.get("target", ""), edge_detail.get("target", ""))
        st.markdown(f"起点: {src_cn}")
        st.markdown(f"终点: {tgt_cn}")
        st.markdown(f"耦合强度: {edge_detail.get('coupling_strength', 0):.2f}")
        st.markdown(f"残差水平: {edge_detail.get('residual_level', 0):.2f}")
        if edge_detail.get("description"):
            st.caption(edge_detail["description"])
    else:
        st.warning("无法解析边信息")


def render_coupling_detail(coupling_id: str) -> None:
    """渲染耦合残差详情。"""
    st.markdown("**复杂耦合/残差**")
    st.caption("多源耦合残差处理模块，整合各模块间的耦合效应残差。")
    st.markdown("- 类型: 耦合残差处理")
    st.markdown("- 来源: 执行控制、能量输入、环境约束")
    st.markdown("- 输出: 耦合残差特征 → 智能补偿模型")


def render_residual_detail(residual_id: str) -> None:
    """渲染模型残差详情。"""
    st.markdown("**模型残差**")
    st.caption("基础统计模型（PCA/IF）的残差输出。")
    st.markdown("- 类型: 统计模型残差")
    st.markdown("- 来源: PCA 监测模型 / Isolation Forest")
    st.markdown("- 输出: 残差特征 → 智能补偿模型")


def render_intelligent_model_detail() -> None:
    """渲染智能补偿模型详情。"""
    st.markdown("**智能补偿模型**")
    st.caption("基于 XGBoost / Autoencoder 的智能异常补偿。")
    st.markdown("- 模型类型: XGBoost / Autoencoder")
    st.markdown("- 输入特征: 四模块融合特征 + 耦合残差 + 模型残差")
    st.markdown("- 输出: 异常补偿分数")
    st.markdown("- 状态: 预留接口")


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
    st.markdown("""
    <div style="padding: 8px 0 16px 0;">
        <div style="font-size: 13px; color: #4A5568; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 4px;">SYSTEM</div>
        <div style="font-size: 18px; font-weight: 600; color: #E2E8F0; font-family: 'Fira Sans', sans-serif;">设备监测系统</div>
        <div style="font-size: 11px; color: #22D3EE; margin-top: 2px; font-family: 'Fira Code', monospace;">EQUIPMENT MONITORING</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    for page in PAGES:
        if st.sidebar.button(page, key=f"nav_btn_{page}", width="stretch"):
            st.session_state.current_page = page
            st.rerun()
    st.markdown("---")
    st.caption("v1.0.0 | 四模块领域模型")


# ════════════════════════════════════════════════════════════
# 首页 - 四模块监测驾驶舱
# ════════════════════════════════════════════════════════════
def render_home_page() -> None:
    status = get_current_status()

    st.markdown("""
    <div style="margin-bottom: 24px;">
        <div style="font-size: 11px; color: #22D3EE; text-transform: uppercase; letter-spacing: 0.12em; font-family: 'Fira Code', monospace; margin-bottom: 4px;">
            SYSTEM DASHBOARD
        </div>
        <div style="font-size: 28px; font-weight: 700; color: #F1F5F9; font-family: 'Fira Sans', sans-serif; letter-spacing: -0.02em;">
            特种材料制备设备状态监测与智能预警系统
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 顶部 KPI 卡片 ──
    risk_status = status["risk_level"]
    hi = status["health_index"]
    hi_status = "normal" if hi > 80 else ("attention" if hi > 60 else ("warning" if hi > 40 else "severe"))
    abnormal_module_cn = MODULE_ID_TO_CHINESE.get(status["main_abnormal_module"], status["main_abnormal_module"])
    abnormal_coupling_cn = format_coupling_text(status["main_abnormal_coupling"])

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        rs = status["risk_score"]
        rs_status = "severe" if rs > 70 else ("warning" if rs > 50 else ("attention" if rs > 30 else "normal"))
        render_kpi_card("综合风险分数", f"{rs:.1f}", status=rs_status)
    with col2:
        level_labels = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}
        render_kpi_card("当前预警等级", level_labels.get(risk_status, risk_status), status=risk_status)
    with col3:
        render_kpi_card("健康指数", f"{hi:.1f}", status=hi_status)
    with col4:
        render_kpi_card("在线样本数", str(status["sample_count"]), status="normal")
    with col5:
        render_kpi_card("主异常模块", abnormal_module_cn, status="warning")
    with col6:
        render_kpi_card("主耦合异常", abnormal_coupling_cn, status="attention")

    st.markdown("---")

    # ── 中部：四模块交互拓扑图（纯 SVG）──
    st.markdown("""
    <div style="margin-bottom: 8px;">
        <span style="font-size: 14px; color: #64748B; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Fira Sans', sans-serif;">拓扑示意图</span>
    </div>
    """, unsafe_allow_html=True)
    graph = CouplingGraph()

    sel_obj = st.session_state.selected_object
    selected_id = sel_obj.get("id", "state_maintenance")

    render_four_module_graph_svg(selected_id, status["module_scores"])

    # ── 图下方按钮组 ──
    st.markdown("""
    <div style="margin: 12px 0 8px 0;">
        <span style="font-size: 12px; color: #4A5568; text-transform: uppercase; letter-spacing: 0.08em;">选择监测对象</span>
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
                update_selected_object(btn_cfg["type"], btn_id)
                st.rerun()

    st.markdown("---")

    # ── 下部：详情面板 + 趋势图 + 预警列表 ──
    col_detail, col_trend, col_alarm = st.columns([1, 1.5, 1])

    with col_detail:
        st.markdown("""
        <div style="margin-bottom: 12px;">
            <span style="font-size: 11px; color: #22D3EE; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Fira Code', monospace;">Detail</span>
            <div style="font-size: 16px; color: #CBD5E1; font-weight: 600; margin-top: 2px;">选中对象详情</div>
        </div>
        """, unsafe_allow_html=True)
        render_selected_object_detail(status, graph)

    with col_trend:
        st.markdown("""
        <div style="margin-bottom: 12px;">
            <span style="font-size: 11px; color: #22D3EE; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Fira Code', monospace;">Trend</span>
            <div style="font-size: 16px; color: #CBD5E1; font-weight: 600; margin-top: 2px;">趋势图</div>
        </div>
        """, unsafe_allow_html=True)
        df = load_model_results()
        if not df.empty:
            trend_metric = st.selectbox(
                "选择指标",
                ["health_index", "risk_score", "pca_anomaly_score", "if_anomaly_score"],
                key="trend_metric_select",
            )
            if trend_metric in df.columns:
                st.line_chart(df[trend_metric].tail(200))
            else:
                st.info("该指标暂无数据")
        else:
            st.info("暂无模型结果数据，请先运行训练脚本")

    with col_alarm:
        st.markdown("""
        <div style="margin-bottom: 12px;">
            <span style="font-size: 11px; color: #EF4444; text-transform: uppercase; letter-spacing: 0.08em; font-family: 'Fira Code', monospace;">Alerts</span>
            <div style="font-size: 16px; color: #CBD5E1; font-weight: 600; margin-top: 2px;">最新预警</div>
        </div>
        """, unsafe_allow_html=True)
        alarm_service = AlarmService()
        if not df.empty:
            last = df.iloc[-1]
            if last.get("risk_level") in ("warning", "severe"):
                render_alarm_item({
                    "level": last.get("risk_level", "normal"),
                    "message": f"风险分数 {last.get('risk_score', 0):.1f}",
                    "module": MODULE_SHORT_CHINESE.get(status["main_abnormal_module"], status["main_abnormal_module"]),
                    "timestamp": str(df.index[-1]),
                })
            if last.get("pca_anomaly_score", 0) > 1.0:
                render_alarm_item({
                    "level": "attention",
                    "message": f"PCA 异常分数 {last.get('pca_anomaly_score', 0):.2f}",
                    "module": "状态维持",
                    "timestamp": str(df.index[-1]),
                })
        st.caption("预警基于模型输出和规则引擎")


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

    st.markdown("### 模块特征数据")
    df = load_fused_features()
    if not df.empty:
        module_cols = [c for c in df.columns if c.startswith(f"{module_type.value}__")]
        if module_cols:
            st.dataframe(df[module_cols].tail(50), width="stretch")
            st.line_chart(df[module_cols].tail(200))
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
                st.line_chart(df[cols].tail(200))
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

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### PCA 监测模型")
        if "pca_anomaly_score" in df.columns:
            st.line_chart(df["pca_anomaly_score"].tail(200))
        if "pca_t2" in df.columns:
            st.line_chart(df["pca_t2"].tail(200))

    with col2:
        st.markdown("### Isolation Forest")
        if "if_anomaly_score" in df.columns:
            st.line_chart(df["if_anomaly_score"].tail(200))

    st.markdown("### 健康指数趋势")
    if "health_index" in df.columns:
        st.line_chart(df["health_index"].tail(200))

    st.markdown("### 风险分数趋势")
    if "risk_score" in df.columns:
        st.line_chart(df["risk_score"].tail(200))


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
        st.markdown("### 健康指数历史趋势")
        st.line_chart(df["health_index"])

        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card("平均健康指数", f"{df['health_index'].mean():.1f}", status="normal")
        with col2:
            render_kpi_card("最低健康指数", f"{df['health_index'].min():.1f}", status="warning")
        with col3:
            render_kpi_card("当前健康指数", f"{df['health_index'].iloc[-1]:.1f}", status="normal")

    st.markdown("### 模块评分趋势")
    module_scores_data = {}
    for mod in ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]:
        cols = [c for c in df.columns if c.startswith(f"{mod}__")]
        if cols:
            module_scores_data[mod] = df[cols].apply(
                lambda row: ModuleScorer.compute_module_score(row), axis=1
            )
    if module_scores_data:
        scores_df = pd.DataFrame(module_scores_data)
        st.line_chart(scores_df)


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
