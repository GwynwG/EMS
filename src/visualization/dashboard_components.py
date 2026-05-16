"""Dashboard UI 组件。"""
from __future__ import annotations

from typing import Any

import streamlit as st

# ── 模块 ID → 中文名映射 ──
MODULE_ID_TO_CHINESE: dict[str, str] = {
    "execution_control": "执行控制模块",
    "energy_input": "能量输入模块",
    "environmental_constraint": "环境约束模块",
    "state_maintenance": "状态维持模块",
    "coupling_residual": "复杂耦合/残差",
    "model_residual": "模型残差",
    "intelligent_model": "智能补偿模型",
    "diagnosis_layer": "诊断层",
}

MODULE_SHORT_CHINESE: dict[str, str] = {
    "execution_control": "执行控制",
    "energy_input": "能量输入",
    "environmental_constraint": "环境约束",
    "state_maintenance": "状态维持",
    "coupling_residual": "耦合残差",
    "model_residual": "模型残差",
    "intelligent_model": "智能模型",
    "diagnosis_layer": "诊断层",
}

# ── 风险等级颜色 ──
STATUS_COLORS: dict[str, str] = {
    "normal": "#2E7D32",
    "attention": "#F9A825",
    "warning": "#EF6C00",
    "severe": "#C62828",
}

STATUS_BG: dict[str, str] = {
    "normal": "rgba(46,125,50,0.12)",
    "attention": "rgba(249,168,37,0.12)",
    "warning": "rgba(239,108,0,0.12)",
    "severe": "rgba(198,40,40,0.12)",
}


def render_kpi_card(
    label: str,
    value: str,
    subtext: str = "",
    status: str = "normal",
) -> None:
    """渲染统一 KPI 卡片。

    三层文字：label(小标题) / value(核心值) / subtext(解释)
    固定高度 120px，不允许溢出。
    """
    color = STATUS_COLORS.get(status, "#1565C0")
    bg = STATUS_BG.get(status, "rgba(21,101,192,0.10)")
    st.markdown(
        f"""
        <div style="
            background: {bg};
            border: 1px solid {color}44;
            border-left: 4px solid {color};
            border-radius: 10px;
            padding: 14px 16px;
            text-align: center;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        ">
            <div style="
                font-size: 12px;
                color: #9e9e9e;
                margin-bottom: 6px;
                word-wrap: break-word;
                width: 100%;
            ">{label}</div>
            <div style="
                font-size: 24px;
                font-weight: 700;
                color: {color};
                line-height: 1.2;
                word-wrap: break-word;
                width: 100%;
            ">{value}</div>
            {"<div style='font-size: 11px; color: #78909C; margin-top: 4px; word-wrap: break-word; width: 100%;'>" + subtext + "</div>" if subtext else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_coupling_text(coupling_str: str) -> str:
    """将耦合关系文本格式化为中文短文本。

    输入可能是: "state_maintenance ↔ execution_control" 或英文 id 对。
    输出: "状态维持 → 执行控制"
    """
    # 尝试解析 "id ↔ id" 或 "id → id" 格式
    for sep in [" ↔ ", " ↔ ", " → ", " -> ", " - "]:
        if sep in coupling_str:
            parts = coupling_str.split(sep)
            if len(parts) == 2:
                src = MODULE_SHORT_CHINESE.get(parts[0].strip(), parts[0].strip())
                tgt = MODULE_SHORT_CHINESE.get(parts[1].strip(), parts[1].strip())
                return f"{src} → {tgt}"
    # 如果整个字符串是一个已知模块 id
    if coupling_str.strip() in MODULE_SHORT_CHINESE:
        return MODULE_SHORT_CHINESE[coupling_str.strip()]
    return coupling_str


def render_metric_card(
    title: str,
    value: str | float,
    delta: str | None = None,
    color: str = "#1565C0",
) -> None:
    """渲染指标卡片（兼容旧接口）。"""
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, {color}18, {color}08);
                     border: 1px solid {color}44; border-radius: 12px;
                     padding: 16px; text-align: center;
                     min-height: 120px; display: flex; flex-direction: column;
                     justify-content: center;
                     box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
            <div style="font-size: 12px; color: #aaa; margin-bottom: 4px;">{title}</div>
            <div style="font-size: 24px; font-weight: bold; color: {color};
                        word-wrap: break-word;">{value}</div>
            {f'<div style="font-size: 11px; color: #888; margin-top: 4px;">{delta}</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_risk_badge(level: str) -> str:
    """返回风险等级对应的 HTML 徽章。"""
    colors = {
        "normal": ("#00C853", "正常"),
        "attention": ("#FFD600", "关注"),
        "warning": ("#FF6D00", "预警"),
        "severe": ("#D50000", "严重"),
    }
    color, label = colors.get(level, ("#666", level))
    return (
        f'<span style="background:{color}; color:#fff; padding:4px 12px; '
        f'border-radius:16px; font-size:13px; font-weight:bold;">{label}</span>'
    )


def render_module_score_bar(module_name: str, score: float, chinese_name: str) -> None:
    """渲染模块评分条。"""
    if score >= 80:
        color = "#00C853"
    elif score >= 60:
        color = "#FFD600"
    elif score >= 40:
        color = "#FF6D00"
    else:
        color = "#D50000"

    st.markdown(
        f"""
        <div style="margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                <span style="font-size: 13px; color: #ccc;">{chinese_name}</span>
                <span style="font-size: 13px; color: {color}; font-weight: bold;">{score:.1f}</span>
            </div>
            <div style="background: #1a2332; border-radius: 4px; height: 8px;">
                <div style="background: {color}; width: {score}%; height: 100%; border-radius: 4px;
                            transition: width 0.5s ease;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alarm_item(alarm: dict[str, Any]) -> None:
    """渲染单条预警记录。"""
    level_colors = {
        "normal": "#00C853",
        "attention": "#FFD600",
        "warning": "#FF6D00",
        "severe": "#D50000",
    }
    color = level_colors.get(alarm.get("level", "normal"), "#666")
    st.markdown(
        f"""
        <div style="border-left: 3px solid {color}; padding: 8px 12px;
                     margin-bottom: 6px; background: {color}11; border-radius: 0 8px 8px 0;">
            <div style="display: flex; justify-content: space-between;">
                <span style="font-weight: bold; color: {color};">{alarm.get('level', '').upper()}</span>
                <span style="font-size: 12px; color: #888;">{alarm.get('timestamp', '')}</span>
            </div>
            <div style="font-size: 14px; color: #ddd; margin-top: 4px;">{alarm.get('message', '')}</div>
            <div style="font-size: 12px; color: #aaa; margin-top: 2px;">模块: {alarm.get('module', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
