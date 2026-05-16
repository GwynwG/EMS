"""事件特征提取。

提取联锁触发、异常跳变、功率骤降等事件计数特征。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class EventFeatureExtractor:
    """事件特征提取器。"""

    def __init__(self, event_window: int = 60) -> None:
        self.event_window = event_window

    def extract(self, df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
        """提取事件特征。"""
        feat = pd.DataFrame(index=df.index)

        for col in columns:
            if col not in df.columns:
                continue

            series = df[col]

            # 联锁状态事件计数
            if "interlock" in col.lower():
                feat[f"{col}_event_count"] = series.rolling(
                    self.event_window, min_periods=1
                ).sum()

            # 跳变事件计数
            diff = series.diff().abs()
            std_val = series.std()
            if std_val > 0:
                jump_mask = (diff > 5 * std_val).astype(float)
                feat[f"{col}_jump_count"] = jump_mask.rolling(
                    self.event_window, min_periods=1
                ).sum()

            # 超限事件
            mean_val = series.mean()
            upper = mean_val + 3 * std_val
            lower = mean_val - 3 * std_val
            exceed_mask = ((series > upper) | (series < lower)).astype(float)
            feat[f"{col}_exceed_count"] = exceed_mask.rolling(
                self.event_window, min_periods=1
            ).sum()

            # 功率骤降检测
            if "power" in col.lower() or "voltage" in col.lower():
                drop_mask = (series.pct_change() < -0.1).astype(float)
                feat[f"{col}_drop_count"] = drop_mask.rolling(
                    self.event_window, min_periods=1
                ).sum()

        return feat
