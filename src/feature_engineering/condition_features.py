"""条件特征提取。

提取与运行工况相关的派生特征，如冷却水温差、温度均匀性等。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class ConditionFeatureExtractor:
    """条件特征提取器。"""

    def extract(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取条件/工况派生特征。"""
        feat = pd.DataFrame(index=df.index)

        # 冷却水温差
        if "cooling_water_temp_in" in df.columns and "cooling_water_temp_out" in df.columns:
            feat["cooling_temp_diff"] = (
                df["cooling_water_temp_out"] - df["cooling_water_temp_in"]
            )
            feat["cooling_heat_removal"] = feat["cooling_temp_diff"] * df.get(
                "cooling_water_flow", 1.0
            )

        # 炉温均匀性
        temp_cols = [c for c in df.columns if c.startswith("furnace_temp_")]
        if len(temp_cols) >= 2:
            temp_matrix = df[temp_cols]
            feat["temp_uniformity"] = temp_matrix.std(axis=1)
            feat["temp_max_diff"] = temp_matrix.max(axis=1) - temp_matrix.min(axis=1)
            feat["temp_mean"] = temp_matrix.mean(axis=1)

        # 振动综合指标
        if "vibration_x" in df.columns and "vibration_y" in df.columns:
            feat["vibration_magnitude"] = np.sqrt(
                df["vibration_x"] ** 2 + df["vibration_y"] ** 2
            )

        # 功率效率比
        if "active_power" in df.columns and "supply_voltage" in df.columns:
            feat["current_estimate"] = df["active_power"] / df["supply_voltage"].replace(0, np.nan)

        # 设定值偏差
        if "setpoint_temperature" in df.columns and "furnace_temp_1" in df.columns:
            feat["temp_deviation"] = df["furnace_temp_1"] - df["setpoint_temperature"]
            feat["temp_deviation_pct"] = (
                feat["temp_deviation"] / df["setpoint_temperature"].replace(0, np.nan) * 100
            )

        # 压力偏差
        if "setpoint_pressure" in df.columns and "furnace_pressure" in df.columns:
            feat["pressure_deviation"] = df["furnace_pressure"] - df["setpoint_pressure"]

        return feat
