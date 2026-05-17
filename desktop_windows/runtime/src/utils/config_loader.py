"""配置文件加载工具。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.utils.app_paths import ensure_directory, resolve_path


def _resolve_path(path: str | Path) -> Path:
    """将相对路径解析为安装资源或用户运行数据路径。"""
    return resolve_path(path)


def load_yaml(path: str | Path) -> dict[str, Any]:
    """加载 YAML 配置文件并返回字典。"""
    fp = _resolve_path(path)
    if not fp.exists():
        raise FileNotFoundError(f"配置文件不存在: {fp}")
    with open(fp, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_app_config() -> dict[str, Any]:
    """加载应用主配置。"""
    return load_yaml("configs/app_config.yaml")


def load_variable_dictionary() -> list[dict[str, Any]]:
    """加载变量字典，返回变量列表。"""
    cfg = load_yaml("configs/variable_dictionary.yaml")
    return cfg.get("variables", [])


def load_model_config() -> dict[str, Any]:
    """加载模型配置。"""
    return load_yaml("configs/model_config.yaml")


def load_feature_config() -> dict[str, Any]:
    """加载特征工程配置。"""
    return load_yaml("configs/feature_config.yaml")


def load_alarm_rules() -> dict[str, Any]:
    """加载预警规则配置。"""
    return load_yaml("configs/alarm_rules.yaml")


def get_variable_by_module(module: str) -> list[dict[str, Any]]:
    """按模块名过滤变量字典。"""
    all_vars = load_variable_dictionary()
    return [v for v in all_vars if v.get("module") == module and v.get("enabled", True)]


def get_enabled_variables() -> list[dict[str, Any]]:
    """返回所有已启用的变量。"""
    return [v for v in load_variable_dictionary() if v.get("enabled", True)]


def ensure_dir(path: str | Path) -> Path:
    """确保目录存在，返回路径对象。"""
    return ensure_directory(path)
