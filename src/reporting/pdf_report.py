"""PDF 可视化报告生成器。

使用 matplotlib 后端生成包含图表的 PDF 诊断报告，无需额外依赖。
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

# 中文字体设置 — 自动查找系统可用中文字体
def _find_cn_font():
    """查找系统中可用的中文字体。"""
    candidates = ["Microsoft YaHei", "SimHei", "SimSun", "PingFang SC",
                  "WenQuanYi Micro Hei", "Noto Sans CJK SC", "Arial Unicode MS"]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return "sans-serif"

_CN_FONT = _find_cn_font()
plt.rcParams["font.sans-serif"] = [_CN_FONT, "DejaVu Sans", "sans-serif"]
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.unicode_minus"] = False

# 颜色
C_BG = "#2B2F36"
C_CARD = "#353B45"
C_BLUE = "#60A5FA"
C_RED = "#F87171"
C_GREEN = "#34D399"
C_AMBER = "#FBBF24"
C_TEXT = "#F3F4F6"
C_TEXT2 = "#D1D5DB"
C_MUTED = "#9CA3AF"
C_GRID = "#49515D"


def _dark_style():
    """设置暗色图表风格。"""
    return {
        "figure.facecolor": C_BG,
        "axes.facecolor": C_CARD,
        "axes.edgecolor": C_GRID,
        "axes.labelcolor": C_TEXT2,
        "text.color": C_TEXT,
        "xtick.color": C_MUTED,
        "ytick.color": C_MUTED,
        "grid.color": C_GRID,
        "grid.alpha": 0.3,
    }


def generate_pdf_report(
    df: pd.DataFrame,
    status: dict[str, Any],
    output_path: str | Path,
    root_cause_result: dict | None = None,
) -> Path:
    """生成 PDF 诊断报告。

    Args:
        df: model_results.csv 数据
        status: 当前状态字典（risk_score, health_index, module_scores 等）
        output_path: PDF 输出路径
        root_cause_result: 根因分析结果（可选）

    Returns:
        生成的 PDF 文件路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(str(output_path)) as pdf:
        style = _dark_style()

        # ── 第 1 页：封面 + 概要 ──
        with plt.rc_context(style):
            fig, axes = plt.subplots(2, 2, figsize=(11.69, 8.27))
            fig.suptitle("设备状态监测与智能预警 — 诊断报告", fontsize=18, fontweight="bold",
                        color=C_TEXT, y=0.97)

            # 报告信息
            ax = axes[0, 0]
            ax.axis("off")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rs = status.get("risk_score", 0)
            hi = status.get("health_index", 100)
            risk_level = status.get("risk_level", "normal")
            level_cn = {"normal": "正常", "attention": "关注", "warning": "预警", "severe": "严重"}.get(risk_level, risk_level)

            info_text = (
                f"报告时间: {now}\n"
                f"样本数量: {len(df):,}\n"
                f"风险等级: {level_cn}\n"
                f"风险分数: {rs:.1f}\n"
                f"健康指数: {hi:.1f}\n"
                f"主异常模块: {status.get('main_abnormal_module', '—')}"
            )
            ax.text(0.1, 0.5, info_text, fontsize=13, color=C_TEXT2, va="center",
                   family=_CN_FONT, transform=ax.transAxes)

            # 风险分数仪表
            ax = axes[0, 1]
            _draw_gauge(ax, rs, "综合风险分数", max_val=100)

            # 健康指数仪表
            ax = axes[1, 0]
            _draw_gauge(ax, hi, "健康指数", max_val=100)

            # 模块评分
            ax = axes[1, 1]
            module_scores = status.get("module_scores", {})
            if module_scores:
                mod_cn = {"execution_control": "执行控制", "energy_input": "能量输入",
                         "environmental_constraint": "环境约束", "state_maintenance": "状态维持"}
                names = [mod_cn.get(k, k) for k in module_scores]
                scores = list(module_scores.values())
                colors = [C_GREEN if s > 80 else (C_AMBER if s > 60 else C_RED) for s in scores]
                bars = ax.barh(names, scores, color=colors, height=0.5)
                ax.set_xlim(0, 100)
                ax.set_title("四模块健康评分", fontsize=12, color=C_TEXT)
                for bar, score in zip(bars, scores):
                    ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                           f"{score:.1f}", va="center", fontsize=10, color=C_TEXT2)

            plt.tight_layout(rect=[0, 0, 1, 0.94])
            pdf.savefig(fig)
            plt.close(fig)

        # ── 第 2 页：趋势图 ──
        if not df.empty:
            with plt.rc_context(style):
                fig, axes = plt.subplots(3, 1, figsize=(11.69, 8.27))
                fig.suptitle("关键指标趋势", fontsize=16, fontweight="bold",
                            color=C_TEXT, y=0.97)

                # 风险分数趋势
                ax = axes[0]
                if "risk_score" in df.columns:
                    data = df["risk_score"].tail(300)
                    ax.plot(range(len(data)), data.values, color=C_RED, linewidth=1.2)
                    ax.fill_between(range(len(data)), data.values, alpha=0.1, color=C_RED)
                    ax.axhline(y=70, color=C_AMBER, linestyle="--", linewidth=0.8, alpha=0.6)
                    ax.axhline(y=30, color=C_GREEN, linestyle="--", linewidth=0.8, alpha=0.6)
                ax.set_title("风险分数", fontsize=11, color=C_TEXT)
                ax.grid(True, alpha=0.2)

                # 健康指数趋势
                ax = axes[1]
                if "health_index" in df.columns:
                    data = df["health_index"].tail(300)
                    ax.plot(range(len(data)), data.values, color=C_BLUE, linewidth=1.2)
                    ax.fill_between(range(len(data)), data.values, alpha=0.1, color=C_BLUE)
                    ax.axhline(y=80, color=C_GREEN, linestyle="--", linewidth=0.8, alpha=0.6)
                    ax.axhline(y=60, color=C_AMBER, linestyle="--", linewidth=0.8, alpha=0.6)
                    ax.axhline(y=40, color=C_RED, linestyle="--", linewidth=0.8, alpha=0.6)
                ax.set_title("健康指数", fontsize=11, color=C_TEXT)
                ax.grid(True, alpha=0.2)

                # 异常分数趋势
                ax = axes[2]
                if "pca_anomaly_score" in df.columns:
                    data = df["pca_anomaly_score"].tail(300)
                    ax.plot(range(len(data)), data.values, color=C_AMBER, linewidth=1.0, label="PCA")
                if "if_anomaly_score" in df.columns:
                    data = df["if_anomaly_score"].tail(300)
                    ax.plot(range(len(data)), data.values, color=C_BLUE, linewidth=1.0, alpha=0.7, label="IF")
                ax.axhline(y=1.0, color=C_RED, linestyle="--", linewidth=0.8, alpha=0.6)
                ax.set_title("异常分数", fontsize=11, color=C_TEXT)
                ax.legend(fontsize=9, framealpha=0.3)
                ax.grid(True, alpha=0.2)

                plt.tight_layout(rect=[0, 0, 1, 0.94])
                pdf.savefig(fig)
                plt.close(fig)

        # ── 第 3 页：根因分析 ──
        if root_cause_result and root_cause_result.get("root_causes"):
            with plt.rc_context(style):
                fig, axes = plt.subplots(1, 2, figsize=(11.69, 8.27))
                fig.suptitle("异常根因分析", fontsize=16, fontweight="bold",
                            color=C_TEXT, y=0.97)

                # 贡献度条形图
                ax = axes[0]
                causes = root_cause_result["root_causes"][:10]
                labels = [f"{c['variable']} ({c['module_cn']})" for c in causes]
                values = [c["contribution"] for c in causes]
                colors = [C_RED if v > 0 else C_BLUE for v in values]
                bars = ax.barh(range(len(labels)), values, color=colors, height=0.6)
                ax.set_yticks(range(len(labels)))
                ax.set_yticklabels(labels, fontsize=9)
                ax.invert_yaxis()
                ax.set_title("变量贡献度 Top-10", fontsize=12, color=C_TEXT)
                ax.grid(True, alpha=0.2, axis="x")

                # 模块贡献饼图
                ax = axes[1]
                mc = root_cause_result.get("module_contributions", {})
                if mc:
                    mod_cn = {"execution_control": "执行控制", "energy_input": "能量输入",
                             "environmental_constraint": "环境约束", "state_maintenance": "状态维持"}
                    pie_labels = [mod_cn.get(k, k) for k in mc.keys()]
                    pie_values = list(mc.values())
                    pie_colors = [C_BLUE, C_GREEN, C_AMBER, C_RED][:len(pie_values)]
                    ax.pie(pie_values, labels=pie_labels, colors=pie_colors,
                          autopct="%1.1f%%", textprops={"color": C_TEXT, "fontsize": 10})
                    ax.set_title("模块异常贡献分布", fontsize=12, color=C_TEXT)

                plt.tight_layout(rect=[0, 0, 1, 0.94])
                pdf.savefig(fig)
                plt.close(fig)

        logger.info(f"PDF 报告已生成: {output_path}")

    return output_path


def _draw_gauge(ax, value: float, title: str, max_val: float = 100):
    """在 matplotlib axes 上绘制仪表盘。"""
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.3, 1.2)
    ax.axis("off")
    ax.set_aspect("equal")

    # 背景弧
    theta = np.linspace(np.pi, 0, 100)
    r_outer = 1.0
    r_inner = 0.7
    for i in range(len(theta) - 1):
        angle = np.degrees(theta[i])
        if angle > 120:
            color = C_GREEN
        elif angle > 60:
            color = C_AMBER
        else:
            color = C_RED
        ax.fill_between(
            [r_inner * np.cos(theta[i]), r_outer * np.cos(theta[i])],
            [r_inner * np.sin(theta[i]), r_outer * np.sin(theta[i])],
            alpha=0.2, color=color,
        )

    # 指针
    angle = np.pi * (1 - min(value, max_val) / max_val)
    ax.annotate("", xy=(0.85 * np.cos(angle), 0.85 * np.sin(angle)),
               xytext=(0, 0),
               arrowprops=dict(arrowstyle="->", color=C_TEXT, lw=2.5))

    # 数值
    ax.text(0, -0.15, f"{value:.1f}", fontsize=22, fontweight="bold",
           color=C_TEXT, ha="center", va="center")
    ax.text(0, -0.3, title, fontsize=11, color=C_MUTED, ha="center", va="center")
