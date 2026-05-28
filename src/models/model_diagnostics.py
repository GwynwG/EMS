"""模型自诊断模块。

监测模型性能退化和数据分布漂移，当模型可能失效时发出告警。
使用 PSI（Population Stability Index）和 KS 统计量评估模型健康度。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ModelHealthReport:
    """模型健康诊断报告。"""
    model_name: str
    psi: float  # Population Stability Index
    ks_stat: float  # KS 统计量
    drift_detected: bool  # 是否检测到漂移
    health_status: str  # "健康", "关注", "失效"
    details: dict[str, Any]


class ModelDiagnostics:
    """模型自诊断器。"""

    # PSI 阈值：<0.1 稳定，0.1-0.25 关注，>0.25 显著漂移
    PSI_THRESHOLD_WARN = 0.10
    PSI_THRESHOLD_ALERT = 0.25

    # KS 阈值：<0.1 优秀，0.1-0.2 可接受，>0.2 模型区分力下降
    KS_THRESHOLD_WARN = 0.15
    KS_THRESHOLD_ALERT = 0.25

    @staticmethod
    def compute_psi(expected: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
        """计算 Population Stability Index（PSI）。

        PSI 衡量两个分布之间的差异：
        PSI = Σ (actual% - expected%) × ln(actual% / expected%)

        Args:
            expected: 参考分布（训练集）
            actual: 当前分布（在线数据）
            n_bins: 分箱数量

        Returns:
            PSI 值（越大漂移越严重）
        """
        # 基于训练集分位数分箱
        min_val = min(expected.min(), actual.min())
        max_val = max(expected.max(), actual.max())
        if max_val - min_val < 1e-10:
            return 0.0

        bins = np.linspace(min_val, max_val, n_bins + 1)

        expected_hist, _ = np.histogram(expected, bins=bins)
        actual_hist, _ = np.histogram(actual, bins=bins)

        # 避免除零
        expected_pct = (expected_hist + 1) / (len(expected) + n_bins)
        actual_pct = (actual_hist + 1) / (len(actual) + n_bins)

        psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
        return float(psi)

    @staticmethod
    def compute_ks(expected: np.ndarray, actual: np.ndarray) -> float:
        """计算 Kolmogorov-Smirnov 统计量。

        KS 衡量两个分布的最大累积差异。

        Args:
            expected: 参考分布
            actual: 当前分布

        Returns:
            KS 统计量（0~1，越大差异越大）
        """
        all_values = np.concatenate([expected, actual])
        all_values.sort()

        cdf_expected = np.searchsorted(np.sort(expected), all_values, side="right") / len(expected)
        cdf_actual = np.searchsorted(np.sort(actual), all_values, side="right") / len(actual)

        ks = float(np.max(np.abs(cdf_expected - cdf_actual)))
        return ks

    def diagnose_model(
        self,
        model_name: str,
        train_scores: np.ndarray,
        current_scores: np.ndarray,
    ) -> ModelHealthReport:
        """诊断单个模型的健康状态。

        Args:
            model_name: 模型名称
            train_scores: 训练集异常分数
            current_scores: 当前在线数据的异常分数

        Returns:
            ModelHealthReport
        """
        psi = self.compute_psi(train_scores, current_scores)
        ks = self.compute_ks(train_scores, current_scores)

        # 综合判定
        if psi > self.PSI_THRESHOLD_ALERT or ks > self.KS_THRESHOLD_ALERT:
            health = "失效"
            drift = True
        elif psi > self.PSI_THRESHOLD_WARN or ks > self.KS_THRESHOLD_WARN:
            health = "关注"
            drift = True
        else:
            health = "健康"
            drift = False

        return ModelHealthReport(
            model_name=model_name,
            psi=round(psi, 4),
            ks_stat=round(ks, 4),
            drift_detected=drift,
            health_status=health,
            details={
                "psi_threshold_warn": self.PSI_THRESHOLD_WARN,
                "psi_threshold_alert": self.PSI_THRESHOLD_ALERT,
                "ks_threshold_warn": self.KS_THRESHOLD_WARN,
                "ks_threshold_alert": self.KS_THRESHOLD_ALERT,
            },
        )

    def diagnose_all(
        self,
        train_df: pd.DataFrame,
        current_df: pd.DataFrame,
        score_columns: list[str] | None = None,
    ) -> list[ModelHealthReport]:
        """诊断所有模型。"""
        if score_columns is None:
            score_columns = [c for c in current_df.columns
                           if c.endswith("_anomaly_score") or c in ["pca_t2", "pca_spe"]]

        reports = []
        for col in score_columns:
            if col in train_df.columns and col in current_df.columns:
                train_vals = train_df[col].dropna().values
                current_vals = current_df[col].dropna().values
                if len(train_vals) > 10 and len(current_vals) > 10:
                    report = self.diagnose_model(col, train_vals, current_vals)
                    reports.append(report)

        return reports

    @staticmethod
    def get_overall_health(reports: list[ModelHealthReport]) -> str:
        """根据所有模型诊断结果返回整体状态。"""
        if not reports:
            return "未知"
        statuses = [r.health_status for r in reports]
        if "失效" in statuses:
            return "模型失效"
        if "关注" in statuses:
            return "需要关注"
        return "模型健康"
