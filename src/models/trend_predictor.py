"""趋势预测器。

基于滚动窗口线性回归和指数平滑，预测未来 N 步的关键指标变化趋势。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PredictionResult:
    """预测结果。"""
    current_value: float
    predicted_values: list[float]
    trend_direction: str  # "上升", "下降", "平稳"
    trend_rate: float  # 每步变化率
    confidence_band: list[tuple[float, float]]  # (lower, upper) 置信带
    time_to_threshold: float | None  # 到达阈值的预估步数（None = 不会到达）
    risk_forecast: str  # "稳定", "趋于恶化", "趋于好转"


class TrendPredictor:
    """趋势预测器。"""

    def __init__(self, window: int = 50, forecast_steps: int = 20) -> None:
        """
        Args:
            window: 用于拟合的历史窗口长度
            forecast_steps: 预测未来步数
        """
        self.window = window
        self.forecast_steps = forecast_steps

    def predict_trend(
        self,
        series: pd.Series,
        threshold_high: float | None = None,
        threshold_low: float | None = None,
    ) -> PredictionResult:
        """预测单个指标的未来趋势。

        Args:
            series: 历史时间序列
            threshold_high: 上限阈值（如风险分数 70）
            threshold_low: 下限阈值（如健康指数 40）

        Returns:
            PredictionResult 预测结果
        """
        if len(series) < 5:
            return PredictionResult(
                current_value=float(series.iloc[-1]) if len(series) > 0 else 0,
                predicted_values=[], trend_direction="平稳",
                trend_rate=0, confidence_band=[],
                time_to_threshold=None, risk_forecast="数据不足",
            )

        # 取最近 window 个点
        recent = series.tail(self.window).values.astype(float)
        n = len(recent)
        x = np.arange(n)

        # 线性回归拟合趋势
        slope, intercept = np.polyfit(x, recent, 1)

        # 计算残差标准差（用于置信带）
        fitted = slope * x + intercept
        residuals = recent - fitted
        residual_std = max(np.std(residuals), 1e-6)

        # 预测未来 N 步
        future_x = np.arange(n, n + self.forecast_steps)
        predicted = slope * future_x + intercept

        # 95% 置信带（随预测步数扩大）
        confidence_band = []
        for i, px in enumerate(predicted):
            spread = residual_std * (1 + i * 0.1) * 1.96
            confidence_band.append((float(px - spread), float(px + spread)))

        # 趋势判定
        if abs(slope) < residual_std * 0.1:
            direction = "平稳"
        elif slope > 0:
            direction = "上升"
        else:
            direction = "下降"

        # 到达阈值的预估步数
        time_to_threshold = None
        if threshold_high is not None and slope > 0:
            current = recent[-1]
            if current < threshold_high:
                steps = (threshold_high - current) / slope
                time_to_threshold = float(steps)
        elif threshold_low is not None and slope < 0:
            current = recent[-1]
            if current > threshold_low:
                steps = (current - threshold_low) / abs(slope)
                time_to_threshold = float(steps)

        # 风险预测
        if time_to_threshold is not None and time_to_threshold < self.forecast_steps:
            risk_forecast = "趋于恶化"
        elif abs(slope) < residual_std * 0.05:
            risk_forecast = "稳定"
        elif (slope > 0 and threshold_high is not None) or (slope < 0 and threshold_low is not None):
            risk_forecast = "趋于恶化"
        else:
            risk_forecast = "趋于好转"

        return PredictionResult(
            current_value=float(recent[-1]),
            predicted_values=[float(v) for v in predicted],
            trend_direction=direction,
            trend_rate=float(slope),
            confidence_band=confidence_band,
            time_to_threshold=time_to_threshold,
            risk_forecast=risk_forecast,
        )

    def predict_multi(
        self,
        df: pd.DataFrame,
        columns: list[str],
        thresholds: dict[str, dict[str, float]] | None = None,
    ) -> dict[str, PredictionResult]:
        """预测多个指标。"""
        results = {}
        for col in columns:
            if col not in df.columns:
                continue
            th = thresholds.get(col, {}) if thresholds else {}
            results[col] = self.predict_trend(
                df[col],
                threshold_high=th.get("high"),
                threshold_low=th.get("low"),
            )
        return results
