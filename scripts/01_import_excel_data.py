"""脚本 01: 导入 Excel 数据。

如果 data/raw_excel/ 下没有数据，则自动生成 demo 数据。
"""
from __future__ import annotations

import sys
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from src.data_ingestion.data_import_service import DataImportService
from src.data_foundation.data_quality import DataQualityReporter
from src.utils.config_loader import load_app_config, ensure_dir, _resolve_path
from src.utils.logger import get_logger

logger = get_logger("01_import")


def generate_demo_data(output_path: str | Path, n_rows: int = 5000) -> pd.DataFrame:
    """生成面向生产场景的多元异构数据模拟数据。"""
    logger.info(f"生成 demo 数据: {n_rows} 行")

    np.random.seed(42)
    timestamps = pd.date_range("2024-01-01", periods=n_rows, freq="1s")

    # 基础工况
    base_temp = 800.0  # 基础温度
    base_pressure = 0.5  # 基础压力 MPa

    data = pd.DataFrame({"timestamp": timestamps})

    # ── 执行控制模块 ──
    data["setpoint_temperature"] = base_temp + np.random.normal(0, 5, n_rows)
    data["setpoint_pressure"] = base_pressure + np.random.normal(0, 0.02, n_rows)
    data["control_mode"] = np.random.choice([0, 1, 2], n_rows, p=[0.05, 0.85, 0.10])
    data["valve_position_main"] = 50 + np.random.normal(0, 5, n_rows)
    data["valve_position_cooling"] = 40 + np.random.normal(0, 3, n_rows)
    data["interlock_status"] = np.zeros(n_rows)
    data["actuator_feedback"] = 50 + np.random.normal(0, 3, n_rows)

    # ── 能量输入模块 ──
    data["supply_voltage"] = 380 + np.random.normal(0, 5, n_rows)
    data["supply_current"] = 100 + np.random.normal(0, 10, n_rows)
    data["active_power"] = data["supply_voltage"] * data["supply_current"] / 1000 + np.random.normal(0, 0.5, n_rows)
    data["reactive_power"] = data["active_power"] * 0.3 + np.random.normal(0, 0.2, n_rows)
    data["power_factor"] = 0.85 + np.random.normal(0, 0.03, n_rows)
    data["energy_efficiency"] = 85 + np.random.normal(0, 3, n_rows)
    data["power_frequency"] = 50 + np.random.normal(0, 0.1, n_rows)

    # ── 环境约束模块 ──
    data["cooling_water_flow"] = 15 + np.random.normal(0, 1, n_rows)
    data["cooling_water_temp_in"] = 25 + np.random.normal(0, 1, n_rows)
    data["cooling_water_temp_out"] = data["cooling_water_temp_in"] + 8 + np.random.normal(0, 0.5, n_rows)
    data["cooling_water_pressure"] = 0.3 + np.random.normal(0, 0.02, n_rows)
    data["vacuum_pressure"] = 100 + np.random.normal(0, 10, n_rows)
    data["ambient_pressure"] = 101.3 + np.random.normal(0, 0.5, n_rows)
    data["ambient_humidity"] = 60 + np.random.normal(0, 5, n_rows)

    # ── 状态维持模块 ──
    data["furnace_temp_1"] = base_temp + np.random.normal(0, 10, n_rows)
    data["furnace_temp_2"] = base_temp + np.random.normal(0, 8, n_rows)
    data["furnace_temp_3"] = base_temp + np.random.normal(0, 12, n_rows)
    data["furnace_pressure"] = base_pressure + np.random.normal(0, 0.03, n_rows)
    data["vibration_x"] = 2.0 + np.random.normal(0, 0.5, n_rows)
    data["vibration_y"] = 1.8 + np.random.normal(0, 0.4, n_rows)
    data["temp_stability_index"] = 90 + np.random.normal(0, 5, n_rows)
    data["degradation_index"] = 10 + np.cumsum(np.random.normal(0, 0.01, n_rows))

    # 注入异常模式（后 20% 数据）
    anomaly_start = int(n_rows * 0.8)
    t = np.arange(n_rows - anomaly_start)
    data.loc[anomaly_start:, "furnace_temp_1"] += t * 0.5  # 温度漂升
    data.loc[anomaly_start:, "vibration_x"] += t * 0.02  # 振动增加
    data.loc[anomaly_start:, "cooling_water_flow"] -= t * 0.01  # 流量衰减
    data.loc[anomaly_start:, "degradation_index"] += t * 0.1  # 退化加速

    # 随机联锁触发
    interlock_indices = np.random.choice(range(anomaly_start, n_rows), size=5, replace=False)
    data.loc[interlock_indices, "interlock_status"] = 1

    # 保存
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    data.to_excel(out, index=False, engine="openpyxl")
    logger.info(f"Demo 数据已保存: {out}")

    return data


def main() -> None:
    """主流程。"""
    cfg = load_app_config()
    demo_dir = ensure_dir(cfg["data"]["demo_dir"])
    raw_dir = ensure_dir(cfg["data"]["raw_excel_dir"])
    processed_dir = ensure_dir(cfg["data"]["processed_dir"])

    # 检查是否有真实数据
    real_files = list(raw_dir.glob("*.xlsx"))
    if not real_files:
        logger.info("raw_excel 目录无数据，自动生成 demo 数据")
        demo_path = demo_dir / "demo_equipment_data.xlsx"
        generate_demo_data(demo_path)

        # 复制到 raw_excel
        import shutil
        dest = raw_dir / "demo_equipment_data.xlsx"
        shutil.copy2(demo_path, dest)
        logger.info(f"已复制到: {dest}")

    # 导入
    service = DataImportService()
    df = service.import_and_save(raw_dir, "imported_data.csv")

    if df.empty:
        logger.error("导入失败")
        return

    # 质量报告
    reporter = DataQualityReporter()
    report_text = reporter.generate_text(df)
    print(report_text)

    # 保存质量报告
    report_path = processed_dir / "data_quality_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    logger.info(f"质量报告已保存: {report_path}")


if __name__ == "__main__":
    main()
