"""四模块特征构造器。

以四模块为单位，分别提取各模块变量的特征。
"""
from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

from src.domain_framework.module_schema import ModuleType
from src.feature_engineering.statistical_features import StatisticalFeatureExtractor
from src.feature_engineering.dynamic_features import DynamicFeatureExtractor
from src.feature_engineering.event_features import EventFeatureExtractor
from src.utils.config_loader import load_feature_config, ensure_dir
from src.utils.file_utils import save_csv
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModuleFeatureBuilder:
    """四模块特征构造器。"""

    def __init__(self) -> None:
        self.cfg = load_feature_config()
        self.stat_extractor = StatisticalFeatureExtractor()
        self.dynamic_extractor = DynamicFeatureExtractor()
        self.event_extractor = EventFeatureExtractor()

    def build_module_features(
        self,
        df: pd.DataFrame,
        module: ModuleType | str,
        window: int = 60,
    ) -> pd.DataFrame:
        """为单个模块构建特征。"""
        module_name = module.value if isinstance(module, ModuleType) else module
        module_cfg = self.cfg.get("features", {}).get(module_name, {})
        raw_features = module_cfg.get("raw_features", [])

        # 过滤出模块可用的列
        available_cols = [c for c in raw_features if c in df.columns]
        if not available_cols:
            logger.warning(f"模块 {module_name} 无可用列")
            return pd.DataFrame()

        logger.info(f"构建模块 {module_name} 特征: {len(available_cols)} 个变量")

        all_features = []

        for col in available_cols:
            series = df[col]
            feat = pd.DataFrame(index=df.index)

            # 统计特征
            stat_feat = self.stat_extractor.extract(series, prefix=col)
            feat = pd.concat([feat, stat_feat], axis=1)

            # 动态特征
            dyn_feat = self.dynamic_extractor.extract(series, prefix=col)
            feat = pd.concat([feat, dyn_feat], axis=1)

            all_features.append(feat)

        # 事件特征
        event_feat = self.event_extractor.extract(df, available_cols)
        if not event_feat.empty:
            all_features.append(event_feat)

        if not all_features:
            return pd.DataFrame()

        result = pd.concat(all_features, axis=1)
        # 去除全 NaN 列
        result = result.dropna(axis=1, how="all")
        # 填充剩余缺失
        result = result.ffill().bfill().fillna(0)

        logger.info(f"模块 {module_name} 特征: {result.shape[1]} 个特征")
        return result

    def build_all_module_features(
        self,
        df: pd.DataFrame,
        window: int = 60,
    ) -> dict[str, pd.DataFrame]:
        """构建所有四模块的特征。"""
        results = {}
        for module in ModuleType:
            feat = self.build_module_features(df, module, window)
            results[module.value] = feat
        return results

    def save_module_features(
        self,
        module_features: dict[str, pd.DataFrame],
        output_dir: str = "data/processed",
    ) -> list[str]:
        """保存各模块特征到 CSV 文件。"""
        saved = []
        for module_name, feat_df in module_features.items():
            if feat_df.empty:
                continue
            filename = f"module_features_{module_name}.csv"
            path = save_csv(feat_df, f"{output_dir}/{filename}")
            saved.append(str(path))
            logger.info(f"已保存: {path}")
        return saved
