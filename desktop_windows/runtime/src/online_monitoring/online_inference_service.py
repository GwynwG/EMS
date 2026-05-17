"""在线推理服务。

加载离线训练模型，对实时特征进行推理，输出四模块评分、异常分数、健康指数和风险评估。
"""
from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from src.domain_framework.module_scoring import ModuleScorer
from src.models.health_index import HealthIndexCalculator
from src.models.risk_fusion import RiskFusion
from src.utils.app_paths import resolve_path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OnlineInferenceService:
    """在线推理服务。"""

    def __init__(self) -> None:
        self.scorer = ModuleScorer()
        self.hi_calc = HealthIndexCalculator()
        self.risk_fusion = RiskFusion()

        # 离线模型（由外部加载注入）
        self.pca_model: Any = None
        self.if_model: Any = None
        self.module_models: Any = None

    def load_models(self, models_dir: str = "outputs/models") -> None:
        """加载离线训练好的模型。"""
        from src.models.pca_monitor import PCAMonitor
        from src.models.isolation_forest_model import IsolationForestModel

        base = resolve_path(models_dir)
        pca_path = base / "pca_monitor.joblib"
        if_path = base / "isolation_forest.joblib"

        if pca_path.exists():
            self.pca_model = PCAMonitor().load(pca_path)
            logger.info("在线服务: PCA 模型已加载")

        if if_path.exists():
            self.if_model = IsolationForestModel().load(if_path)
            logger.info("在线服务: IF 模型已加载")

    def _align_features(self, X: pd.DataFrame, model: Any) -> pd.DataFrame:
        """对齐在线特征与模型训练时的特征列。"""
        expected = getattr(model, "_feature_names", [])
        if not expected:
            return X
        # 选择交集列，缺失列填 0
        common = [c for c in expected if c in X.columns]
        if len(common) == len(expected):
            return X[expected]
        aligned = pd.DataFrame(0, index=X.index, columns=expected)
        for c in common:
            aligned[c] = X[c]
        return aligned

    def infer(
        self,
        fused_features: pd.DataFrame,
        module_features: dict[str, pd.DataFrame] | None = None,
    ) -> dict[str, Any]:
        """执行在线推理。"""
        if fused_features.empty:
            return self._empty_result()

        result: dict[str, Any] = {}

        # PCA 推理
        pca_score = 0.0
        if self.pca_model is not None:
            try:
                aligned = self._align_features(fused_features, self.pca_model)
                pca_pred = self.pca_model.predict(aligned)
                pca_score = float(pca_pred["anomaly_score"].iloc[-1])
                result["pca"] = pca_pred.iloc[-1].to_dict()
            except Exception as e:
                logger.warning(f"PCA 推理失败: {e}")

        # IF 推理
        if_score = 0.0
        if self.if_model is not None:
            try:
                aligned = self._align_features(fused_features, self.if_model)
                if_pred = self.if_model.predict(aligned)
                if_score = float(if_pred["if_anomaly_score"].iloc[-1])
                result["if"] = if_pred.iloc[-1].to_dict()
            except Exception as e:
                logger.warning(f"IF 推理失败: {e}")

        # 模块级评分
        module_scores = {}
        if module_features and self.module_models:
            try:
                module_results = self.module_models.predict(module_features)
                module_scores = module_results.get("module_scores", {})
            except Exception:
                pass

        if not module_scores:
            # 使用简化评分
            module_scores = self._simplified_module_scores(fused_features)

        # 健康指数
        health_index = self.hi_calc.compute(
            pca_anomaly_score=pca_score,
            if_anomaly_score=if_score,
            module_scores=module_scores,
        )

        # 风险融合
        risk_result = self.risk_fusion.compute_risk(
            module_scores=module_scores,
            pca_anomaly_score=pca_score,
            if_anomaly_score=if_score,
            health_index=health_index,
        )

        result.update({
            "module_scores": module_scores,
            "health_index": health_index,
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
            "main_abnormal_module": risk_result["main_abnormal_module"],
            "main_abnormal_coupling": risk_result["main_abnormal_coupling"],
        })

        return result

    def _simplified_module_scores(
        self, fused_features: pd.DataFrame
    ) -> dict[str, float]:
        """简化模块评分（基于特征统计）。"""
        scores = {}
        for module in ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]:
            cols = [c for c in fused_features.columns if c.startswith(f"{module}__")]
            if cols:
                values = fused_features[cols].iloc[-1]
                # 基于变异系数的简化评分
                mean_val = values.abs().mean()
                std_val = values.std()
                if mean_val > 1e-10:
                    cv = std_val / mean_val
                    score = max(0.0, 100.0 - cv * 30.0)
                else:
                    score = 100.0
                scores[module] = float(score)
            else:
                scores[module] = 80.0
        return scores

    @staticmethod
    def _empty_result() -> dict[str, Any]:
        return {
            "module_scores": {
                "execution_control": 100.0,
                "energy_input": 100.0,
                "environmental_constraint": 100.0,
                "state_maintenance": 100.0,
            },
            "health_index": 100.0,
            "risk_score": 0.0,
            "risk_level": "normal",
            "main_abnormal_module": "无",
            "main_abnormal_coupling": "无",
        }
