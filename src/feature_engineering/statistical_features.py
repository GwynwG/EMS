"""统计特征提取。"""
from __future__ import annotations

import numpy as np
import pandas as pd


class StatisticalFeatureExtractor:
    """统计特征提取器。"""

    def __init__(self, window: int = 10) -> None:
        self.window = window

    def extract(self, series: pd.Series, prefix: str = "") -> pd.DataFrame:
        """提取统计特征。"""
        feat = pd.DataFrame(index=series.index)

        # 原始值
        feat[f"{prefix}_raw"] = series

        # 滑动统计量
        rolling = series.rolling(window=self.window, min_periods=1)
        feat[f"{prefix}_mean"] = rolling.mean()
        feat[f"{prefix}_std"] = rolling.std()
        feat[f"{prefix}_max"] = rolling.max()
        feat[f"{prefix}_min"] = rolling.min()
        feat[f"{prefix}_range"] = feat[f"{prefix}_max"] - feat[f"{prefix}_min"]

        # 全局统计量（累计）
        feat[f"{prefix}_cummean"] = series.expanding().mean()
        feat[f"{prefix}_cumstd"] = series.expanding().std()

        return feat

    @staticmethod
    def extract_basic_stats(series: pd.Series) -> dict[str, float]:
        """提取基本统计量字典。"""
        return {
            "mean": float(series.mean()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
            "median": float(series.median()),
            "skew": float(series.skew()),
            "kurt": float(series.kurtosis()),
        }
