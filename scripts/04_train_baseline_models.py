"""脚本 04: 训练基线模型（PCA、Isolation Forest）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from src.models.pca_monitor import PCAMonitor
from src.models.isolation_forest_model import IsolationForestModel
from src.models.health_index import HealthIndexCalculator
from src.models.risk_fusion import RiskFusion
from src.models.model_registry import ModelRegistry
from src.domain_framework.module_scoring import ModuleScorer
from src.utils.config_loader import load_app_config, ensure_dir
from src.utils.file_utils import load_csv, save_csv
from src.utils.logger import get_logger
from src.visualization.plotting import plot_anomaly_scores, plot_health_index, plot_risk_dashboard

logger = get_logger("04_train")


def main() -> None:
    cfg = load_app_config()
    processed_dir = ensure_dir(cfg["data"]["processed_dir"])
    models_dir = ensure_dir(cfg["output"]["models_dir"])
    figures_dir = ensure_dir(cfg["output"]["figures_dir"])

    # 加载融合特征
    features_path = processed_dir / "fused_features_selected.csv"
    if not features_path.exists():
        features_path = processed_dir / "fused_features.csv"
    if not features_path.exists():
        logger.error("融合特征文件不存在，请先运行 03")
        return

    df = load_csv(features_path, index_col=0, parse_dates=True)
    logger.info(f"加载融合特征: {df.shape}")

    # 只使用数值列
    numeric_df = df.select_dtypes(include=[np.number])
    # 去除 NaN
    numeric_df = numeric_df.ffill().bfill().fillna(0)

    # 分割训练/测试集
    split_idx = int(len(numeric_df) * 0.7)
    train_data = numeric_df.iloc[:split_idx]
    test_data = numeric_df.iloc[split_idx:]

    logger.info(f"训练集: {train_data.shape}, 测试集: {test_data.shape}")

    # ── 训练 PCA ──
    logger.info("训练 PCA 模型...")
    pca_model = PCAMonitor()
    pca_model.fit(train_data)
    pca_train_pred = pca_model.predict(train_data)
    pca_test_pred = pca_model.predict(test_data)

    pca_model.save(str(models_dir / "pca_monitor.joblib"))
    logger.info(f"PCA 训练完成: T²阈值={pca_model.t2_threshold:.4f}, SPE阈值={pca_model.spe_threshold:.4f}")

    # ── 训练 Isolation Forest ──
    logger.info("训练 Isolation Forest...")
    if_model = IsolationForestModel()
    if_model.fit(train_data)
    if_test_pred = if_model.predict(test_data)

    if_model.save(str(models_dir / "isolation_forest.joblib"))
    logger.info("Isolation Forest 训练完成")

    # ── 计算健康指数 ──
    hi_calc = HealthIndexCalculator()
    hi_series = hi_calc.compute_batch(
        pca_scores=pca_test_pred,
        if_scores=if_test_pred,
    )
    hi_series.index = test_data.index

    # ── 模块评分 ──
    scorer = ModuleScorer()
    # 简化模块评分
    module_score_series = {}
    for module in ["execution_control", "energy_input", "environmental_constraint", "state_maintenance"]:
        cols = [c for c in numeric_df.columns if c.startswith(f"{module}__")]
        if cols:
            module_data = test_data[cols]
            scores = []
            for i in range(len(module_data)):
                row = module_data.iloc[i]
                score = ModuleScorer.compute_module_score(row)
                scores.append(score)
            module_score_series[module] = pd.Series(scores, index=test_data.index)

    # ── 风险融合 ──
    risk_fusion = RiskFusion()
    risk_results = risk_fusion.compute_batch(
        module_score_series=module_score_series,
        pca_scores=pca_test_pred["anomaly_score"],
        if_scores=if_test_pred["if_anomaly_score"],
        health_indices=hi_series,
    )

    # 保存结果
    results_df = test_data.copy()
    results_df["pca_anomaly_score"] = pca_test_pred["anomaly_score"].values
    results_df["pca_t2"] = pca_test_pred["t2"].values
    results_df["pca_spe"] = pca_test_pred["spe"].values
    results_df["if_anomaly_score"] = if_test_pred["if_anomaly_score"].values
    results_df["health_index"] = hi_series.values
    results_df["risk_score"] = risk_results["risk_score"].values
    results_df["risk_level"] = risk_results["risk_level"].values

    save_csv(results_df, processed_dir / "model_results.csv")

    # 保存模型结果汇总
    summary = {
        "pca": {
            "n_components": pca_model.pca.n_components_,
            "t2_threshold": pca_model.t2_threshold,
            "spe_threshold": pca_model.spe_threshold,
        },
        "if": {
            "n_estimators": if_model.n_estimators,
            "contamination": if_model.contamination,
        },
        "health_index_mean": float(hi_series.mean()),
        "risk_score_mean": float(risk_results["risk_score"].mean()),
        "risk_level_distribution": risk_results["risk_level"].value_counts().to_dict(),
    }
    logger.info(f"模型结果汇总: {summary}")

    # ── 生成图表 ──
    # 异常分数图
    plot_anomaly_scores(
        pca_test_pred,
        title="PCA 异常分数趋势",
        save_path=str(figures_dir / "pca_anomaly_scores.png"),
    )
    logger.info("已生成: pca_anomaly_scores.png")

    # 健康指数图
    plot_health_index(
        hi_series,
        title="健康指数趋势",
        save_path=str(figures_dir / "health_index_trend.png"),
    )
    logger.info("已生成: health_index_trend.png")

    # 风险仪表盘
    last_risk = {
        "risk_score": float(risk_results["risk_score"].iloc[-1]),
        "risk_level": risk_results["risk_level"].iloc[-1],
        "health_index": float(hi_series.iloc[-1]),
        "main_abnormal_module": "state_maintenance",
        "main_abnormal_coupling": "state_maintenance ↔ execution_control",
        "module_scores": {k: float(v.iloc[-1]) if len(v) > 0 else 100.0 for k, v in module_score_series.items()},
    }
    plot_risk_dashboard(
        last_risk,
        save_path=str(figures_dir / "risk_dashboard.png"),
    )
    logger.info("已生成: risk_dashboard.png")

    # 注册模型
    registry = ModelRegistry(str(models_dir))
    registry.register("pca_monitor", pca_model)
    registry.register("isolation_forest", if_model)
    registry.save_all()

    logger.info("模型训练全部完成")


if __name__ == "__main__":
    main()
