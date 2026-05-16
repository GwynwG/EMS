"""模型注册表。

统一管理所有模型的保存、加载和版本管理。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from src.utils.config_loader import _resolve_path, ensure_dir
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelRegistry:
    """模型注册表。"""

    def __init__(self, models_dir: str = "outputs/models") -> None:
        self.models_dir = _resolve_path(models_dir)
        ensure_dir(self.models_dir)
        self._registry: dict[str, dict[str, Any]] = {}

    def register(self, name: str, model: Any, metadata: dict[str, Any] | None = None) -> None:
        """注册模型。"""
        self._registry[name] = {
            "model": model,
            "metadata": metadata or {},
        }
        logger.info(f"模型已注册: {name}")

    def get(self, name: str) -> Any:
        """获取模型。"""
        entry = self._registry.get(name)
        if entry is None:
            raise KeyError(f"模型未注册: {name}")
        return entry["model"]

    def save(self, name: str) -> Path:
        """保存已注册模型到磁盘。优先使用模型自身的 save 方法。"""
        entry = self._registry.get(name)
        if entry is None:
            raise KeyError(f"模型未注册: {name}")

        model = entry["model"]
        path = self.models_dir / f"{name}.joblib"

        # 如果模型有 save 方法，使用它自己的序列化格式
        if hasattr(model, "save") and callable(model.save):
            model.save(str(path))
        else:
            joblib.dump(entry, path)

        logger.info(f"模型已保存: {path}")
        return path

    def load(self, name: str) -> Any:
        """从磁盘加载模型。"""
        path = self.models_dir / f"{name}.joblib"
        if not path.exists():
            raise FileNotFoundError(f"模型文件不存在: {path}")

        data = joblib.load(path)
        self._registry[name] = data
        logger.info(f"模型已加载: {path}")
        return data["model"]

    def save_all(self) -> list[str]:
        """保存所有已注册模型。"""
        saved = []
        for name in self._registry:
            self.save(name)
            saved.append(name)
        return saved

    def list_models(self) -> list[str]:
        """列出所有已注册模型。"""
        return list(self._registry.keys())

    def list_saved(self) -> list[str]:
        """列出磁盘上已保存的模型。"""
        return [f.stem for f in self.models_dir.glob("*.joblib")]
