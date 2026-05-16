"""健康指数（Health Index）计算。

输出 0-100 健康指数，数值越高代表设备状态越健康。
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from src.utils.config_loader import load_model_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class HealthIndexCalculator:
    """健康指数计算器。"""

    def __init__(self) -> None:
        cfg = load_model_config().get("health_index", {})
        self.weights = cfg.get("weights", {
            "pca_score": 0.25,
            "isolation_forest_score": 0.25,
            "module_scores": 0.35,
            "event_penalty": 0.15,
        })
        self.decay_factor = cfg.get("decay_factor", 0.95)

    def compute(
        self,
        pca_anomaly_score: float | np.ndarray = 0.0,
        if_anomaly_score: float | np.ndarray = 0.0,
        module_scores: dict[str, float] | None = None,
        event_penalty: float | np.ndarray = 0.0,
    ) -> float | np.ndarray:
        """计算健康指数。

        Args:
            pca_anomaly_score: PCA 异常分数（0-1，越高越异常）
            if_anomaly_score: IF 异常分数（0-1，越高越异常）
            module_scores: 四模块评分字典（0-100，越高越健康）
            event_penalty: 事件惩罚分数（0-1）

        Returns:
            0-100 健康指数
        """
        # PCA 部分：异常分数转健康分
        pca_health = np.clip(1.0 - pca_anomaly_score, 0, 1) * 100

        # IF 部分
        if_health = np.clip(1.0 - if_anomaly_score, 0, 1) * 100

        # 模块部分：加权平均
        if module_scores:
            mod_health = np.mean(list(module_scores.values()))
        else:
            mod_health = 80.0  # 默认

        # 事件惩罚
        event_health = np.clip(1.0 - event_penalty, 0, 1) * 100

        # 加权融合
        hi = (
            self.weights["pca_score"] * pca_health
            + self.weights["isolation_forest_score"] * if_health
            + self.weights["module_scores"] * mod_health
            + self.weights["event_penalty"] * event_health
        )

        hi = np.clip(hi, 0, 100)
        return float(hi) if np.isscalar(hi) else hi

    def compute_batch(
        self,
        pca_scores: pd.DataFrame,
        if_scores: pd.DataFrame,
        module_scores: dict[str, pd.Series] | None = None,
    ) -> pd.Series:
        """批量计算健康指数。"""
        n = len(pca_scores)

        pca_anomaly = pca_scores.get("anomaly_score", pd.Series(np.zeros(n)))
        if_anomaly = if_scores.get("if_anomaly_score", pd.Series(np.zeros(n)))

        hi_values = []
        for i in range(n):
            ms = {}
            if module_scores:
                for k, v in module_scores.items():
                    if isinstance(v, pd.Series) and i < len(v):
                        ms[k] = v.iloc[i]
                    elif isinstance(v, (list, np.ndarray)) and i < len(v):
                        ms[k] = v[i]

            hi = self.compute(
                pca_anomaly_score=pca_anomaly.iloc[i] if i < len(pca_anomaly) else 0,
                if_anomaly_score=if_anomaly.iloc[i] if i < len(if_anomaly) else 0,
                module_scores=ms if ms else None,
            )
            hi_values.append(hi)

        return pd.Series(hi_values, name="health_index")

    @staticmethod
    def get_health_level(hi: float) -> str:
        """根据健康指数返回状态描述。"""
        if hi >= 80:
            return "健康"
        elif hi >= 60:
            return "亚健康"
        elif hi >= 40:
            return "异常"
        else:
            return "严重异常"
