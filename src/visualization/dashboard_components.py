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

# ── 风险等级颜色 (工业深色主题) ──
STATUS_COLORS: dict[str, str] = {
    "normal": "#10B981",
    "attention": "#F59E0B",
    "warning": "#F97316",
    "severe": "#EF4444",
}

STATUS_BG: dict[str, str] = {
    "normal": "rgba(16,185,129,0.10)",
    "attention": "rgba(245,158,11,0.10)",
    "warning": "rgba(249,115,22,0.10)",
    "severe": "rgba(239,68,68,0.10)",
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
            background: #111827;
            border: 1px solid #1E2D4A;
            border-left: 3px solid {color};
            border-radius: 8px;
            padding: 16px 18px;
            text-align: center;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            box-shadow: 0 4px 16px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.03);
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute; top: 0; left: 0; right: 0; height: 1px;
                background: linear-gradient(90deg, transparent, {color}33, transparent);
            "></div>
            <div style="
                font-size: 11px;
                color: #64748B;
                margin-bottom: 8px;
                word-wrap: break-word;
                width: 100%;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-family: 'Fira Sans', sans-serif;
            ">{label}</div>
            <div style="
                font-size: 28px;
                font-weight: 700;
                color: {color};
                line-height: 1.2;
                word-wrap: break-word;
                width: 100%;
                font-family: 'Fira Code', 'Fira Sans', monospace;
                text-shadow: 0 0 20px {color}33;
            ">{value}</div>
            {"<div style='font-size: 11px; color: #64748B; margin-top: 6px; word-wrap: break-word; width: 100%;'>" + subtext + "</div>" if subtext else ""}
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
    color: str = "#22D3EE",
) -> None:
    """渲染指标卡片（兼容旧接口）。"""
    st.markdown(
        f"""
        <div style="background: #111827;
                     border: 1px solid #1E2D4A; border-radius: 8px;
                     padding: 16px; text-align: center;
                     min-height: 120px; display: flex; flex-direction: column;
                     justify-content: center;
                     box-shadow: 0 4px 16px rgba(0,0,0,0.3);">
            <div style="font-size: 11px; color: #64748B; margin-bottom: 6px;
                        text-transform: uppercase; letter-spacing: 0.08em;">{title}</div>
            <div style="font-size: 26px; font-weight: 700; color: {color};
                        word-wrap: break-word; font-family: 'Fira Code', monospace;
                        text-shadow: 0 0 20px {color}33;">{value}</div>
            {f'<div style="font-size: 11px; color: #64748B; margin-top: 4px;">{delta}</div>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_risk_badge(level: str) -> str:
    """返回风险等级对应的 HTML 徽章。"""
    colors = {
        "normal": ("#10B981", "正常"),
        "attention": ("#F59E0B", "关注"),
        "warning": ("#F97316", "预警"),
        "severe": ("#EF4444", "严重"),
    }
    color, label = colors.get(level, ("#64748B", level))
    return (
        f'<span style="background:{color}1A; color:{color}; padding:4px 14px; '
        f'border-radius:4px; font-size:12px; font-weight:600; border:1px solid {color}44;'
        f'letter-spacing:0.05em; text-transform:uppercase;">{label}</span>'
    )


def render_module_score_bar(module_name: str, score: float, chinese_name: str) -> None:
    """渲染模块评分条。"""
    if score >= 80:
        color = "#10B981"
    elif score >= 60:
        color = "#F59E0B"
    elif score >= 40:
        color = "#F97316"
    else:
        color = "#EF4444"

    st.markdown(
        f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 12px; color: #8B9DC3; letter-spacing: 0.02em;">{chinese_name}</span>
                <span style="font-size: 13px; color: {color}; font-weight: 600; font-family: 'Fira Code', monospace;">{score:.1f}</span>
            </div>
            <div style="background: #1A2332; border-radius: 3px; height: 6px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, {color}88, {color}); width: {score}%; height: 100%; border-radius: 3px;
                            transition: width 0.6s ease; box-shadow: 0 0 8px {color}44;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alarm_item(alarm: dict[str, Any]) -> None:
    """渲染单条预警记录。"""
    level_colors = {
        "normal": "#10B981",
        "attention": "#F59E0B",
        "warning": "#F97316",
        "severe": "#EF4444",
    }
    color = level_colors.get(alarm.get("level", "normal"), "#64748B")
    st.markdown(
        f"""
        <div style="border-left: 3px solid {color}; padding: 10px 14px;
                     margin-bottom: 8px; background: #111827; border-radius: 0 6px 6px 0;
                     border: 1px solid #1E2D4A; border-left-color: {color};
                     box-shadow: 0 2px 8px rgba(0,0,0,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; color: {color}; font-size: 11px;
                             text-transform: uppercase; letter-spacing: 0.06em;
                             background: {color}15; padding: 2px 8px; border-radius: 3px;">{alarm.get('level', '').upper()}</span>
                <span style="font-size: 11px; color: #4A5568; font-family: 'Fira Code', monospace;">{alarm.get('timestamp', '')}</span>
            </div>
            <div style="font-size: 13px; color: #CBD5E1; margin-top: 6px; line-height: 1.5;">{alarm.get('message', '')}</div>
            <div style="font-size: 11px; color: #64748B; margin-top: 4px;">模块: {alarm.get('module', '')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
