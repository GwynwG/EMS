"""绘图工具模块。"""
from __future__ import annotations

from typing import Any, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from src.utils.config_loader import _resolve_path, ensure_dir
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 中文字体设置
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def plot_time_series(
    df: pd.DataFrame,
    columns: list[str],
    title: str = "时间序列",
    figsize: tuple[int, int] = (14, 5),
    save_path: str | None = None,
) -> plt.Figure:
    """绘制时间序列图。"""
    fig, ax = plt.subplots(figsize=figsize)
    for col in columns:
        if col in df.columns:
            ax.plot(df.index, df[col], label=col, linewidth=1)

    ax.set_title(title, fontsize=14)
    ax.set_xlabel("时间")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_anomaly_scores(
    scores: pd.DataFrame,
    title: str = "异常分数趋势",
    figsize: tuple[int, int] = (14, 6),
    save_path: str | None = None,
) -> plt.Figure:
    """绘制异常分数趋势图。"""
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)

    if "anomaly_score" in scores.columns:
        axes[0].plot(scores.index, scores["anomaly_score"], color="#1565C0", linewidth=1)
        axes[0].axhline(y=1.0, color="red", linestyle="--", alpha=0.7, label="阈值")
        axes[0].set_title("PCA 异常分数")
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

    if "t2" in scores.columns:
        axes[1].plot(scores.index, scores["t2"], color="#E65100", linewidth=1)
        axes[1].set_title("T² 统计量")
        axes[1].grid(True, alpha=0.3)

    fig.suptitle(title, fontsize=14)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_health_index(
    hi_series: pd.Series,
    title: str = "健康指数趋势",
    figsize: tuple[int, int] = (14, 4),
    save_path: str | None = None,
) -> plt.Figure:
    """绘制健康指数趋势图。"""
    fig, ax = plt.subplots(figsize=figsize)

    ax.fill_between(range(len(hi_series)), hi_series.values, alpha=0.3, color="#00C853")
    ax.plot(range(len(hi_series)), hi_series.values, color="#00C853", linewidth=1.5)

    # 阈值线
    ax.axhline(y=80, color="#FFD600", linestyle="--", alpha=0.5, label="健康阈值")
    ax.axhline(y=60, color="#FF6D00", linestyle="--", alpha=0.5, label="关注阈值")
    ax.axhline(y=40, color="#D50000", linestyle="--", alpha=0.5, label="预警阈值")

    ax.set_ylim(0, 105)
    ax.set_title(title, fontsize=14)
    ax.set_ylabel("健康指数")
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig


def plot_risk_dashboard(
    risk_data: dict[str, Any],
    figsize: tuple[int, int] = (16, 10),
    save_path: str | None = None,
) -> plt.Figure:
    """绘制风险仪表盘。"""
    fig = plt.figure(figsize=figsize)

    # 模块评分雷达图
    ax1 = fig.add_subplot(221, polar=True)
    modules = ["执行控制", "能量输入", "环境约束", "状态维持"]
    scores = [
        risk_data.get("module_scores", {}).get("execution_control", 100),
        risk_data.get("module_scores", {}).get("energy_input", 100),
        risk_data.get("module_scores", {}).get("environmental_constraint", 100),
        risk_data.get("module_scores", {}).get("state_maintenance", 100),
    ]
    angles = np.linspace(0, 2 * np.pi, len(modules), endpoint=False).tolist()
    scores_plot = scores + [scores[0]]
    angles += [angles[0]]
    ax1.fill(angles, scores_plot, alpha=0.25, color="#1565C0")
    ax1.plot(angles, scores_plot, color="#1565C0", linewidth=2)
    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels(modules, fontsize=10)
    ax1.set_ylim(0, 100)
    ax1.set_title("模块评分雷达", fontsize=12)

    # 风险分数
    ax2 = fig.add_subplot(222)
    risk_score = risk_data.get("risk_score", 0)
    color = "#D50000" if risk_score > 70 else "#FF6D00" if risk_score > 50 else "#FFD600" if risk_score > 30 else "#00C853"
    ax2.barh(["风险分数"], [risk_score], color=color, height=0.5)
    ax2.set_xlim(0, 100)
    ax2.set_title(f"综合风险: {risk_score:.1f}", fontsize=12)

    # 模块评分散点
    ax3 = fig.add_subplot(223)
    colors = ["#00C853" if s >= 80 else "#FFD600" if s >= 60 else "#FF6D00" if s >= 40 else "#D50000" for s in scores]
    ax3.bar(modules, scores, color=colors)
    ax3.set_ylim(0, 100)
    ax3.set_title("各模块评分", fontsize=12)
    ax3.tick_params(axis='x', rotation=15)

    # 信息
    ax4 = fig.add_subplot(224)
    ax4.axis("off")
    info_text = (
        f"风险等级: {risk_data.get('risk_level', 'N/A')}\n"
        f"健康指数: {risk_data.get('health_index', 'N/A'):.1f}\n"
        f"主异常模块: {risk_data.get('main_abnormal_module', 'N/A')}\n"
        f"主异常耦合: {risk_data.get('main_abnormal_coupling', 'N/A')}"
    )
    ax4.text(0.1, 0.5, info_text, fontsize=13, va="center", family="monospace")

    fig.suptitle("设备风险监测仪表盘", fontsize=16, y=0.98)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    return fig
