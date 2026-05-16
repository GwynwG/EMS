"""Autoencoder 模型（预留接口）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from src.utils.config_loader import load_model_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AutoencoderModel:
    """Autoencoder 异常检测模型（预留接口）。"""

    def __init__(self) -> None:
        cfg = load_model_config().get("autoencoder", {})
        self.encoding_dim = cfg.get("encoding_dim", 16)
        self.epochs = cfg.get("epochs", 50)
        self.batch_size = cfg.get("batch_size", 32)
        self.threshold_percentile = cfg.get("threshold_percentile", 99)
        self.enabled = cfg.get("enabled", False)
        self._model: Any = None
        self._threshold: float = 0.0
        self._is_fitted: bool = False

    def fit(self, X: pd.DataFrame | np.ndarray) -> "AutoencoderModel":
        """训练模型。"""
        if not self.enabled:
            logger.info("Autoencoder 模型已禁用")
            return self

        try:
            import tensorflow as tf
            from tensorflow import keras

            X_arr = X.values if isinstance(X, pd.DataFrame) else X
            input_dim = X_arr.shape[1]

            # 构建自编码器
            encoder = keras.Sequential([
                keras.layers.Dense(self.encoding_dim * 2, activation="relu", input_shape=(input_dim,)),
                keras.layers.Dense(self.encoding_dim, activation="relu"),
            ])
            decoder = keras.Sequential([
                keras.layers.Dense(self.encoding_dim * 2, activation="relu", input_shape=(self.encoding_dim,)),
                keras.layers.Dense(input_dim, activation="linear"),
            ])

            self._model = keras.Sequential([encoder, decoder])
            self._model.compile(optimizer="adam", loss="mse")
            self._model.fit(X_arr, X_arr, epochs=self.epochs, batch_size=self.batch_size,
                           validation_split=0.1, verbose=0)

            # 计算重建误差阈值
            reconstructed = self._model.predict(X_arr, verbose=0)
            mse = np.mean((X_arr - reconstructed) ** 2, axis=1)
            self._threshold = np.percentile(mse, self.threshold_percentile)
            self._is_fitted = True
            logger.info(f"Autoencoder 已训练, 阈值={self._threshold:.6f}")
        except ImportError:
            logger.warning("tensorflow 未安装，跳过 Autoencoder 训练")

        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> pd.DataFrame:
        """预测。"""
        n = len(X)
        if not self._is_fitted or self._model is None:
            return pd.DataFrame({
                "ae_anomaly_score": np.zeros(n),
                "is_anomaly": np.zeros(n, dtype=int),
            })

        X_arr = X.values if isinstance(X, pd.DataFrame) else X
        reconstructed = self._model.predict(X_arr, verbose=0)
        mse = np.mean((X_arr - reconstructed) ** 2, axis=1)

        return pd.DataFrame({
            "ae_anomaly_score": mse,
            "ae_reconstruction_error": mse,
            "is_anomaly": (mse > self._threshold).astype(int),
        })

    def save(self, path: str | Path) -> None:
        import joblib
        fp = Path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"model": self._model, "threshold": self._threshold}, fp)

    def load(self, path: str | Path) -> "AutoencoderModel":
        import joblib
        data = joblib.load(path)
        self._model = data["model"]
        self._threshold = data["threshold"]
        self._is_fitted = True
        return self
