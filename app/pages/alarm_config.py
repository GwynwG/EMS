"""告警规则配置页面。

在仪表盘中动态查看和调整告警阈值，无需手动修改 YAML 文件。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from app.shared import (
    ROOT, load_model_results,
    ACCENT_BLUE, RISK_RED, HEALTH_GREEN, WARN_AMBER,
    TEXT_MAIN, TEXT_SECONDARY, TEXT_MUTED,
    render_kpi_card,
)


_MODULE_CN = {
    "execution_control": "执行控制",
    "energy_input": "能量输入",
    "environmental_constraint": "环境约束",
    "state_maintenance": "状态维持",
}

_LEVEL_COLORS = {
    "normal": HEALTH_GREEN,
    "attention": WARN_AMBER,
    "warning": WARN_AMBER,
    "severe": RISK_RED,
}

_LEVEL_CN = {
    "normal": "正常",
    "attention": "关注",
    "warning": "预警",
    "severe": "严重",
}


@st.cache_data
def _load_alarm_rules() -> dict:
    """加载告警规则配置。"""
    path = ROOT / "configs" / "alarm_rules.yaml"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _save_alarm_rules(config: dict) -> None:
    """保存告警规则配置。"""
    path = ROOT / "configs" / "alarm_rules.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    # 清除缓存
    _load_alarm_rules.clear()


def render_alarm_config_page() -> None:
    st.markdown("# 告警规则配置")
    st.caption("查看和调整告警阈值，修改后立即生效")

    config = _load_alarm_rules()
    df = load_model_results()

    # ── 风险等级阈值 ──
    st.markdown("## 风险等级阈值")
    st.caption("调整风险分数的等级划分阈值")

    levels = config.get("alarm_levels", {})
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)

    thresholds = {}
    with col_l1:
        normal_range = levels.get("normal", {}).get("score_range", [0, 30])
        thresholds["normal"] = st.slider("正常上限", 0, 100, normal_range[1], 5, key="al_normal")
    with col_l2:
        attention_range = levels.get("attention", {}).get("score_range", [30, 50])
        thresholds["attention"] = st.slider("关注上限", 0, 100, attention_range[1], 5, key="al_attention")
    with col_l3:
        warning_range = levels.get("warning", {}).get("score_range", [50, 70])
        thresholds["warning"] = st.slider("预警上限", 0, 100, warning_range[1], 5, key="al_warning")
    with col_l4:
        severe_range = levels.get("severe", {}).get("score_range", [70, 100])
        thresholds["severe"] = st.slider("严重起点", 0, 100, severe_range[0], 5, key="al_severe")

    if st.button("保存风险等级阈值", type="primary"):
        config["alarm_levels"] = {
            "normal": {"label": "正常", "color": HEALTH_GREEN, "score_range": [0, thresholds["normal"]]},
            "attention": {"label": "关注", "color": WARN_AMBER, "score_range": [thresholds["normal"], thresholds["attention"]]},
            "warning": {"label": "预警", "color": WARN_AMBER, "score_range": [thresholds["attention"], thresholds["warning"]]},
            "severe": {"label": "严重", "color": RISK_RED, "score_range": [thresholds["severe"], 100]},
        }
        _save_alarm_rules(config)
        st.success("风险等级阈值已保存")
        st.rerun()

    st.markdown("---")

    # ── 告警规则列表 ──
    st.markdown("## 告警规则")
    st.caption("条件表达式格式: 变量名 > 阈值 或 变量名 < 阈值")

    rules = config.get("alarm_rules", [])

    # 当前规则展示
    if rules:
        rules_data = []
        for i, rule in enumerate(rules):
            rules_data.append({
                "序号": i + 1,
                "规则名": rule.get("name", ""),
                "模块": _MODULE_CN.get(rule.get("module", ""), rule.get("module", "")),
                "条件": rule.get("condition", ""),
                "等级": _LEVEL_CN.get(rule.get("level", ""), rule.get("level", "")),
                "消息": rule.get("message", ""),
            })
        st.dataframe(pd.DataFrame(rules_data), width="stretch", hide_index=True)
    else:
        st.info("暂无告警规则")

    # ── 添加新规则 ──
    st.markdown("### 添加新规则")
    with st.form("add_alarm_rule"):
        ar1, ar2 = st.columns(2)
        with ar1:
            rule_name = st.text_input("规则名称", placeholder="furnace_temp_high")
            rule_module = st.selectbox("所属模块", list(_MODULE_CN.keys()),
                                      format_func=lambda x: _MODULE_CN.get(x, x))
            rule_condition = st.text_input("触发条件", placeholder="furnace_temp_1 > 1200")
        with ar2:
            rule_level = st.selectbox("告警等级", ["attention", "warning", "severe"],
                                     format_func=lambda x: _LEVEL_CN.get(x, x))
            rule_message = st.text_input("告警消息", placeholder="炉温1区超温")

        submitted = st.form_submit_button("添加规则")
        if submitted and rule_name and rule_condition:
            new_rule = {
                "name": rule_name,
                "module": rule_module,
                "condition": rule_condition,
                "level": rule_level,
                "message": rule_message or rule_name,
            }
            rules.append(new_rule)
            config["alarm_rules"] = rules
            _save_alarm_rules(config)
            st.success(f"规则 '{rule_name}' 已添加")
            st.rerun()

    # ── 删除规则 ──
    if rules:
        st.markdown("### 删除规则")
        rule_names = [r.get("name", f"规则{i+1}") for i, r in enumerate(rules)]
        to_delete = st.selectbox("选择要删除的规则", rule_names)
        if st.button("删除选中规则", type="secondary"):
            rules = [r for r in rules if r.get("name") != to_delete]
            config["alarm_rules"] = rules
            _save_alarm_rules(config)
            st.success(f"规则 '{to_delete}' 已删除")
            st.rerun()

    st.markdown("---")

    # ── 触发统计 ──
    st.markdown("## 触发统计")
    if not df.empty:
        st.caption("基于最近数据统计各规则的触发情况")

        trigger_data = []
        for rule in rules:
            condition = rule.get("condition", "")
            name = rule.get("name", "")
            message = rule.get("message", "")
            level = rule.get("level", "")

            # 简单解析条件（支持 > 和 < 比较）
            triggered = 0
            try:
                if " > " in condition:
                    var, threshold = condition.split(" > ")
                    var = var.strip()
                    threshold = float(threshold.strip())
                    if var in df.columns:
                        triggered = int((df[var] > threshold).sum())
                elif " < " in condition:
                    var, threshold = condition.split(" < ")
                    var = var.strip()
                    threshold = float(threshold.strip())
                    if var in df.columns:
                        triggered = int((df[var] < threshold).sum())
                elif " == " in condition:
                    var, val = condition.split(" == ")
                    var = var.strip()
                    val = float(val.strip())
                    if var in df.columns:
                        triggered = int((df[var] == val).sum())
            except (ValueError, KeyError):
                pass

            trigger_data.append({
                "规则": message,
                "等级": _LEVEL_CN.get(level, level),
                "触发次数": triggered,
                "触发率": f"{triggered / len(df) * 100:.1f}%" if len(df) > 0 else "0%",
            })

        st.dataframe(pd.DataFrame(trigger_data), width="stretch", hide_index=True)
    else:
        st.info("暂无数据")
