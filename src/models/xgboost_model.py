"""XGBoost 模型（预留接口）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.utils.config_loader import load_model_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class XGBoostModel:
    """XGBoost 异常检测/分类模型（预留接口）。"""

    def __init__(self) -> None:
        cfg = load_model_config().get("xgboost", {})
        self.n_estimators = cfg.get("n_estimators", 100)
        self.max_depth = cfg.get("max_depth", 6)
        self.learning_rate = cfg.get("learning_rate", 0.1)
        self.random_state = cfg.get("random_state", 42)
        self.enabled = cfg.get("enabled", False)
        self._model: Any = None
        self._is_fitted: bool = False

    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray | None = None) -> "XGBoostModel":
        """训练模型。"""
        if not self.enabled:
            logger.info("XGBoost 模型已禁用")
            return self

        try:
            import xgboost as xgb
            X_arr = X.values if isinstance(X, pd.DataFrame) else X

            if y is None:
                # 无监督模式：使用自编码器思路
                y = np.zeros(len(X_arr))

            self._model = xgb.XGBClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                learning_rate=self.learning_rate,
                random_state=self.random_state,
                use_label_encoder=False,
                eval_metric="logloss",
            )
            self._model.fit(X_arr, y)
            self._is_fitted = True
            logger.info("XGBoost 模型已训练")
        except ImportError:
            logger.warning("xgboost 未安装，跳过训练")

        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> pd.DataFrame:
        """预测。"""
        n = len(X)
        if not self._is_fitted or self._model is None:
            return pd.DataFrame({
                "xgb_anomaly_score": np.zeros(n),
                "is_anomaly": np.zeros(n, dtype=int),
            })

        X_arr = X.values if isinstance(X, pd.DataFrame) else X
        proba = self._model.predict_proba(X_arr)[:, 1] if hasattr(self._model, "predict_proba") else self._model.predict(X_arr)

        return pd.DataFrame({
            "xgb_anomaly_score": proba,
            "is_anomaly": (proba > 0.5).astype(int),
        })

    def save(self, path: str | Path) -> None:
        import joblib
        fp = Path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._model, fp)

    def load(self, path: str | Path) -> "XGBoostModel":
        import joblib
        self._model = joblib.load(path)
        self._is_fitted = True
        return self
