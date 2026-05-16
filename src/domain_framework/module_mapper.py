"""模块映射器：将变量字典中的变量映射到四模块。"""
from __future__ import annotations

from typing import Any

from src.domain_framework.module_schema import ModuleType, get_module_variables
from src.utils.config_loader import load_variable_dictionary


class ModuleMapper:
    """管理变量到模块的映射关系。"""

    def __init__(self) -> None:
        self._var_dict = load_variable_dictionary()
        self._name_to_var: dict[str, dict[str, Any]] = {
            v["standard_name"]: v for v in self._var_dict if v.get("enabled", True)
        }
        self._module_vars: dict[str, list[str]] = {}
        for v in self._var_dict:
            if v.get("enabled", True):
                mod = v["module"]
                self._module_vars.setdefault(mod, []).append(v["standard_name"])

    def get_variables_for_module(self, module: ModuleType | str) -> list[str]:
        """返回指定模块的标准变量名列表。"""
        key = module.value if isinstance(module, ModuleType) else module
        return self._module_vars.get(key, [])

    def get_module_for_variable(self, standard_name: str) -> str | None:
        """返回变量所属模块名。"""
        v = self._name_to_var.get(standard_name)
        return v["module"] if v else None

    def classify_columns(self, columns: list[str]) -> dict[str, list[str]]:
        """将 DataFrame 列名按模块分类。"""
        result: dict[str, list[str]] = {m.value: [] for m in ModuleType}
        for col in columns:
            mod = self.get_module_for_variable(col)
            if mod and mod in result:
                result[mod].append(col)
        return result

    def get_all_standard_names(self) -> list[str]:
        """返回所有已启用变量的标准名。"""
        return list(self._name_to_var.keys())

    def get_raw_tag(self, standard_name: str) -> str | None:
        """返回变量对应的原始 DCS 点位。"""
        v = self._name_to_var.get(standard_name)
        return v.get("raw_tag") if v else None

    def build_tag_mapping(self) -> dict[str, str]:
        """构建 standard_name -> raw_tag 映射。"""
        return {
            name: v.get("raw_tag", name)
            for name, v in self._name_to_var.items()
        }
