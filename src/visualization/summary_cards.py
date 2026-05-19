"""系统状态摘要区块组件。

提供数据链路、模型状态、风险来源、推荐关注 4 个摘要区块的渲染。
"""
from __future__ import annotations

import streamlit as st

from src.visualization.theme import (
    BG_CARD,
    BG_SUMMARY_BLOCK,
    BORDER_SUMMARY,
    BORDER_MAIN,
    TEXT_MAIN,
    TEXT_SECONDARY,
    TEXT_MUTED,
    ACCENT_BLUE,
    RISK_RED,
    FONT_FAMILY,
    FONT_MONO,
)


def _summary_block_wrapper(title: str, content_html: str) -> None:
    """统一的摘要区块容器。"""
    st.markdown(
        f"""
        <div style="
            background: {BG_SUMMARY_BLOCK};
            border: 1px solid {BORDER_SUMMARY};
            border-radius: 10px;
            padding: 14px 16px;
            min-height: 160px;
        ">
            <div style="
                font-size: 13px;
                font-weight: 600;
                color: {TEXT_MAIN};
                font-family: {FONT_FAMILY};
                margin-bottom: 10px;
                padding-bottom: 8px;
                border-bottom: 1px solid {BORDER_SUMMARY};
            ">{title}</div>
            {content_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _item_line(label: str, value: str, value_color: str = TEXT_MAIN) -> str:
    """单行项目。"""
    return (
        f'<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">'
        f'<span style="font-size: 12px; color: {TEXT_SECONDARY}; font-family: {FONT_FAMILY};">{label}</span>'
        f'<span style="font-size: 12px; color: {value_color}; font-family: {FONT_MONO}; font-weight: 500;">{value}</span>'
        f'</div>'
    )


def render_data_link_status_block(data: dict) -> None:
    """渲染数据链路状态区块。"""
    excel_ok = data.get("excel_imported", False)
    dcs_status = data.get("dcs_status", "未连接")
    qm = data.get("quality_metrics", {})

    content = _item_line("Excel 历史数据", "已导入" if excel_ok else "未导入", ACCENT_BLUE if excel_ok else RISK_RED)
    content += _item_line("DCS 在线数据", dcs_status, ACCENT_BLUE)
    content += _item_line("缺失率", qm.get("missing_rate", "N/A"))
    content += _item_line("异常跳变率", qm.get("abnormal_jump_rate", "N/A"))
    content += _item_line("有效样本率", qm.get("valid_sample_rate", "N/A"), ACCENT_BLUE)
    content += _item_line("数据源", qm.get("data_source", "N/A"))

    _summary_block_wrapper("数据链路状态", content)


def render_model_status_block(data: dict) -> None:
    """渲染模型状态区块。"""
    def _status_color(s: str) -> str:
        if "已加载" in s or "已启用" in s:
            return ACCENT_BLUE
        if "待训练" in s:
            return TEXT_MUTED
        if "未启用" in s or "预留" in s:
            return TEXT_MUTED
        return TEXT_MAIN

    content = _item_line("PCA 模型", data.get("pca", "N/A"), _status_color(data.get("pca", "")))
    content += _item_line("PLS 模型", data.get("pls", "N/A"), _status_color(data.get("pls", "")))
    content += _item_line("Isolation Forest", data.get("if_model", "N/A"), _status_color(data.get("if_model", "")))
    content += _item_line("健康指数模型", data.get("health_index", "N/A"), _status_color(data.get("health_index", "")))
    content += _item_line("智能补偿模型", data.get("intelligent", "N/A"), _status_color(data.get("intelligent", "")))
    content += _item_line("模型版本", data.get("version", "N/A"))

    _summary_block_wrapper("模型运行状态", content)


def render_risk_sources_block(data: dict) -> None:
    """渲染当前风险来源区块。"""
    content = ""
    for key, item in data.items():
        if isinstance(item, dict):
            label = item.get("label", key)
            value = item.get("value", "N/A")
            active = item.get("active", False)
            color = RISK_RED if active else TEXT_MAIN
            indicator = "●" if active else "○"
            content += (
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">'
                f'<span style="font-size: 12px; color: {TEXT_SECONDARY}; font-family: {FONT_FAMILY};">'
                f'<span style="color: {RISK_RED if active else TEXT_MUTED}; margin-right: 4px;">{indicator}</span>{label}</span>'
                f'<span style="font-size: 12px; color: {color}; font-family: {FONT_MONO}; font-weight: 500;">{value}</span>'
                f'</div>'
            )

    _summary_block_wrapper("当前风险来源", content)


def render_recommended_focus_block(data: dict) -> None:
    """渲染推荐关注对象区块。"""
    module = data.get("module", "")
    variable = data.get("variable", "")
    coupling = data.get("coupling", "")

    content = _item_line("建议关注模块", module or "无", ACCENT_BLUE if module else TEXT_MUTED)
    content += _item_line("建议关注变量", variable or "无", ACCENT_BLUE if variable else TEXT_MUTED)
    content += _item_line("建议关注耦合", coupling or "无", ACCENT_BLUE if coupling else TEXT_MUTED)

    _summary_block_wrapper("推荐关注对象", content)
