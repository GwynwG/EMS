"""脚本 03: 构建四模块特征。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.feature_engineering.module_feature_builder import ModuleFeatureBuilder
from src.feature_engineering.feature_fusion import FeatureFusion
from src.feature_engineering.feature_selector import FeatureSelector
from src.utils.config_loader import load_app_config, ensure_dir
from src.utils.file_utils import load_csv, save_csv
from src.utils.logger import get_logger

logger = get_logger("03_features")


def main() -> None:
    cfg = load_app_config()
    processed_dir = ensure_dir(cfg["data"]["processed_dir"])

    # 加载清洗后数据
    input_path = processed_dir / "cleaned_data.csv"
    if not input_path.exists():
        logger.error(f"输入文件不存在: {input_path}，请先运行 02")
        return

    df = load_csv(input_path, index_col=0, parse_dates=True)
    logger.info(f"加载数据: {df.shape}")

    # 构建四模块特征
    builder = ModuleFeatureBuilder()
    module_features = builder.build_all_module_features(df)

    # 保存各模块特征
    saved = builder.save_module_features(module_features, str(processed_dir))
    for s in saved:
        logger.info(f"已保存: {s}")

    # 特征融合
    fusion = FeatureFusion()
    fused = fusion.fuse_and_save(module_features, str(processed_dir / "fused_features.csv"))

    # 特征选择
    selector = FeatureSelector(variance_threshold=0.01, correlation_threshold=0.95)
    fused_selected = selector.select(fused)
    save_csv(fused_selected, processed_dir / "fused_features_selected.csv")

    logger.info(f"融合特征: {fused.shape}")
    logger.info(f"选择后特征: {fused_selected.shape}")

    # 输出各模块特征统计
    for module_name, feat_df in module_features.items():
        logger.info(f"  {module_name}: {feat_df.shape[1]} 个特征")


if __name__ == "__main__":
    main()
