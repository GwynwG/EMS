"""数据清洗模块。

处理缺失值、重复值、异常跳变、冻结值等问题。
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataCleaner:
    """数据清洗器。"""

    def __init__(
        self,
        missing_method: str = "ffill",
        missing_limit: int = 10,
        freeze_threshold: float = 1e-8,
        freeze_window: int = 10,
        jump_factor: float = 10.0,
    ) -> None:
        self.missing_method = missing_method
        self.missing_limit = missing_limit
        self.freeze_threshold = freeze_threshold
        self.freeze_window = freeze_window
        self.jump_factor = jump_factor

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """执行完整清洗流程。"""
        logger.info(f"开始数据清洗: {df.shape}")
        df = df.copy()

        # 1. 去除完全重复行
        n_dup = df.duplicated().sum()
        if n_dup > 0:
            df = df.drop_duplicates()
            logger.info(f"去除重复行: {n_dup}")

        # 2. 去除重复时间戳
        if hasattr(df.index, 'duplicated'):
            n_dup_idx = df.index.duplicated().sum()
            if n_dup_idx > 0:
                df = df[~df.index.duplicated(keep="first")]
                logger.info(f"去除重复时间戳: {n_dup_idx}")

        # 3. 缺失值处理
        df = self._handle_missing(df)

        # 4. 冻结值标记
        df = self._detect_frozen(df)

        # 5. 异常跳变标记
        df = self._detect_jumps(df)

        logger.info(f"清洗完成: {df.shape}")
        return df

    def _handle_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值。"""
        missing_before = df.isna().sum().sum()

        if self.missing_method == "ffill":
            df = df.ffill(limit=self.missing_limit)
        elif self.missing_method == "bfill":
            df = df.bfill(limit=self.missing_limit)
        elif self.missing_method == "interpolate":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            df[numeric_cols] = df[numeric_cols].interpolate(
                method="linear", limit=self.missing_limit
            )
        elif self.missing_method == "drop":
            df = df.dropna()

        # 剩余缺失用中位数填充
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isna().any():
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)

        missing_after = df.isna().sum().sum()
        logger.info(f"缺失值: {missing_before} → {missing_after}")
        return df

    def _detect_frozen(self, df: pd.DataFrame) -> pd.DataFrame:
        """检测冻结值（连续多行完全相同）。"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        frozen_mask = pd.DataFrame(False, index=df.index, columns=numeric_cols)

        for col in numeric_cols:
            vals = df[col].values
            for i in range(self.freeze_window, len(vals)):
                window = vals[i - self.freeze_window:i]
                if np.std(window) < self.freeze_threshold:
                    frozen_mask.iloc[i][col] = True

        # 将冻结值标记添加到 DataFrame
        for col in numeric_cols:
            if frozen_mask[col].any():
                df[f"{col}_frozen_flag"] = frozen_mask[col].astype(int)
                n_frozen = frozen_mask[col].sum()
                logger.info(f"  {col}: 检测到 {n_frozen} 个冻结值")

        return df

    def _detect_jumps(self, df: pd.DataFrame) -> pd.DataFrame:
        """检测异常跳变。"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col.endswith("_frozen_flag"):
                continue
            diff = df[col].diff().abs()
            std_val = df[col].std()
            if std_val > 0:
                jump_mask = diff > self.jump_factor * std_val
                n_jumps = jump_mask.sum()
                if n_jumps > 0:
                    df[f"{col}_jump_flag"] = jump_mask.astype(int)
                    logger.info(f"  {col}: 检测到 {n_jumps} 个异常跳变")

        return df
