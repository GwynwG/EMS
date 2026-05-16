"""DCS 点位映射管理。

管理 raw_tag 到 standard_name 的映射，支持后续真实 DCS 接入。
"""
from __future__ import annotations

from typing import Any

from src.utils.config_loader import load_variable_dictionary


class TagMapping:
    """DCS 点位映射管理器。"""

    def __init__(self) -> None:
        self._variables = load_variable_dictionary()
        self._raw_to_std: dict[str, str] = {}
        self._std_to_raw: dict[str, str] = {}
        for v in self._variables:
            raw = v.get("raw_tag", "")
            std = v.get("standard_name", "")
            if raw and std:
                self._raw_to_std[raw] = std
                self._std_to_raw[std] = raw

    def raw_to_standard(self, raw_tag: str) -> str | None:
        """raw_tag → standard_name。"""
        return self._raw_to_std.get(raw_tag)

    def standard_to_raw(self, standard_name: str) -> str | None:
        """standard_name → raw_tag。"""
        return self._std_to_raw.get(standard_name)

    def rename_columns_raw_to_standard(self, columns: list[str]) -> dict[str, str]:
        """生成 rename 映射字典。"""
        mapping = {}
        for col in columns:
            std = self.raw_to_standard(col)
            if std:
                mapping[col] = std
        return mapping

    def get_all_mappings(self) -> list[dict[str, str]]:
        """返回所有映射关系。"""
        return [
            {"raw_tag": v["raw_tag"], "standard_name": v["standard_name"],
             "module": v.get("module", ""), "chinese_name": v.get("chinese_name", "")}
            for v in self._variables
        ]
