"""异常根因分析器。

从 PCA 贡献度提取 Top-K 异常变量，映射回模块，输出结构化根因报告。
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

# 模块 ID → 中文名
_MODULE_CN = {
    "execution_control": "执行控制",
    "energy_input": "能量输入",
    "environmental_constraint": "环境约束",
    "state_maintenance": "状态维持",
}


class RootCauseAnalyzer:
    """异常根因分析器。"""

    # 变量名 → 中文名（常见变量）
    _VAR_CN = {
        "furnace_temp_1": "炉温1区", "furnace_temp_2": "炉温2区",
        "furnace_temp_3": "炉温3区", "furnace_pressure": "炉内压力",
        "vibration_x": "X向振动", "vibration_y": "Y向振动",
        "supply_voltage": "供电电压", "supply_current": "供电电流",
        "active_power": "有功功率", "cooling_water_flow": "冷却水流量",
        "cooling_water_temp_in": "冷却水进水温度", "cooling_water_temp_out": "冷却水出水温度",
        "vacuum_pressure": "真空度", "setpoint_temperature": "温度设定值",
        "valve_position_main": "主阀阀位", "interlock_status": "联锁状态",
        "power_factor": "功率因数", "energy_efficiency": "能量利用效率",
        "temp_stability_index": "温度稳定性指标", "degradation_index": "退化指标",
    }

    @staticmethod
    def _detect_module(col_name: str) -> str:
        """从列名推断所属模块。"""
        for prefix in ["execution_control__", "energy_input__",
                       "environmental_constraint__", "state_maintenance__"]:
            if col_name.startswith(prefix):
                return prefix.rstrip("__")
        return "unknown"

    @staticmethod
    def _extract_base_variable(col_name: str) -> str:
        """从列名提取基础变量名（去掉模块前缀和特征后缀）。"""
        name = col_name
        for prefix in ["execution_control__", "energy_input__",
                       "environmental_constraint__", "state_maintenance__"]:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break

        # 去掉常见特征后缀
        suffixes = [
            "_rolling_mean_10", "_rolling_std_10", "_rolling_mean_20", "_rolling_std_20",
            "_change_rate", "_pct_change", "_acceleration", "_slope",
            "_lag_1", "_lag_3", "_lag_5",
            "_jump_count", "_exceed_count",
            "_mean", "_std", "_max", "_min", "_range", "_median",
            "_cummean", "_cumstd", "_variance",
            "_raw", "_current", "_value",
        ]
        for suffix in sorted(suffixes, key=len, reverse=True):
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        return name

    def analyze_sample(
        self,
        contributions: np.ndarray,
        feature_names: list[str],
        current_values: pd.Series | None = None,
        top_k: int = 5,
    ) -> dict[str, Any]:
        """分析单个样本的异常根因。

        Args:
            contributions: PCA 重构残差（各变量的贡献，形状 [n_features]）
            feature_names: 特征名列表
            current_values: 当前变量值（可选，用于判断趋势方向）
            top_k: 返回前 K 个贡献最大的变量

        Returns:
            根因分析结果字典
        """
        abs_contrib = np.abs(contributions)
        top_idx = np.argsort(abs_contrib)[::-1][:top_k]

        root_causes = []
        module_contributions: dict[str, float] = {}

        for idx in top_idx:
            col = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
            contrib_value = float(contributions[idx])
            abs_value = float(abs_contrib[idx])
            module = self._detect_module(col)
            base_var = self._extract_base_variable(col)
            var_cn = self._VAR_CN.get(base_var, base_var)
            module_cn = _MODULE_CN.get(module, module)

            # 趋势方向
            trend = "—"
            if current_values is not None and col in current_values.index:
                val = current_values[col]
                if contrib_value > 0:
                    trend = "偏高" if val > 0 else "偏低"
                else:
                    trend = "偏低" if val > 0 else "偏高"

            root_causes.append({
                "rank": len(root_causes) + 1,
                "feature": col,
                "variable": var_cn,
                "module": module,
                "module_cn": module_cn,
                "contribution": round(contrib_value, 4),
                "abs_contribution": round(abs_value, 4),
                "trend": trend,
            })

            # 累积模块贡献
            module_contributions[module] = module_contributions.get(module, 0) + abs_value

        # 归一化模块贡献
        total_contrib = sum(module_contributions.values()) or 1.0
        module_contributions = {
            k: round(v / total_contrib, 3) for k, v in module_contributions.items()
        }

        # 主因模块
        main_module = max(module_contributions, key=module_contributions.get) if module_contributions else "unknown"

        return {
            "root_causes": root_causes,
            "module_contributions": module_contributions,
            "main_module": main_module,
            "main_module_cn": _MODULE_CN.get(main_module, main_module),
            "total_anomaly_degree": round(float(np.sum(abs_contrib)), 4),
        }

    def analyze_batch(
        self,
        contributions_matrix: np.ndarray,
        feature_names: list[str],
        top_k: int = 5,
    ) -> pd.DataFrame:
        """批量分析根因，返回每行的主因变量和模块。"""
        results = []
        for i in range(len(contributions_matrix)):
            analysis = self.analyze_sample(contributions_matrix[i], feature_names, top_k=top_k)
            top1 = analysis["root_causes"][0] if analysis["root_causes"] else {}
            results.append({
                "top_variable": top1.get("variable", ""),
                "top_feature": top1.get("feature", ""),
                "top_module": top1.get("module", ""),
                "top_module_cn": top1.get("module_cn", ""),
                "top_contribution": top1.get("abs_contribution", 0),
                "main_module": analysis["main_module"],
                "main_module_cn": analysis["main_module_cn"],
            })
        return pd.DataFrame(results)
