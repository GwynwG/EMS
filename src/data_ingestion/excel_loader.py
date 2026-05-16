"""Excel 数据加载器。

支持读取 xlsx 文件、多 sheet、自动/指定时间列识别、基本数据质量检查。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from src.utils.config_loader import _resolve_path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ExcelLoader:
    """Excel 数据加载器。"""

    def __init__(self, time_col: str | None = None) -> None:
        self.time_col = time_col

    def load(self, file_path: str | Path, sheet_name: str | int | None = 0) -> pd.DataFrame:
        """加载单个 Excel 文件。"""
        fp = _resolve_path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"Excel 文件不存在: {fp}")

        logger.info(f"加载 Excel: {fp}, sheet={sheet_name}")
        df = pd.read_excel(fp, sheet_name=sheet_name, engine="openpyxl")

        # 时间列处理
        df = self._resolve_time_column(df)

        logger.info(f"加载完成: {df.shape[0]} 行 × {df.shape[1]} 列")
        return df

    def load_all_sheets(self, file_path: str | Path) -> dict[str, pd.DataFrame]:
        """加载 Excel 所有 sheet。"""
        fp = _resolve_path(file_path)
        xls = pd.ExcelFile(fp, engine="openpyxl")
        result = {}
        for sheet in xls.sheet_names:
            result[sheet] = self.load(fp, sheet_name=sheet)
        return result

    def load_directory(self, directory: str | Path) -> pd.DataFrame:
        """加载目录下所有 xlsx 文件并合并。"""
        dp = _resolve_path(directory)
        files = sorted(dp.glob("*.xlsx"))
        if not files:
            logger.warning(f"目录下无 Excel 文件: {dp}")
            return pd.DataFrame()

        frames = []
        for f in files:
            try:
                df = self.load(f)
                df["_source_file"] = f.name
                frames.append(df)
            except Exception as e:
                logger.error(f"加载失败 {f.name}: {e}")

        if not frames:
            return pd.DataFrame()

        combined = pd.concat(frames, ignore_index=True)
        logger.info(f"合并完成: {len(files)} 个文件, {combined.shape[0]} 行")
        return combined

    def _resolve_time_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """识别并设置时间列。"""
        if self.time_col and self.time_col in df.columns:
            df[self.time_col] = pd.to_datetime(df[self.time_col], errors="coerce")
            df = df.set_index(self.time_col).sort_index()
            return df

        # 自动识别：查找包含 time/date/timestamp 的列
        candidates = [
            c for c in df.columns
            if any(kw in c.lower() for kw in ["time", "date", "timestamp", "时间"])
        ]
        if candidates:
            col = candidates[0]
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df = df.set_index(col).sort_index()
            logger.info(f"自动识别时间列: {col}")
            return df

        # 尝试将第一列作为时间列
        first_col = df.columns[0]
        try:
            converted = pd.to_datetime(df[first_col], errors="coerce")
            if converted.notna().sum() > len(df) * 0.5:
                df[first_col] = converted
                df = df.set_index(first_col).sort_index()
                logger.info(f"使用第一列作为时间列: {first_col}")
                return df
        except Exception:
            pass

        logger.warning("未识别到时间列，使用整数索引")
        return df
