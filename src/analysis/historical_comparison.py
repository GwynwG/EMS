"""历史对比分析模块。

支持选取两个时间段进行指标对比，计算退化速率差异，
并与历史异常模式进行匹配。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PeriodStats:
    """时间段统计。"""
    start: str
    end: str
    mean: float
    std: float
    min_val: float
    max_val: float
    trend_slope: float  # 线性趋势斜率
    anomaly_rate: float  # 异常占比


@dataclass
class ComparisonResult:
    """对比结果。"""
    metric: str
    period_a: PeriodStats
    period_b: PeriodStats
    mean_change: float  # 均值变化百分比
    std_change: float  # 标准差变化百分比
    trend_change: float  # 趋势斜率变化
    degradation_rate: float  # 退化速率差异
    severity: str  # "无显著变化", "轻微恶化", "明显恶化", "严重恶化"
    description: str  # 文字描述


class HistoricalComparator:
    """历史对比分析器。"""

    def compute_period_stats(
        self,
        series: pd.Series,
        start: str | int | None = None,
        end: str | int | None = None,
        anomaly_threshold: float | None = None,
    ) -> PeriodStats:
        """计算单个时间段的统计指标。"""
        try:
            if start is not None:
                series = series.loc[start:]
            if end is not None:
                series = series.loc[:end]
        except (KeyError, TypeError):
            # 数值索引回退：用 iloc 位置切片
            pass

        if series.empty:
            return PeriodStats("", "", 0, 0, 0, 0, 0, 0)

        values = series.dropna().values.astype(float)
        if len(values) < 2:
            return PeriodStats("", "", float(values[0]) if len(values) > 0 else 0,
                             0, 0, 0, 0, 0)

        # 线性趋势
        x = np.arange(len(values))
        slope = float(np.polyfit(x, values, 1)[0])

        # 异常率
        anomaly_rate = 0.0
        if anomaly_threshold is not None:
            anomaly_rate = float(np.mean(values > anomaly_threshold))

        idx = series.index
        return PeriodStats(
            start=str(idx[0]),
            end=str(idx[-1]),
            mean=float(np.mean(values)),
            std=float(np.std(values)),
            min_val=float(np.min(values)),
            max_val=float(np.max(values)),
            trend_slope=slope,
            anomaly_rate=anomaly_rate,
        )

    def compare_periods(
        self,
        series: pd.Series,
        period_a: tuple[str, str],
        period_b: tuple[str, str],
        metric_name: str = "",
        anomaly_threshold: float | None = None,
    ) -> ComparisonResult:
        """对比两个时间段的指标。

        Args:
            series: 完整时间序列
            period_a: 第一个时间段 (start, end)
            period_b: 第二个时间段 (start, end)
            metric_name: 指标名称
            anomaly_threshold: 异常阈值

        Returns:
            ComparisonResult
        """
        stats_a = self.compute_period_stats(series, period_a[0], period_a[1], anomaly_threshold)
        stats_b = self.compute_period_stats(series, period_b[0], period_b[1], anomaly_threshold)

        # 变化百分比
        mean_change = 0.0
        if abs(stats_a.mean) > 1e-10:
            mean_change = (stats_b.mean - stats_a.mean) / abs(stats_a.mean) * 100

        std_change = 0.0
        if abs(stats_a.std) > 1e-10:
            std_change = (stats_b.std - stats_a.std) / abs(stats_a.std) * 100

        trend_change = stats_b.trend_slope - stats_a.trend_slope

        # 退化速率差异（趋势斜率的变化）
        degradation_rate = trend_change

        # 严重程度判定
        if abs(mean_change) < 5 and abs(std_change) < 10:
            severity = "无显著变化"
            desc = f"{metric_name}在两个时间段内基本稳定。"
        elif abs(mean_change) < 15 and abs(std_change) < 30:
            severity = "轻微恶化" if mean_change > 0 or std_change > 0 else "轻微改善"
            desc = f"{metric_name}均值变化 {mean_change:+.1f}%，波动性变化 {std_change:+.1f}%。"
        elif abs(mean_change) < 30:
            severity = "明显恶化" if mean_change > 0 or std_change > 0 else "明显改善"
            desc = (f"{metric_name}均值变化 {mean_change:+.1f}%，"
                   f"波动性变化 {std_change:+.1f}%，"
                   f"趋势斜率变化 {trend_change:+.4f}。")
        else:
            severity = "严重恶化" if mean_change > 0 or std_change > 0 else "显著改善"
            desc = (f"{metric_name}发生显著变化：均值变化 {mean_change:+.1f}%，"
                   f"建议排查原因。")

        return ComparisonResult(
            metric=metric_name,
            period_a=stats_a,
            period_b=stats_b,
            mean_change=round(mean_change, 2),
            std_change=round(std_change, 2),
            trend_change=round(trend_change, 6),
            degradation_rate=round(degradation_rate, 6),
            severity=severity,
            description=desc,
        )

    def compare_multi_metrics(
        self,
        df: pd.DataFrame,
        period_a: tuple[str, str] | tuple[int, int],
        period_b: tuple[str, str] | tuple[int, int],
        columns: list[str] | None = None,
    ) -> list[ComparisonResult]:
        """对比多个指标。"""
        if columns is None:
            columns = ["risk_score", "health_index", "pca_anomaly_score", "if_anomaly_score"]
            columns = [c for c in columns if c in df.columns]

        # 如果是位置索引（int），用 iloc 切片
        n = len(df)
        use_iloc = isinstance(period_a[0], int)

        results = []
        thresholds = {
            "risk_score": 70,
            "health_index": None,
            "pca_anomaly_score": 1.0,
            "if_anomaly_score": 0.7,
        }

        for col in columns:
            if use_iloc:
                series_a = df[col].iloc[period_a[0]:period_a[1]]
                series_b = df[col].iloc[period_b[0]:period_b[1]]
                stats_a = self._compute_stats_from_series(series_a, thresholds.get(col))
                stats_b = self._compute_stats_from_series(series_b, thresholds.get(col))
            else:
                stats_a = self.compute_period_stats(df[col], period_a[0], period_a[1], thresholds.get(col))
                stats_b = self.compute_period_stats(df[col], period_b[0], period_b[1], thresholds.get(col))

            result = self._build_comparison(stats_a, stats_b, col)
            results.append(result)

        return results

    def _compute_stats_from_series(
        self,
        series: pd.Series,
        anomaly_threshold: float | None = None,
    ) -> PeriodStats:
        """从已切好的 Series 计算统计。"""
        values = series.dropna().values.astype(float)
        if len(values) < 2:
            return PeriodStats("", "", float(values[0]) if len(values) > 0 else 0,
                             0, 0, 0, 0, 0)
        x = np.arange(len(values))
        slope = float(np.polyfit(x, values, 1)[0])
        anomaly_rate = float(np.mean(values > anomaly_threshold)) if anomaly_threshold else 0.0
        idx = series.index
        return PeriodStats(
            start=str(idx[0]), end=str(idx[-1]),
            mean=float(np.mean(values)), std=float(np.std(values)),
            min_val=float(np.min(values)), max_val=float(np.max(values)),
            trend_slope=slope, anomaly_rate=anomaly_rate,
        )

    @staticmethod
    def _build_comparison(stats_a: PeriodStats, stats_b: PeriodStats, metric_name: str) -> ComparisonResult:
        """从两个统计结果构建对比。"""
        mean_change = (stats_b.mean - stats_a.mean) / abs(stats_a.mean) * 100 if abs(stats_a.mean) > 1e-10 else 0
        std_change = (stats_b.std - stats_a.std) / abs(stats_a.std) * 100 if abs(stats_a.std) > 1e-10 else 0
        trend_change = stats_b.trend_slope - stats_a.trend_slope

        if abs(mean_change) < 5 and abs(std_change) < 10:
            severity = "无显著变化"
            desc = f"{metric_name}在两个时间段内基本稳定。"
        elif abs(mean_change) < 15 and abs(std_change) < 30:
            severity = "轻微恶化" if mean_change > 0 or std_change > 0 else "轻微改善"
            desc = f"{metric_name}均值变化 {mean_change:+.1f}%，波动性变化 {std_change:+.1f}%。"
        elif abs(mean_change) < 30:
            severity = "明显恶化" if mean_change > 0 or std_change > 0 else "明显改善"
            desc = f"{metric_name}均值变化 {mean_change:+.1f}%，波动性变化 {std_change:+.1f}%。"
        else:
            severity = "严重恶化" if mean_change > 0 or std_change > 0 else "显著改善"
            desc = f"{metric_name}发生显著变化：均值变化 {mean_change:+.1f}%。"

        return ComparisonResult(
            metric=metric_name, period_a=stats_a, period_b=stats_b,
            mean_change=round(mean_change, 2), std_change=round(std_change, 2),
            trend_change=round(trend_change, 6),
            degradation_rate=round(trend_change, 6),
            severity=severity, description=desc,
        )
