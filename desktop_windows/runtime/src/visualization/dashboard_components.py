"""Dashboard UI 组件 — 极简工业风格。

颜色仅使用：蓝(#4FC1FF) + 灰(#A7B0BD) + 红(#FF6B6B)
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from src.visualization.theme import (
    BG_CARD,
    BORDER_MAIN,
    TEXT_MAIN,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_BLUE,
    RISK_RED,
    FONT_FAMILY,
    FONT_MONO,
    STATUS_COLORS,
    BG_GRAPH_INNER,
)

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


def _status_to_color(status: str) -> str:
    """状态 → 颜色：severe 用红，其他全用蓝。"""
    if status == "severe":
        return RISK_RED
    return ACCENT_BLUE


def render_kpi_card(
    label: str,
    value: str,
    subtext: str = "",
    status: str = "normal",
) -> None:
    """渲染统一 KPI 卡片。

    极简风格：背景统一 #2A2D33，左侧色条仅蓝/红两色。
    """
    color = _status_to_color(status)
    st.markdown(
        f"""
        <div style="
            background: {BG_CARD};
            border: 1px solid {BORDER_MAIN};
            border-left: 3px solid {color};
            border-radius: 12px;
            padding: 18px 20px;
            height: 122px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: visible;
            box-sizing: border-box;
        ">
            <div style="
                font-size: 12px;
                color: {TEXT_SECONDARY};
                font-weight: 500;
                letter-spacing: 0.02em;
                font-family: {FONT_FAMILY};
                white-space: normal;
                word-break: break-word;
            ">{label}</div>
            <div style="
                font-size: 30px;
                line-height: 1.15;
                font-weight: 700;
                color: {color};
                font-family: {FONT_MONO};
                white-space: normal;
                word-break: break-word;
            ">{value}</div>
            {"<div style='font-size: 11px; color: " + TEXT_MUTED + "; line-height: 1.3; white-space: normal; word-break: break-word;'>" + subtext + "</div>" if subtext else "<div style='font-size: 11px;'>&nbsp;</div>"}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_coupling_text(coupling_str: str) -> str:
    """将耦合关系文本格式化为中文短文本。"""
    for sep in [" ↔ ", " ↔ ", " → ", " -> ", " - "]:
        if sep in coupling_str:
            parts = coupling_str.split(sep)
            if len(parts) == 2:
                src = MODULE_SHORT_CHINESE.get(parts[0].strip(), parts[0].strip())
                tgt = MODULE_SHORT_CHINESE.get(parts[1].strip(), parts[1].strip())
                return f"{src} → {tgt}"
    if coupling_str.strip() in MODULE_SHORT_CHINESE:
        return MODULE_SHORT_CHINESE[coupling_str.strip()]
    return coupling_str


def render_metric_card(
    title: str,
    value: str | float,
    delta: str | None = None,
    color: str | None = None,
) -> None:
    """渲染指标卡片（兼容旧接口）。"""
    if color is None:
        color = ACCENT_BLUE
    st.markdown(
        f"""
        <div style="
            background: {BG_CARD};
            border: 1px solid {BORDER_MAIN};
            border-radius: 12px;
            padding: 18px 20px;
            height: 122px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            overflow: visible;
            box-sizing: border-box;
        ">
            <div style="
                font-size: 12px;
                color: {TEXT_SECONDARY};
                font-weight: 500;
                letter-spacing: 0.02em;
                font-family: {FONT_FAMILY};
            ">{title}</div>
            <div style="
                font-size: 28px;
                font-weight: 700;
                color: {color};
                word-wrap: break-word;
                font-family: {FONT_MONO};
            ">{value}</div>
            {f'<div style="font-size: 11px; color: {TEXT_MUTED};">{delta}</div>' if delta else '<div style="font-size: 11px;">&nbsp;</div>'}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_risk_badge(level: str) -> str:
    """返回风险等级对应的 HTML 徽章。"""
    label_map = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}
    color = RISK_RED if level == "severe" else ACCENT_BLUE
    label = label_map.get(level, level)
    return (
        f'<span style="background:{color}1A; color:{color}; padding:4px 14px; '
        f'border-radius:4px; font-size:12px; font-weight:600; border:1px solid {color}44;'
        f'letter-spacing:0.05em;">{label}</span>'
    )


def render_module_score_bar(module_name: str, score: float, chinese_name: str) -> None:
    """渲染模块评分条。"""
    color = RISK_RED if score < 40 else ACCENT_BLUE

    st.markdown(
        f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 13px; color: {TEXT_SECONDARY}; font-family: {FONT_FAMILY};">{chinese_name}</span>
                <span style="font-size: 14px; color: {color}; font-weight: 600; font-family: {FONT_MONO};">{score:.1f}</span>
            </div>
            <div style="background: {BG_GRAPH_INNER}; border-radius: 3px; height: 6px; overflow: hidden;">
                <div style="background: {color}; width: {score}%; height: 100%; border-radius: 3px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alarm_item(alarm: dict[str, Any]) -> None:
    """渲染单条预警记录。"""
    level = alarm.get("level", "normal")
    color = RISK_RED if level == "severe" else ACCENT_BLUE
    st.markdown(
        f"""
        <div style="
            border-left: 3px solid {color};
            padding: 10px 14px;
            margin-bottom: 8px;
            background: {BG_CARD};
            border-radius: 0 8px 8px 0;
            border: 1px solid {BORDER_MAIN};
            border-left-color: {color};
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; color: {color}; font-size: 11px;
                             letter-spacing: 0.06em;
                             background: {color}15; padding: 2px 8px; border-radius: 3px;
                             font-family: {FONT_FAMILY};">{level.upper()}</span>
                <span style="font-size: 11px; color: {TEXT_MUTED}; font-family: {FONT_MONO};">{alarm.get('timestamp', '')}</span>
            </div>
            <div style="font-size: 13px; color: {TEXT_MAIN}; margin-top: 6px; line-height: 1.5;">{alarm.get('message', '')}</div>
            <div style="font-size: 11px; color: {TEXT_MUTED}; margin-top: 4px;">模块: {alarm.get('module', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
