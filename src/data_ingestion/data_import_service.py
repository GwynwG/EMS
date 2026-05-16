"""数据导入服务。

统一管理 Excel 导入、变量映射和初步数据质量检查。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.data_ingestion.excel_loader import ExcelLoader
from src.domain_framework.module_mapper import ModuleMapper
from src.utils.config_loader import load_app_config, ensure_dir
from src.utils.file_utils import save_csv
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataImportService:
    """数据导入服务。"""

    def __init__(self, time_col: str | None = None) -> None:
        self.loader = ExcelLoader(time_col=time_col)
        self.mapper = ModuleMapper()

    def import_excel(self, file_path: str | Path) -> pd.DataFrame:
        """导入单个 Excel 文件。"""
        df = self.loader.load(file_path)
        self._log_quality_summary(df)
        return df

    def import_directory(self, directory: str | Path) -> pd.DataFrame:
        """导入目录下所有 Excel 文件。"""
        df = self.loader.load_directory(directory)
        if not df.empty:
            self._log_quality_summary(df)
        return df

    def import_and_save(
        self,
        source_dir: str | Path,
        output_name: str = "imported_data.csv",
    ) -> pd.DataFrame:
        """导入数据并保存到 processed 目录。"""
        cfg = load_app_config()
        processed_dir = ensure_dir(cfg["data"]["processed_dir"])

        df = self.import_directory(source_dir)
        if df.empty:
            logger.warning("无数据可导入")
            return df

        # 移除源文件标记列
        if "_source_file" in df.columns:
            df = df.drop(columns=["_source_file"])

        # 保存
        out_path = save_csv(df, processed_dir / output_name)
        logger.info(f"数据已保存: {out_path}")
        return df

    def _log_quality_summary(self, df: pd.DataFrame) -> None:
        """输出数据质量摘要。"""
        total = df.shape[0] * df.shape[1]
        missing = df.isna().sum().sum()
        logger.info(
            f"数据质量摘要: {df.shape[0]} 行 × {df.shape[1]} 列, "
            f"缺失率 {missing/total*100:.2f}%"
        )

        # 检查哪些列属于已知模块
        col_module = self.mapper.classify_columns(list(df.columns))
        for mod, cols in col_module.items():
            if cols:
                logger.info(f"  模块 {mod}: {len(cols)} 个变量已匹配")
