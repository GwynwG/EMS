"""特征融合模块。

将四模块特征融合为统一特征表。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils.file_utils import save_csv
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FeatureFusion:
    """多模块特征融合器。"""

    def fuse(
        self,
        module_features: dict[str, pd.DataFrame],
        add_module_labels: bool = True,
    ) -> pd.DataFrame:
        """将四模块特征融合为统一特征表。"""
        # 确保所有特征表对齐
        aligned = self._align_features(module_features)

        # 拼接
        parts = []
        for module_name, feat_df in aligned.items():
            if feat_df.empty:
                continue
            # 添加模块前缀
            renamed = feat_df.add_prefix(f"{module_name}__")
            parts.append(renamed)

        if not parts:
            logger.warning("无特征可融合")
            return pd.DataFrame()

        fused = pd.concat(parts, axis=1)

        # 处理缺失和无穷
        fused = fused.replace([np.inf, -np.inf], np.nan)
        fused = fused.ffill().bfill().fillna(0)

        logger.info(f"特征融合完成: {fused.shape[1]} 个特征")
        return fused

    @staticmethod
    def _align_features(
        module_features: dict[str, pd.DataFrame],
    ) -> dict[str, pd.DataFrame]:
        """对齐各模块特征的索引。"""
        # 找到最长的索引
        all_indices = []
        for df in module_features.values():
            if not df.empty:
                all_indices.append(df.index)

        if not all_indices:
            return module_features

        # 使用交集索引
        common_index = all_indices[0]
        for idx in all_indices[1:]:
            common_index = common_index.intersection(idx)

        if len(common_index) == 0:
            # 如果没有交集，使用并集
            common_index = all_indices[0]
            for idx in all_indices[1:]:
                common_index = common_index.union(idx)

        aligned = {}
        for name, df in module_features.items():
            if df.empty:
                aligned[name] = df
            else:
                aligned[name] = df.reindex(common_index).ffill().bfill().fillna(0)

        return aligned

    def fuse_and_save(
        self,
        module_features: dict[str, pd.DataFrame],
        output_path: str = "data/processed/fused_features.csv",
    ) -> pd.DataFrame:
        """融合并保存。"""
        fused = self.fuse(module_features)
        if not fused.empty:
            save_csv(fused, output_path)
            logger.info(f"融合特征已保存: {output_path}")
        return fused
