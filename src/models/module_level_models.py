"""模块级模型。

为每个模块独立训练 PCA 模型，输出模块级状态评分。
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.domain_framework.module_schema import ModuleType
from src.domain_framework.module_scoring import ModuleScorer
from src.models.pca_monitor import PCAMonitor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModuleLevelModels:
    """四模块级独立监测模型。"""

    def __init__(self) -> None:
        self.models: dict[str, PCAMonitor] = {}
        self.scorer = ModuleScorer()
        self._reference_stats: dict[str, dict[str, dict[str, float]]] = {}

    def fit(self, module_features: dict[str, pd.DataFrame]) -> "ModuleLevelModels":
        """为每个模块训练独立 PCA 模型。"""
        for module_name, feat_df in module_features.items():
            if feat_df.empty:
                logger.warning(f"模块 {module_name} 无特征数据，跳过")
                continue

            # 保存参考统计量
            self._reference_stats[module_name] = {}
            for col in feat_df.columns:
                self._reference_stats[module_name][col] = {
                    "mean": float(feat_df[col].mean()),
                    "std": float(feat_df[col].std()),
                }

            # 训练模块级 PCA
            model = PCAMonitor()
            try:
                model.fit(feat_df)
                self.models[module_name] = model
                logger.info(f"模块 {module_name} PCA 已训练: {feat_df.shape[1]} 特征")
            except Exception as e:
                logger.error(f"模块 {module_name} 训练失败: {e}")

        return self

    def predict(self, module_features: dict[str, pd.DataFrame]) -> dict[str, Any]:
        """预测各模块状态。"""
        results = {}
        module_scores = {}

        for module_name, feat_df in module_features.items():
            if module_name in self.models and not feat_df.empty:
                pred = self.models[module_name].predict(feat_df)
                anomaly_score = float(pred["anomaly_score"].mean())
                # 模块评分 = 100 - 异常度 * 惩罚系数
                score = max(0.0, 100.0 - anomaly_score * 20.0)
                module_scores[module_name] = score
                results[module_name] = {
                    "anomaly_score": anomaly_score,
                    "score": score,
                    "predictions": pred,
                }
            else:
                module_scores[module_name] = 100.0
                results[module_name] = {
                    "anomaly_score": 0.0,
                    "score": 100.0,
                }

        results["module_scores"] = module_scores
        return results

    def get_module_scores_from_raw(
        self,
        module_features: dict[str, pd.Series | dict[str, float]],
    ) -> dict[str, float]:
        """从原始特征值计算模块评分。"""
        return self.scorer.compute_all_module_scores(
            module_features, self._reference_stats
        )
