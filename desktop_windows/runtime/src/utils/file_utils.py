"""文件操作工具。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import warnings

import pandas as pd

from src.utils.config_loader import _resolve_path
from src.utils.app_paths import resolve_path


def save_csv(df: pd.DataFrame, path: str | Path, index: bool = False) -> Path:
    """保存 DataFrame 到 CSV。"""
    fp = resolve_path(path, for_write=True)
    fp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=index, encoding="utf-8-sig")
    return fp


def load_csv(path: str | Path, **kwargs) -> pd.DataFrame:
    """加载 CSV 文件。"""
    fp = _resolve_path(path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return pd.read_csv(fp, **kwargs)


def save_json(data: Any, path: str | Path) -> Path:
    """保存 JSON 文件。"""
    fp = resolve_path(path, for_write=True)
    fp.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return fp


def load_json(path: str | Path) -> Any:
    """加载 JSON 文件。"""
    fp = _resolve_path(path)
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)


def list_excel_files(directory: str | Path) -> list[Path]:
    """列出目录下所有 xlsx 文件。"""
    fp = _resolve_path(directory)
    return sorted(fp.glob("*.xlsx"))
