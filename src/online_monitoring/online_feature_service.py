"""在线特征服务。

从流缓冲区提取四模块特征，供在线推理使用。
"""
from __future__ import annotations

import pandas as pd

from src.domain_framework.module_schema import ModuleType
from src.feature_engineering.module_feature_builder import ModuleFeatureBuilder
from src.feature_engineering.feature_fusion import FeatureFusion
from src.online_monitoring.stream_buffer import StreamBuffer
from src.utils.logger import get_logger

logger = get_logger(__name__)


class OnlineFeatureService:
    """在线特征提取服务。"""

    def __init__(self, window_size: int = 60) -> None:
        self.window_size = window_size
        self.feature_builder = ModuleFeatureBuilder()
        self.fusion = FeatureFusion()

    def extract_features(
        self,
        buffer: StreamBuffer,
    ) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
        """从缓冲区提取四模块特征和融合特征。"""
        # 获取滑动窗口数据
        window_data = buffer.get_window(self.window_size)
        if window_data.empty or len(window_data) < 10:
            return {}, pd.DataFrame()

        # 按模块提取特征
        module_features = {}
        for module in ModuleType:
            feat = self.feature_builder.build_module_features(
                window_data, module, window=self.window_size
            )
            if not feat.empty:
                # 取最后一行作为当前特征
                module_features[module.value] = feat

        # 融合特征
        if module_features:
            fused = self.fusion.fuse(module_features)
            # 取最后一行
            if not fused.empty:
                current_fused = fused.iloc[[-1]]
            else:
                current_fused = pd.DataFrame()
        else:
            current_fused = pd.DataFrame()

        return module_features, current_fused

    def extract_module_summary(
        self,
        module_features: dict[str, pd.DataFrame],
    ) -> dict[str, pd.Series]:
        """提取各模块当前特征摘要（最后一行）。"""
        summary = {}
        for module_name, feat_df in module_features.items():
            if not feat_df.empty:
                summary[module_name] = feat_df.iloc[-1]
        return summary
