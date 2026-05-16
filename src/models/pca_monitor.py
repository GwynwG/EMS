"""PCA 监测模型。

输出 T² 统计量、SPE/Q 统计量、异常分数和贡献变量。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.utils.config_loader import load_model_config
from src.utils.file_utils import save_csv
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PCAMonitor:
    """PCA 状态监测模型。"""

    def __init__(self) -> None:
        cfg = load_model_config().get("pca", {})
        self.n_components = cfg.get("n_components", 0.95)
        self.whiten = cfg.get("whiten", False)
        self.threshold_percentile = cfg.get("anomaly_threshold_percentile", 99)

        self.pca: PCA | None = None
        self.scaler: StandardScaler = StandardScaler()
        self.t2_threshold: float = 0.0
        self.spe_threshold: float = 0.0
        self._feature_names: list[str] = []
        self._is_fitted: bool = False

    def fit(self, X: pd.DataFrame | np.ndarray) -> "PCAMonitor":
        """训练 PCA 模型。"""
        if isinstance(X, pd.DataFrame):
            self._feature_names = list(X.columns)
            X_arr = X.values
        else:
            X_arr = X

        # 标准化
        X_scaled = self.scaler.fit_transform(X_arr)

        # PCA
        self.pca = PCA(n_components=self.n_components, whiten=self.whiten)
        self.pca.fit(X_scaled)

        # 计算训练集统计量并设定阈值
        scores = self._compute_scores(X_scaled)
        self.t2_threshold = np.percentile(scores["t2"], self.threshold_percentile)
        self.spe_threshold = np.percentile(scores["spe"], self.threshold_percentile)

        self._is_fitted = True
        logger.info(
            f"PCA 模型已训练: n_components={self.pca.n_components_}, "
            f"T²阈值={self.t2_threshold:.4f}, SPE阈值={self.spe_threshold:.4f}"
        )
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> pd.DataFrame:
        """预测，返回 T²、SPE、异常分数和贡献变量。"""
        if not self._is_fitted or self.pca is None:
            raise RuntimeError("模型未训练，请先调用 fit()")

        if isinstance(X, pd.DataFrame):
            X_arr = X.values
        else:
            X_arr = X

        X_scaled = self.scaler.transform(X_arr)
        scores = self._compute_scores(X_scaled)

        # 异常分数 = max(T²/T²_threshold, SPE/SPE_threshold)
        t2_ratio = scores["t2"] / self.t2_threshold if self.t2_threshold > 0 else scores["t2"]
        spe_ratio = scores["spe"] / self.spe_threshold if self.spe_threshold > 0 else scores["spe"]
        anomaly_score = np.maximum(t2_ratio, spe_ratio)

        # 贡献变量
        contributions = self._compute_contributions(X_scaled)

        result = pd.DataFrame({
            "t2": scores["t2"],
            "spe": scores["spe"],
            "anomaly_score": anomaly_score,
            "is_anomaly": (anomaly_score > 1.0).astype(int),
        })

        # 添加贡献最大的变量
        if contributions is not None and self._feature_names:
            result["top_contributor"] = [
                self._feature_names[np.argmax(np.abs(c))] for c in contributions
            ]
            result["top_contribution"] = [
                np.max(np.abs(c)) for c in contributions
            ]

        return result

    def _compute_scores(self, X_scaled: np.ndarray) -> dict[str, np.ndarray]:
        """计算 T² 和 SPE 统计量。"""
        if self.pca is None:
            return {"t2": np.zeros(len(X_scaled)), "spe": np.zeros(len(X_scaled))}

        # 主成分得分
        T = self.pca.transform(X_scaled)
        eigenvalues = self.pca.explained_variance_
        eigenvalues = np.maximum(eigenvalues, 1e-10)

        # T² = Σ(t_i² / λ_i)
        t2 = np.sum(T ** 2 / eigenvalues, axis=1)

        # SPE = ||X - X̂||²
        X_reconstructed = self.pca.inverse_transform(T)
        spe = np.sum((X_scaled - X_reconstructed) ** 2, axis=1)

        return {"t2": t2, "spe": spe}

    def _compute_contributions(self, X_scaled: np.ndarray) -> np.ndarray | None:
        """计算各变量对异常的贡献。"""
        if self.pca is None or not self._feature_names:
            return None

        T = self.pca.transform(X_scaled)
        X_reconstructed = self.pca.inverse_transform(T)
        contributions = X_scaled - X_reconstructed
        return contributions

    def save(self, path: str | Path) -> None:
        """保存模型。"""
        import joblib
        fp = Path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "pca": self.pca,
            "scaler": self.scaler,
            "t2_threshold": self.t2_threshold,
            "spe_threshold": self.spe_threshold,
            "feature_names": self._feature_names,
        }, fp)
        logger.info(f"PCA 模型已保存: {fp}")

    def load(self, path: str | Path) -> "PCAMonitor":
        """加载模型。"""
        import joblib
        data = joblib.load(path)
        self.pca = data["pca"]
        self.scaler = data["scaler"]
        self.t2_threshold = data["t2_threshold"]
        self.spe_threshold = data["spe_threshold"]
        self._feature_names = data["feature_names"]
        self._is_fitted = True
        logger.info(f"PCA 模型已加载: {path}")
        return self
