"""Isolation Forest 异常检测模型。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src.utils.config_loader import load_model_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class IsolationForestModel:
    """Isolation Forest 异常检测模型。"""

    def __init__(self) -> None:
        cfg = load_model_config().get("isolation_forest", {})
        self.n_estimators = cfg.get("n_estimators", 200)
        self.contamination = cfg.get("contamination", 0.05)
        self.max_samples = cfg.get("max_samples", "auto")
        self.random_state = cfg.get("random_state", 42)

        self.model: IsolationForest | None = None
        self.scaler: StandardScaler = StandardScaler()
        self._is_fitted: bool = False
        self._feature_names: list[str] = []

    def fit(self, X: pd.DataFrame | np.ndarray) -> "IsolationForestModel":
        """训练模型。"""
        if isinstance(X, pd.DataFrame):
            self._feature_names = list(X.columns)
            X_arr = X.values
        else:
            X_arr = X

        X_scaled = self.scaler.fit_transform(X_arr)

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            contamination=self.contamination,
            max_samples=self.max_samples,
            random_state=self.random_state,
        )
        self.model.fit(X_scaled)
        self._is_fitted = True
        logger.info(f"Isolation Forest 已训练: n_estimators={self.n_estimators}")
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> pd.DataFrame:
        """预测异常分数。"""
        if not self._is_fitted or self.model is None:
            raise RuntimeError("模型未训练")

        if isinstance(X, pd.DataFrame):
            X_arr = X.values
        else:
            X_arr = X

        X_scaled = self.scaler.transform(X_arr)

        # 异常分数（负值越小越异常）
        raw_scores = self.model.decision_function(X_scaled)
        # 归一化到 0-1（1 = 最异常）
        anomaly_score = 1 - (raw_scores - raw_scores.min()) / (raw_scores.max() - raw_scores.min() + 1e-10)
        predictions = self.model.predict(X_scaled)  # 1=正常, -1=异常

        return pd.DataFrame({
            "if_anomaly_score": anomaly_score,
            "if_raw_score": raw_scores,
            "is_anomaly": (predictions == -1).astype(int),
        })

    def save(self, path: str | Path) -> None:
        """保存模型。"""
        import joblib
        fp = Path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "model": self.model,
            "scaler": self.scaler,
            "feature_names": self._feature_names,
        }, fp)
        logger.info(f"IF 模型已保存: {fp}")

    def load(self, path: str | Path) -> "IsolationForestModel":
        """加载模型。"""
        import joblib
        data = joblib.load(path)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self._feature_names = data.get("feature_names", [])
        self._is_fitted = True
        logger.info(f"IF 模型已加载: {path}")
        return self
