"""PLS 监测模型（预留接口）。

第一版可选实现，保留完整接口供后续扩展。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.utils.config_loader import load_model_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PLSMonitor:
    """PLS 状态监测模型（预留接口）。"""

    def __init__(self) -> None:
        cfg = load_model_config().get("pls", {})
        self.n_components = cfg.get("n_components", 5)
        self.scale = cfg.get("scale", True)
        self.enabled = cfg.get("enabled", False)
        self._is_fitted: bool = False
        self._model: Any = None

    def fit(self, X: pd.DataFrame | np.ndarray, Y: pd.DataFrame | np.ndarray | None = None) -> "PLSMonitor":
        """训练 PLS 模型。"""
        if not self.enabled:
            logger.info("PLS 模型已禁用，跳过训练")
            return self

        try:
            from sklearn.cross_decomposition import PLSRegression
            from sklearn.preprocessing import StandardScaler

            self._scaler = StandardScaler()
            X_arr = X.values if isinstance(X, pd.DataFrame) else X
            X_scaled = self._scaler.fit_transform(X_arr)

            if Y is None:
                # 用 X 自身作为 Y（自回归 PLS）
                Y = X_arr

            self._model = PLSRegression(n_components=self.n_components, scale=self.scale)
            self._model.fit(X_scaled, Y if isinstance(Y, np.ndarray) else Y.values)
            self._is_fitted = True
            logger.info("PLS 模型已训练")
        except ImportError:
            logger.warning("sklearn PLS 不可用")

        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> pd.DataFrame:
        """预测。"""
        if not self._is_fitted or self._model is None:
            # 返回空结果
            n = len(X)
            return pd.DataFrame({
                "pls_anomaly_score": np.zeros(n),
                "is_anomaly": np.zeros(n, dtype=int),
            })

        X_arr = X.values if isinstance(X, pd.DataFrame) else X
        X_scaled = self._scaler.transform(X_arr)
        Y_pred = self._model.predict(X_scaled)

        # 残差作为异常分数
        residual = np.sum((X_scaled - Y_pred) ** 2, axis=1)
        threshold = np.percentile(residual, 99)

        return pd.DataFrame({
            "pls_anomaly_score": residual,
            "is_anomaly": (residual > threshold).astype(int),
        })

    def save(self, path: str | Path) -> None:
        """保存模型。"""
        import joblib
        fp = Path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self._model, "scaler": self._scaler}, fp)

    def load(self, path: str | Path) -> "PLSMonitor":
        """加载模型。"""
        import joblib
        data = joblib.load(path)
        self._model = data["model"]
        self._scaler = data["scaler"]
        self._is_fitted = True
        return self
