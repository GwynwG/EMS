"""变量字典管理。

提供变量查询、验证、分组等功能。
"""
from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from src.utils.config_loader import load_variable_dictionary
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VariableDictionary:
    """变量字典管理器。"""

    def __init__(self) -> None:
        self._variables = load_variable_dictionary()
        self._by_name: dict[str, dict[str, Any]] = {
            v["standard_name"]: v for v in self._variables
        }
        self._by_tag: dict[str, dict[str, Any]] = {
            v["raw_tag"]: v for v in self._variables
        }

    @property
    def all_variables(self) -> list[dict[str, Any]]:
        return self._variables

    def get_by_standard_name(self, name: str) -> dict[str, Any] | None:
        return self._by_name.get(name)

    def get_by_raw_tag(self, tag: str) -> dict[str, Any] | None:
        return self._by_tag.get(tag)

    def get_enabled(self) -> list[dict[str, Any]]:
        return [v for v in self._variables if v.get("enabled", True)]

    def get_by_module(self, module: str) -> list[dict[str, Any]]:
        return [v for v in self._variables if v.get("module") == module]

    def get_standard_names_by_module(self, module: str) -> list[str]:
        return [v["standard_name"] for v in self.get_by_module(module)]

    def validate_dataframe(self, df: pd.DataFrame) -> dict[str, Any]:
        """验证 DataFrame 是否包含变量字典中的变量。"""
        enabled = self.get_enabled()
        present = []
        missing = []
        for v in enabled:
            if v["standard_name"] in df.columns:
                present.append(v["standard_name"])
            else:
                missing.append(v["standard_name"])
        return {
            "total_expected": len(enabled),
            "present": present,
            "missing": missing,
            "coverage": len(present) / len(enabled) * 100 if enabled else 0,
        }

    def get_module_summary(self) -> dict[str, int]:
        """返回各模块变量数量统计。"""
        summary: dict[str, int] = {}
        for v in self._variables:
            mod = v.get("module", "unknown")
            summary[mod] = summary.get(mod, 0) + 1
        return summary
