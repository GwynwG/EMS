"""时间对齐模块。

处理不同采样率数据的时间对齐和重采样。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TimeAligner:
    """时间对齐器。"""

    def __init__(self, target_freq: str = "1s", method: str = "ffill") -> None:
        """初始化。

        Args:
            target_freq: 目标频率，如 '1s', '10s', '1min'
            method: 插值方法 'ffill', 'bfill', 'interpolate', 'nearest'
        """
        self.target_freq = target_freq
        self.method = method

    def align(self, df: pd.DataFrame) -> pd.DataFrame:
        """对齐 DataFrame 到统一时间频率。"""
        if not isinstance(df.index, pd.DatetimeIndex):
            logger.warning("非 DatetimeIndex，跳过时间对齐")
            return df

        logger.info(f"时间对齐: {len(df)} 行, 目标频率={self.target_freq}")

        # 创建统一时间索引
        start = df.index.min()
        end = df.index.max()
        new_index = pd.date_range(start=start, end=end, freq=self.target_freq)

        # 重采样
        df_resampled = df.reindex(new_index)

        # 插值
        if self.method == "ffill":
            df_resampled = df_resampled.ffill()
        elif self.method == "bfill":
            df_resampled = df_resampled.bfill()
        elif self.method == "interpolate":
            numeric = df_resampled.select_dtypes(include=[np.number]).columns
            df_resampled[numeric] = df_resampled[numeric].interpolate(method="linear")
        elif self.method == "nearest":
            df_resampled = df_resampled.ffill().bfill()

        # 填充剩余缺失
        df_resampled = df_resampled.ffill().bfill()

        logger.info(f"对齐完成: {len(df_resampled)} 行")
        return df_resampled

    def resample_to_frequency(self, df: pd.DataFrame, freq: str, agg: str = "mean") -> pd.DataFrame:
        """按指定频率重采样。"""
        if not isinstance(df.index, pd.DatetimeIndex):
            return df

        numeric = df.select_dtypes(include=[np.number])
        if agg == "mean":
            return numeric.resample(freq).mean()
        elif agg == "median":
            return numeric.resample(freq).median()
        elif agg == "max":
            return numeric.resample(freq).max()
        elif agg == "min":
            return numeric.resample(freq).min()
        elif agg == "last":
            return numeric.resample(freq).last()
        return numeric.resample(freq).mean()
