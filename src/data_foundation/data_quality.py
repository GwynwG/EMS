"""数据质量报告生成。"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataQualityReporter:
    """数据质量报告生成器。"""

    def generate(self, df: pd.DataFrame) -> dict[str, Any]:
        """生成完整的数据质量报告。"""
        report: dict[str, Any] = {
            "shape": {"rows": df.shape[0], "columns": df.shape[1]},
            "time_range": self._get_time_range(df),
            "missing": self._missing_report(df),
            "duplicates": int(df.duplicated().sum()),
            "column_stats": self._column_stats(df),
        }
        logger.info(f"数据质量报告已生成: {df.shape[0]} 行 × {df.shape[1]} 列")
        return report

    def generate_text(self, df: pd.DataFrame) -> str:
        """生成可读的文本报告。"""
        r = self.generate(df)
        lines = [
            "=" * 60,
            "数据质量报告",
            "=" * 60,
            f"数据规模: {r['shape']['rows']} 行 × {r['shape']['columns']} 列",
            f"时间范围: {r['time_range']}",
            f"重复行数: {r['duplicates']}",
            "",
            "缺失值统计:",
        ]
        for col, info in r["missing"].items():
            if info["count"] > 0:
                lines.append(
                    f"  {col}: {info['count']} ({info['percent']:.2f}%)"
                )
        lines.append("")
        lines.append("数值列统计:")
        for col, stats in r["column_stats"].items():
            lines.append(
                f"  {col}: mean={stats['mean']:.4f}, std={stats['std']:.4f}, "
                f"min={stats['min']:.4f}, max={stats['max']:.4f}"
            )
        lines.append("=" * 60)
        return "\n".join(lines)

    def _get_time_range(self, df: pd.DataFrame) -> str:
        if isinstance(df.index, pd.DatetimeIndex):
            return f"{df.index.min()} ~ {df.index.max()}"
        return "非时间索引"

    def _missing_report(self, df: pd.DataFrame) -> dict[str, dict[str, Any]]:
        total = len(df)
        report = {}
        for col in df.columns:
            n = int(df[col].isna().sum())
            report[col] = {"count": n, "percent": n / total * 100 if total > 0 else 0}
        return report

    def _column_stats(self, df: pd.DataFrame) -> dict[str, dict[str, float]]:
        numeric = df.select_dtypes(include=[np.number])
        stats = {}
        for col in numeric.columns:
            if col.endswith("_frozen_flag") or col.endswith("_jump_flag"):
                continue
            s = numeric[col]
            stats[col] = {
                "mean": float(s.mean()) if not s.empty else 0.0,
                "std": float(s.std()) if not s.empty else 0.0,
                "min": float(s.min()) if not s.empty else 0.0,
                "max": float(s.max()) if not s.empty else 0.0,
                "median": float(s.median()) if not s.empty else 0.0,
            }
        return stats
