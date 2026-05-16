"""动态特征提取。

提取变化率、斜率、滞后项等动态特征。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class DynamicFeatureExtractor:
    """动态特征提取器。"""

    def __init__(self, lag_steps: list[int] | None = None, rolling_window: int = 10) -> None:
        self.lag_steps = lag_steps or [1, 5]
        self.rolling_window = rolling_window

    def extract(self, series: pd.Series, prefix: str = "") -> pd.DataFrame:
        """提取动态特征。"""
        feat = pd.DataFrame(index=series.index)

        # 变化率
        diff = series.diff()
        feat[f"{prefix}_change_rate"] = diff

        # 百分比变化率
        pct = series.pct_change()
        feat[f"{prefix}_pct_change"] = pct.replace([np.inf, -np.inf], 0)

        # 斜率（线性回归斜率近似）
        feat[f"{prefix}_slope"] = self._rolling_slope(series, self.rolling_window)

        # 滞后项
        for lag in self.lag_steps:
            feat[f"{prefix}_lag_{lag}"] = series.shift(lag)

        # 滑动均值和标准差
        rolling = series.rolling(window=self.rolling_window, min_periods=1)
        feat[f"{prefix}_rolling_mean_{self.rolling_window}"] = rolling.mean()
        feat[f"{prefix}_rolling_std_{self.rolling_window}"] = rolling.std()

        # 二阶差分（加速度）
        feat[f"{prefix}_acceleration"] = diff.diff()

        return feat

    @staticmethod
    def _rolling_slope(series: pd.Series, window: int) -> pd.Series:
        """计算滚动线性回归斜率。"""
        slopes = pd.Series(np.nan, index=series.index)
        values = series.values

        for i in range(window, len(values)):
            y = values[i - window:i]
            x = np.arange(window)
            if np.std(y) > 1e-10:
                slope = np.polyfit(x, y, 1)[0]
                slopes.iloc[i] = slope

        return slopes
