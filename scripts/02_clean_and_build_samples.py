"""脚本 02: 数据清洗与样本构造。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.data_foundation.data_cleaner import DataCleaner
from src.data_foundation.time_alignment import TimeAligner
from src.data_foundation.sample_builder import SampleBuilder
from src.data_foundation.data_quality import DataQualityReporter
from src.utils.config_loader import load_app_config, ensure_dir
from src.utils.file_utils import load_csv, save_csv
from src.utils.logger import get_logger

logger = get_logger("02_clean")


def main() -> None:
    cfg = load_app_config()
    processed_dir = ensure_dir(cfg["data"]["processed_dir"])
    samples_dir = ensure_dir(cfg["data"]["samples_dir"])

    # 加载数据
    input_path = processed_dir / "imported_data.csv"
    if not input_path.exists():
        logger.error(f"输入文件不存在: {input_path}，请先运行 01_import_excel_data.py")
        return

    df = load_csv(input_path, index_col=0, parse_dates=True)
    logger.info(f"加载数据: {df.shape}")

    # 数据清洗
    cleaner = DataCleaner(
        missing_method="ffill",
        missing_limit=10,
        freeze_threshold=1e-8,
        freeze_window=10,
        jump_factor=10.0,
    )
    df_cleaned = cleaner.clean(df)

    # 时间对齐
    aligner = TimeAligner(target_freq="1s", method="ffill")
    df_aligned = aligner.align(df_cleaned)

    # 去除标记列（冻结/跳变标记）
    flag_cols = [c for c in df_aligned.columns if c.endswith("_frozen_flag") or c.endswith("_jump_flag")]
    if flag_cols:
        df_aligned = df_aligned.drop(columns=flag_cols)

    # 保存清洗后数据
    save_csv(df_aligned, processed_dir / "cleaned_data.csv")
    logger.info(f"清洗后数据已保存: {df_aligned.shape}")

    # 质量报告
    reporter = DataQualityReporter()
    report = reporter.generate_text(df_aligned)
    logger.info(f"清洗后数据质量:\n{report}")

    # 样本构造
    builder = SampleBuilder()
    samples = builder.build_samples(df_aligned)
    logger.info(f"构建样本数: {len(samples)}")

    # 保存样本元信息
    sample_info = pd.DataFrame({
        "sample_id": range(len(samples)),
        "start_idx": [s.index[0] for s in samples],
        "end_idx": [s.index[-1] for s in samples],
        "length": [len(s) for s in samples],
    })
    save_csv(sample_info, samples_dir / "sample_info.csv")
    logger.info("样本信息已保存")


if __name__ == "__main__":
    main()
