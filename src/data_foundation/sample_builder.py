"""样本构造模块。

支持滑动窗口样本构造，为特征工程和模型训练提供统一的样本格式。
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from src.utils.config_loader import load_feature_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class SampleBuilder:
    """滑动窗口样本构造器。"""

    def __init__(
        self,
        window_length: int | None = None,
        step: int | None = None,
    ) -> None:
        cfg = load_feature_config().get("window", {})
        self.window_length = window_length or cfg.get("length", 60)
        self.step = step or cfg.get("step", 10)

    def build_samples(self, df: pd.DataFrame) -> list[pd.DataFrame]:
        """构建滑动窗口样本列表。"""
        if len(df) < self.window_length:
            logger.warning(f"数据长度 {len(df)} < 窗口长度 {self.window_length}")
            return []

        samples = []
        for start in range(0, len(df) - self.window_length + 1, self.step):
            window = df.iloc[start:start + self.window_length]
            samples.append(window)

        logger.info(f"构建 {len(samples)} 个样本, 窗口={self.window_length}, 步长={self.step}")
        return samples

    def build_sample_matrix(self, df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
        """构建样本矩阵 X (n_samples × n_features) 和特征名列表。

        每个样本展平为一维向量。
        """
        numeric = df.select_dtypes(include=[np.number])
        feature_names = list(numeric.columns)

        samples = self.build_samples(numeric)
        if not samples:
            return np.array([]), feature_names

        X = np.array([s.values.flatten() for s in samples])
        # 生成展平后的特征名
        flat_names = []
        for fname in feature_names:
            for t in range(self.window_length):
                flat_names.append(f"{fname}_t{t}")

        logger.info(f"样本矩阵: X={X.shape}, 特征数={len(flat_names)}")
        return X, flat_names

    def build_labeled_samples(
        self,
        df: pd.DataFrame,
        label_col: str | None = None,
    ) -> tuple[list[pd.DataFrame], list[Any]]:
        """构建带标签的样本。"""
        samples = self.build_samples(df)
        if not label_col:
            return samples, [0] * len(samples)

        labels = []
        for sample in samples:
            if label_col in sample.columns:
                labels.append(sample[label_col].iloc[-1])
            else:
                labels.append(0)

        return samples, labels

    def build_event_triggered_samples(
        self,
        df: pd.DataFrame,
        event_col: str,
        pre_window: int = 30,
        post_window: int = 30,
    ) -> list[pd.DataFrame]:
        """基于事件触发构建样本窗口（预留接口）。"""
        if event_col not in df.columns:
            return []

        event_indices = df.index[df[event_col] > 0]
        samples = []
        for idx in event_indices:
            pos = df.index.get_loc(idx)
            start = max(0, pos - pre_window)
            end = min(len(df), pos + post_window)
            samples.append(df.iloc[start:end])

        logger.info(f"事件触发样本: {len(samples)} 个")
        return samples
