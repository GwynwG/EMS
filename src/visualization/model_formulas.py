"""模型公式与元数据定义。

纯数据模块，定义所有模型的数学公式、参数、输入输出关系。
供"算法参考"页面渲染使用。
"""
from __future__ import annotations

from src.visualization.theme import (
    ACCENT_BLUE,
    RISK_RED,
    HEALTH_GREEN,
    WARN_AMBER,
    TEXT_MAIN,
    TEXT_SECONDARY,
    TEXT_MUTED,
    BG_CARD,
    FONT_MONO,
)

# ════════════════════════════════════════════════════════════
# 模型公式定义
# ════════════════════════════════════════════════════════════

MODEL_FORMULAS: dict[str, dict] = {
    "pca_monitor": {
        "name": "PCA 状态监测模型",
        "name_en": "PCA Monitor",
        "category": "多元统计过程监测",
        "description": "基于主成分分析的多元统计监测方法，通过降维提取主要变化模式，"
                      "利用 T² 和 SPE 两个统计量分别监测主成分空间和残差空间的异常。",
        "formulas": [
            {
                "label": "T² 统计量",
                "formula": "T² = Σᵢ (tᵢ² / λᵢ)",
                "desc": "主成分得分的加权平方和，反映样本在主成分空间中的偏离程度。"
                       "tᵢ 为第 i 主成分得分，λᵢ 为对应特征值（方差）。",
            },
            {
                "label": "SPE / Q 统计量",
                "formula": "SPE = ‖X - X̂‖² = Σⱼ (xⱼ - x̂ⱼ)²",
                "desc": "原始数据与 PCA 重构数据之间的欧氏距离平方，"
                       "反映主成分空间之外的变异程度。",
            },
            {
                "label": "异常分数",
                "formula": "score = max(T²/T²_th, SPE/SPE_th)",
                "desc": "将 T² 和 SPE 分别除以其阈值后取最大值。"
                       "score > 1.0 判定为异常。",
            },
        ],
        "config_params": {
            "n_components": "0.95（保留 95% 方差）",
            "whiten": "false",
            "anomaly_threshold_percentile": "99（训练集第 99 百分位）",
        },
        "inputs": ["标准化后的融合特征矩阵 X（~100 维）"],
        "outputs": ["T² 统计量", "SPE 统计量", "异常分数（0~∞）", "是否异常（0/1）", "贡献变量排名"],
    },
    "isolation_forest": {
        "name": "Isolation Forest 异常检测",
        "name_en": "Isolation Forest",
        "category": "集成学习异常检测",
        "description": "基于随机森林的无监督异常检测算法。通过随机分割特征空间构建隔离树，"
                      "异常点因分布稀疏而更容易被隔离（路径更短）。",
        "formulas": [
            {
                "label": "路径长度",
                "formula": "h(x) = 节点深度（从根到叶的边数）",
                "desc": "样本 x 在单棵隔离树中的路径长度。异常点路径更短。",
            },
            {
                "label": "异常分数（原始）",
                "formula": "s(x) = decision_function(x)",
                "desc": "sklearn 输出的原始决策函数值，负值越小越异常。",
            },
            {
                "label": "异常分数（归一化）",
                "formula": "score = 1 - (s - s_min) / (s_max - s_min)",
                "desc": "将原始分数归一化到 [0, 1]，1 表示最异常。",
            },
        ],
        "config_params": {
            "n_estimators": "200（隔离树数量）",
            "contamination": "0.05（预期异常比例 5%）",
            "max_samples": "auto（采样数 = min(256, 样本数)）",
            "random_state": "42",
        },
        "inputs": ["标准化后的融合特征矩阵 X"],
        "outputs": ["异常分数（0~1）", "是否异常（0/1）"],
    },
    "health_index": {
        "name": "健康指数计算器",
        "name_en": "Health Index",
        "category": "多源信息融合",
        "description": "将 PCA 异常分数、IF 异常分数、四模块健康评分和事件惩罚进行加权融合，"
                      "输出 0-100 的综合健康指数。数值越高代表系统状态越健康。",
        "formulas": [
            {
                "label": "健康指数",
                "formula": "HI = 0.25·(1-PCA)·100 + 0.25·(1-IF)·100 + 0.35·mean(modules) + 0.15·(1-event)·100",
                "desc": "四项加权融合：PCA 占 25%、IF 占 25%、模块均分占 35%、事件惩罚占 15%。",
            },
            {
                "label": "健康等级",
                "formula": "健康 ≥80 | 亚健康 ≥60 | 异常 ≥40 | 严重异常 <40",
                "desc": "四级健康状态划分。",
            },
        ],
        "weights": {
            "PCA 异常分数": 0.25,
            "IF 异常分数": 0.25,
            "模块健康均分": 0.35,
            "事件惩罚": 0.15,
        },
        "config_params": {
            "decay_factor": "0.95（指数衰减因子）",
        },
        "inputs": ["PCA 异常分数", "IF 异常分数", "四模块健康评分", "事件惩罚分数"],
        "outputs": ["健康指数（0~100）", "健康等级"],
    },
    "risk_fusion": {
        "name": "风险融合器",
        "name_en": "Risk Fusion",
        "category": "多层级风险评估",
        "description": "融合模块风险、全局异常分数、健康指数和事件惩罚，"
                      "输出综合风险分数和风险等级。支持定位主异常模块和主异常耦合关系。",
        "formulas": [
            {
                "label": "模块加权健康度",
                "formula": "W = Σ(module_score × weight) / Σ(weight)",
                "desc": "四模块评分按领域重要性加权平均。"
                       "状态维持权重最高（0.45），执行控制最低（0.15）。",
            },
            {
                "label": "模块风险",
                "formula": "module_risk = 100 - W",
                "desc": "模块健康度取反。",
            },
            {
                "label": "综合风险分数",
                "formula": "risk = 0.5·module_risk + 0.3·anomaly + 0.2·(100-HI) + event·10",
                "desc": "四项融合：模块风险 50%、异常分数 30%、健康缺失 20%、事件惩罚加成。",
            },
            {
                "label": "风险等级",
                "formula": "正常 <30 | 关注 <50 | 预警 <70 | 严重 ≥85",
                "desc": "四级风险状态划分。",
            },
        ],
        "module_weights": {
            "执行控制": 0.15,
            "能量输入": 0.20,
            "环境约束": 0.20,
            "状态维持": 0.45,
        },
        "config_params": {
            "risk_thresholds": "normal=30, attention=50, warning=70, severe=85",
        },
        "inputs": ["四模块评分", "PCA 异常分数", "IF 异常分数", "健康指数", "事件惩罚"],
        "outputs": ["风险分数（0~100）", "风险等级", "主异常模块", "主异常耦合关系"],
    },
    "module_level_pca": {
        "name": "模块级 PCA 监测",
        "name_en": "Module-Level PCA",
        "category": "分域独立监测",
        "description": "对每个模块的特征子集独立训练 PCA 模型，"
                      "输出各模块的独立健康评分。与全局 PCA 互补，提供模块级诊断粒度。",
        "formulas": [
            {
                "label": "模块异常分数",
                "formula": "mod_anomaly = max(T²_mod/T²_th, SPE_mod/SPE_th)",
                "desc": "与全局 PCA 相同的 T²/SPE 方法，但仅使用该模块的特征子集。",
            },
            {
                "label": "模块健康评分",
                "formula": "mod_score = max(0, 100 - anomaly × 20)",
                "desc": "将异常分数映射到 0-100 分，异常越大分越低。",
            },
        ],
        "config_params": {},
        "inputs": ["各模块特征子集"],
        "outputs": ["四模块独立健康评分"],
    },
}


# ════════════════════════════════════════════════════════════
# 模型数据流定义（用于桑基图）
# ════════════════════════════════════════════════════════════

MODEL_FLOW_NODES = [
    "原始特征（29 变量）",     # 0
    "特征工程",               # 1
    "PCA 监测模型",           # 2
    "Isolation Forest",       # 3
    "模块级 PCA",             # 4
    "事件特征提取",           # 5
    "健康指数计算",           # 6
    "风险融合",               # 7
    "诊断与预警",             # 8
]

MODEL_FLOW_LINKS = [
    # source, target, value, color
    (0, 1, 30, ACCENT_BLUE),   # 原始特征 → 特征工程
    (1, 2, 10, ACCENT_BLUE),   # 特征工程 → PCA
    (1, 3, 8, ACCENT_BLUE),    # 特征工程 → IF
    (1, 4, 7, ACCENT_BLUE),    # 特征工程 → 模块 PCA
    (1, 5, 5, ACCENT_BLUE),    # 特征工程 → 事件特征
    (2, 6, 5, ACCENT_BLUE),    # PCA → 健康指数
    (3, 6, 5, ACCENT_BLUE),    # IF → 健康指数
    (4, 6, 5, ACCENT_BLUE),    # 模块 PCA → 健康指数
    (5, 6, 3, ACCENT_BLUE),    # 事件 → 健康指数
    (2, 7, 4, ACCENT_BLUE),    # PCA → 风险融合
    (6, 7, 8, ACCENT_BLUE),    # 健康指数 → 风险融合
    (7, 8, 12, RISK_RED),      # 风险融合 → 诊断预警
]


# ════════════════════════════════════════════════════════════
# 公式渲染辅助
# ════════════════════════════════════════════════════════════

def render_formula_card_html(model_key: str) -> str:
    """返回单个模型的公式卡片 HTML。"""
    info = MODEL_FORMULAS.get(model_key)
    if not info:
        return ""

    formulas_html = ""
    for f in info["formulas"]:
        formulas_html += f"""
        <div style="margin-bottom:12px; padding:10px 14px; background:{BG_CARD};
                    border-radius:8px; border-left:3px solid {ACCENT_BLUE};">
            <div style="color:{TEXT_SECONDARY}; font-size:13px; margin-bottom:4px;">{f['label']}</div>
            <code style="font-family:{FONT_MONO}; font-size:15px; color:{ACCENT_BLUE};
                         background:rgba(0,0,0,0.2); padding:3px 8px; border-radius:4px;">
                {f['formula']}
            </code>
            <div style="color:{TEXT_MUTED}; font-size:12px; margin-top:6px; line-height:1.6;">{f['desc']}</div>
        </div>"""

    # 权重展示
    weights_html = ""
    weights = info.get("weights") or info.get("module_weights")
    if weights:
        items = "".join(
            f'<span style="display:inline-block; margin:2px 6px; padding:2px 10px; '
            f'background:rgba(96,165,250,0.1); border-radius:12px; font-size:12px; '
            f'color:{TEXT_SECONDARY};">{k}: <b style="color:{ACCENT_BLUE};">{v}</b></span>'
            for k, v in weights.items()
        )
        weights_html = f"""
        <div style="margin-top:8px; padding:8px 12px; background:{BG_CARD};
                    border-radius:8px; border:1px solid rgba(96,165,250,0.15);">
            <div style="color:{TEXT_MUTED}; font-size:12px; margin-bottom:4px;">权重配置</div>
            <div>{items}</div>
        </div>"""

    # 参数展示
    params_html = ""
    params = info.get("config_params", {})
    if params:
        rows = "".join(
            f'<tr><td style="padding:3px 10px; color:{TEXT_MUTED}; font-size:12px;">{k}</td>'
            f'<td style="padding:3px 10px; color:{TEXT_SECONDARY}; font-size:12px; font-family:{FONT_MONO};">{v}</td></tr>'
            for k, v in params.items()
        )
        params_html = f"""
        <div style="margin-top:8px; padding:8px 12px; background:{BG_CARD};
                    border-radius:8px; border:1px solid rgba(255,255,255,0.05);">
            <div style="color:{TEXT_MUTED}; font-size:12px; margin-bottom:4px;">配置参数</div>
            <table style="width:100%;">{rows}</table>
        </div>"""

    return f"""
    <div style="padding:16px; background:rgba(53,59,69,0.5); border-radius:10px;
                border:1px solid rgba(96,165,250,0.12); margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
            <span style="font-size:16px; font-weight:600; color:{TEXT_MAIN};">{info['name']}</span>
            <span style="font-size:11px; color:{TEXT_MUTED}; padding:2px 8px;
                         background:{BG_CARD}; border-radius:10px;">{info['category']}</span>
        </div>
        <div style="color:{TEXT_SECONDARY}; font-size:13px; line-height:1.7; margin-bottom:14px;">
            {info['description']}
        </div>
        {formulas_html}
        {weights_html}
        {params_html}
    </div>"""


def render_all_formula_cards() -> None:
    """渲染所有模型的公式卡片。"""
    import streamlit as st
    for key in MODEL_FORMULAS:
        st.markdown(render_formula_card_html(key), unsafe_allow_html=True)
