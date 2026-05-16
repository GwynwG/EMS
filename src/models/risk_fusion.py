"""风险融合模块。

融合四模块评分、统计量、异常分数、健康指数、事件特征和模型残差，
输出综合风险分数、风险等级、主异常模块和主异常耦合关系。
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.domain_framework.module_scoring import ModuleScorer
from src.utils.config_loader import load_model_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RiskFusion:
    """综合风险融合器。"""

    def __init__(self) -> None:
        self.scorer = ModuleScorer()
        cfg = load_model_config()
        self.risk_thresholds = cfg.get("risk_fusion", {}).get("risk_thresholds", {
            "normal": 30, "attention": 50, "warning": 70, "severe": 85,
        })

    def compute_risk(
        self,
        module_scores: dict[str, float],
        pca_anomaly_score: float = 0.0,
        if_anomaly_score: float = 0.0,
        health_index: float = 100.0,
        event_penalty: float = 0.0,
        coupling_residuals: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """计算综合风险评估结果。"""
        # 模块风险
        module_risks = {k: 100.0 - v for k, v in module_scores.items()}

        # 综合风险分数
        risk_score = self.scorer.compute_global_risk_score(
            module_scores=module_scores,
            anomaly_score=max(pca_anomaly_score, if_anomaly_score),
            health_index=health_index,
        )

        # 加入事件惩罚
        risk_score = min(100.0, risk_score + event_penalty * 10)

        # 风险等级
        risk_level = self._determine_level(risk_score)

        # 主异常模块
        main_abnormal_module = self.scorer.find_main_abnormal_module(module_scores)

        # 主异常耦合
        main_abnormal_coupling = self.scorer.find_main_abnormal_coupling(
            module_scores, coupling_residuals
        )

        return {
            "risk_score": round(risk_score, 2),
            "risk_level": risk_level,
            "main_abnormal_module": main_abnormal_module,
            "main_abnormal_coupling": main_abnormal_coupling,
            "module_scores": module_scores,
            "module_risks": module_risks,
            "health_index": health_index,
            "pca_anomaly_score": pca_anomaly_score,
            "if_anomaly_score": if_anomaly_score,
        }

    def _determine_level(self, risk_score: float) -> str:
        """确定风险等级。"""
        if risk_score >= self.risk_thresholds.get("severe", 85):
            return "severe"
        elif risk_score >= self.risk_thresholds.get("warning", 70):
            return "warning"
        elif risk_score >= self.risk_thresholds.get("attention", 50):
            return "attention"
        return "normal"

    def compute_batch(
        self,
        module_score_series: dict[str, pd.Series],
        pca_scores: pd.Series,
        if_scores: pd.Series,
        health_indices: pd.Series,
    ) -> pd.DataFrame:
        """批量计算风险评估。"""
        n = len(pca_scores)
        results = []

        for i in range(n):
            ms = {}
            for k, v in module_score_series.items():
                if i < len(v):
                    ms[k] = v.iloc[i] if isinstance(v, pd.Series) else v[i]

            result = self.compute_risk(
                module_scores=ms,
                pca_anomaly_score=pca_scores.iloc[i] if i < len(pca_scores) else 0,
                if_anomaly_score=if_scores.iloc[i] if i < len(if_scores) else 0,
                health_index=health_indices.iloc[i] if i < len(health_indices) else 100,
            )
            results.append(result)

        return pd.DataFrame(results)
