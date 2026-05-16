"""特征选择模块。

提供基于方差、相关性、模型重要性的特征选择方法。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FeatureSelector:
    """特征选择器。"""

    def __init__(self, variance_threshold: float = 0.01, correlation_threshold: float = 0.95) -> None:
        self.variance_threshold = variance_threshold
        self.correlation_threshold = correlation_threshold

    def select(self, df: pd.DataFrame) -> pd.DataFrame:
        """执行特征选择。"""
        logger.info(f"特征选择前: {df.shape[1]} 个特征")

        # 1. 去除低方差特征
        df = self._remove_low_variance(df)

        # 2. 去除高相关特征
        df = self._remove_high_correlation(df)

        logger.info(f"特征选择后: {df.shape[1]} 个特征")
        return df

    def _remove_low_variance(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除低方差特征。"""
        numeric = df.select_dtypes(include=[np.number])
        variances = numeric.var()
        keep = variances[variances > self.variance_threshold].index.tolist()
        removed = [c for c in df.columns if c not in keep and c in numeric.columns]
        if removed:
            logger.info(f"低方差特征移除: {len(removed)} 个")
        return df[keep + [c for c in df.columns if c not in numeric.columns]]

    def _remove_high_correlation(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除高相关特征（保留方差较大的）。"""
        numeric = df.select_dtypes(include=[np.number])
        if numeric.shape[1] < 2:
            return df

        corr_matrix = numeric.corr().abs()
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

        to_drop = set()
        for col in upper.columns:
            high_corr = upper[col][upper[col] > self.correlation_threshold].index.tolist()
            for hc in high_corr:
                # 保留方差较大的
                if numeric[col].var() >= numeric[hc].var():
                    to_drop.add(hc)
                else:
                    to_drop.add(col)

        if to_drop:
            logger.info(f"高相关特征移除: {len(to_drop)} 个")
            df = df.drop(columns=list(to_drop))

        return df

    def get_feature_importance_ranking(
        self, df: pd.DataFrame, target: pd.Series
    ) -> pd.DataFrame:
        """基于相关性计算特征重要性排名。"""
        numeric = df.select_dtypes(include=[np.number])
        correlations = numeric.corrwith(target).abs().sort_values(ascending=False)
        return pd.DataFrame({
            "feature": correlations.index,
            "importance": correlations.values,
        })
