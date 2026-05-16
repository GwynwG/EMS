"""模块级状态评分。

基于各模块自身特征和模型输出计算模块级状态评分（0-100，越高越健康）。
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.domain_framework.module_schema import ModuleType, get_module_meta
from src.utils.config_loader import load_model_config


class ModuleScorer:
    """四模块状态评分器。"""

    def __init__(self) -> None:
        cfg = load_model_config()
        self.risk_cfg = cfg.get("risk_fusion", {})
        self.module_weights = self.risk_cfg.get("module_weights", {
            "execution_control": 0.15,
            "energy_input": 0.20,
            "environmental_constraint": 0.20,
            "state_maintenance": 0.45,
        })

    @staticmethod
    def compute_module_score(
        feature_values: pd.Series | dict[str, float],
        reference_stats: dict[str, dict[str, float]] | None = None,
    ) -> float:
        """基于特征值计算单个模块的健康评分。

        使用特征偏离参考统计量的程度来评分。
        偏离越大，分数越低。
        """
        if isinstance(feature_values, dict):
            feature_values = pd.Series(feature_values)

        if feature_values.empty:
            return 100.0

        # 如果没有参考统计量，使用自适应方法
        if reference_stats is None:
            values = feature_values.dropna().values
            if len(values) == 0:
                return 100.0
            # 使用变异系数的反向映射
            mean_val = np.mean(np.abs(values))
            std_val = np.std(values)
            if mean_val < 1e-10:
                return 100.0
            cv = std_val / mean_val
            # CV 映射到 0-100 分，CV 越大分越低
            score = max(0.0, 100.0 - cv * 50.0)
            return float(np.clip(score, 0.0, 100.0))

        # 基于参考统计量的评分
        deviations = []
        for col, val in feature_values.items():
            if col in reference_stats and not np.isnan(val):
                ref = reference_stats[col]
                mean = ref.get("mean", 0)
                std = ref.get("std", 1)
                if std > 1e-10:
                    z = abs(val - mean) / std
                    deviations.append(z)

        if not deviations:
            return 100.0

        # 平均偏离映射到分数
        avg_dev = np.mean(deviations)
        score = max(0.0, 100.0 - avg_dev * 15.0)
        return float(np.clip(score, 0.0, 100.0))

    def compute_all_module_scores(
        self,
        module_features: dict[str, pd.Series | dict[str, float]],
        reference_stats: dict[str, dict[str, dict[str, float]]] | None = None,
    ) -> dict[str, float]:
        """计算所有模块的评分。"""
        scores = {}
        for mod in ModuleType:
            key = mod.value
            feat = module_features.get(key)
            if feat is not None:
                ref = reference_stats.get(key) if reference_stats else None
                scores[key] = self.compute_module_score(feat, ref)
            else:
                scores[key] = 100.0
        return scores

    def compute_global_risk_score(
        self,
        module_scores: dict[str, float],
        anomaly_score: float = 0.0,
        health_index: float = 100.0,
    ) -> float:
        """综合模块评分和全局异常分数计算风险分数（0-100，越高越危险）。"""
        # 模块加权健康度
        weighted_health = 0.0
        total_weight = 0.0
        for mod, weight in self.module_weights.items():
            s = module_scores.get(mod, 100.0)
            weighted_health += s * weight
            total_weight += weight

        if total_weight > 0:
            weighted_health /= total_weight

        # 健康度转风险度
        module_risk = 100.0 - weighted_health

        # 融合全局异常分数
        # anomaly_score 已经是异常度（越高越异常）
        risk = 0.5 * module_risk + 0.3 * anomaly_score + 0.2 * (100.0 - health_index)
        return float(np.clip(risk, 0.0, 100.0))

    @staticmethod
    def determine_risk_level(risk_score: float) -> str:
        """根据风险分数确定风险等级。"""
        cfg = load_model_config()
        thresholds = cfg.get("risk_fusion", {}).get("risk_thresholds", {
            "normal": 30, "attention": 50, "warning": 70, "severe": 85,
        })
        if risk_score >= thresholds.get("severe", 85):
            return "severe"
        elif risk_score >= thresholds.get("warning", 70):
            return "warning"
        elif risk_score >= thresholds.get("attention", 50):
            return "attention"
        return "normal"

    def find_main_abnormal_module(self, module_scores: dict[str, float]) -> str:
        """找出主要异常模块（评分最低的模块）。"""
        if not module_scores:
            return "unknown"
        return min(module_scores, key=module_scores.get)  # type: ignore

    @staticmethod
    def find_main_abnormal_coupling(
        module_scores: dict[str, float],
        coupling_residuals: dict[str, float] | None = None,
    ) -> str:
        """找出主要异常耦合关系。"""
        # 找出评分最低的两个模块
        sorted_modules = sorted(module_scores.items(), key=lambda x: x[1])
        if len(sorted_modules) >= 2:
            m1, m2 = sorted_modules[0][0], sorted_modules[1][0]
            return f"{m1} ↔ {m2}"
        return "无"
