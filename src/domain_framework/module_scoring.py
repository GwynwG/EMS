"""模块级状态评分。

基于各模块自身特征和模型输出计算模块级状态评分（0-100，越高越健康）。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from src.domain_framework.module_schema import ModuleType, get_module_meta
from src.utils.config_loader import load_model_config


class ModuleScorer:
    """四模块状态评分器。"""

    def __init__(self) -> None:
        cfg = load_model_config()
        self.risk_cfg = cfg.get("risk_fusion", {})
        self.module_weights = self.risk_cfg.get("module_weights", {
            "execution_control": 0.15,
            "energy_input": 0.20,
            "environmental_constraint": 0.20,
            "state_maintenance": 0.45,
        })

    @staticmethod
    def compute_module_score(
        feature_values: pd.Series | dict[str, float],
        reference_stats: dict[str, dict[str, float]] | None = None,
    ) -> float:
        """基于特征值计算单个模块的健康评分。

        使用特征偏离参考统计量的程度来评分。
        偏离越大，分数越低。
        """
        if isinstance(feature_values, dict):
            feature_values = pd.Series(feature_values)

        if feature_values.empty:
            return 100.0

        # 如果没有参考统计量，使用自适应方法
        if reference_stats is None:
            values = feature_values.dropna().values
            if len(values) == 0:
                return 100.0
            # 使用变异系数的反向映射
            mean_val = np.mean(np.abs(values))
            std_val = np.std(values)
            if mean_val < 1e-10:
                return 100.0
            cv = std_val / mean_val
            # CV 映射到 0-100 分，CV 越大分越低
            score = max(0.0, 100.0 - cv * 50.0)
            return float(np.clip(score, 0.0, 100.0))

        # 基于参考统计量的评分
        deviations = []
        for col, val in feature_values.items():
            if col in reference_stats and not np.isnan(val):
                ref = reference_stats[col]
                mean = ref.get("mean", 0)
                std = ref.get("std", 1)
                if std > 1e-10:
                    z = abs(val - mean) / std
                    deviations.append(z)

        if not deviations:
            return 100.0

        # 平均偏离映射到分数
        avg_dev = np.mean(deviations)
        score = max(0.0, 100.0 - avg_dev * 15.0)
        return float(np.clip(score, 0.0, 100.0))

    def compute_all_module_scores(
        self,
        module_features: dict[str, pd.Series | dict[str, float]],
        reference_stats: dict[str, dict[str, dict[str, float]]] | None = None,
    ) -> dict[str, float]:
        """计算所有模块的评分。"""
        scores = {}
        for mod in ModuleType:
            key = mod.value
            feat = module_features.get(key)
            if feat is not None:
                ref = reference_stats.get(key) if reference_stats else None
                scores[key] = self.compute_module_score(feat, ref)
            else:
                scores[key] = 100.0
        return scores

    def compute_global_risk_score(
        self,
        module_scores: dict[str, float],
        anomaly_score: float = 0.0,
        health_index: float = 100.0,
    ) -> float:
        """综合模块评分和全局异常分数计算风险分数（0-100，越高越危险）。"""
        # 模块加权健康度
        weighted_health = 0.0
        total_weight = 0.0
        for mod, weight in self.module_weights.items():
            s = module_scores.get(mod, 100.0)
            weighted_health += s * weight
            total_weight += weight

        if total_weight > 0:
            weighted_health /= total_weight

        # 健康度转风险度
        module_risk = 100.0 - weighted_health

        # 融合全局异常分数
        # anomaly_score 已经是异常度（越高越异常）
        risk = 0.5 * module_risk + 0.3 * anomaly_score + 0.2 * (100.0 - health_index)
        return float(np.clip(risk, 0.0, 100.0))

    @staticmethod
    def determine_risk_level(risk_score: float) -> str:
        """根据风险分数确定风险等级。"""
        cfg = load_model_config()
        thresholds = cfg.get("risk_fusion", {}).get("risk_thresholds", {
            "normal": 30, "attention": 50, "warning": 70, "severe": 85,
        })
        if risk_score >= thresholds.get("severe", 85):
            return "severe"
        elif risk_score >= thresholds.get("warning", 70):
            return "warning"
        elif risk_score >= thresholds.get("attention", 50):
            return "attention"
        return "normal"

    def find_main_abnormal_module(self, module_scores: dict[str, float]) -> str:
        """找出主要异常模块（评分最低的模块）。"""
        if not module_scores:
            return "unknown"
        return min(module_scores, key=module_scores.get)  # type: ignore

    @staticmethod
    def find_main_abnormal_coupling(
        module_scores: dict[str, float],
        coupling_residuals: dict[str, float] | None = None,
    ) -> str:
        """找出主要异常耦合关系。"""
        # 找出评分最低的两个模块
        sorted_modules = sorted(module_scores.items(), key=lambda x: x[1])
        if len(sorted_modules) >= 2:
            m1, m2 = sorted_modules[0][0], sorted_modules[1][0]
            return f"{m1} ↔ {m2}"
        return "无"

    # ── 驾驶舱展示用的计算方法（基于 demo/mock 数据）──────────────

    @staticmethod
    def compute_edge_contributions(
        module_scores: dict[str, float],
        coupling_graph: Any,
    ) -> list[dict]:
        """为每条耦合边生成展示用的贡献数据。

        基于源/目标模块评分反向推导：评分越低 → 耦合强度/残差/贡献越高。
        """
        from src.visualization.dashboard_components import MODULE_SHORT_CHINESE

        edges_data = []
        for edge in coupling_graph.edges:
            src_score = module_scores.get(edge.source, 80.0)
            tgt_score = module_scores.get(edge.target, 80.0)
            avg_score = (src_score + tgt_score) / 2.0

            # 耦合强度：与模块健康分反相关
            coupling_strength = round(max(0.1, min(1.0, (100 - avg_score) / 100 * 1.2 + 0.3)), 2)
            # 残差水平：与模块健康分反相关
            residual_level = round(max(0.05, min(1.0, (100 - avg_score) / 100 * 0.8 + 0.1)), 2)
            # 风险贡献
            risk_contribution = round(max(0.0, min(1.0, (100 - avg_score) / 100)), 2)

            # 状态判定
            if risk_contribution > 0.6:
                status_text = "预警"
            elif risk_contribution > 0.4:
                status_text = "关注"
            else:
                status_text = "正常"

            # 模型名称映射
            model_map = {
                "main": "PCA/PLS 监测模型",
                "feedback": "状态反馈规则",
                "auxiliary": "IF/XGBoost 异常检测",
            }

            src_cn = MODULE_SHORT_CHINESE.get(edge.source, edge.source)
            tgt_cn = MODULE_SHORT_CHINESE.get(edge.target, edge.target)

            edges_data.append({
                "id": f"{edge.source}__{edge.target}",
                "relation_name": f"{src_cn} → {tgt_cn}",
                "relation_type": edge.edge_type,
                "coupling_strength": coupling_strength,
                "residual_level": residual_level,
                "risk_contribution": risk_contribution,
                "model_name": model_map.get(edge.edge_type, "综合模型"),
                "current_status": status_text,
                "main_contributing_variable": edge.main_contributing_variable or "",
            })
        return edges_data

    @staticmethod
    def compute_variable_contributions(
        module_scores: dict[str, float],
        variable_dict_path: str = "configs/variable_dictionary.yaml",
    ) -> list[dict]:
        """为所有变量生成展示用的贡献数据。

        低评分模块的变量获得更高的 contribution_degree。
        """
        path = Path(variable_dict_path)
        if not path.exists():
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        variables = data.get("variables", [])
        result = []

        # 按模块评分排序，低分模块的变量排在前面
        sorted_modules = sorted(module_scores.items(), key=lambda x: x[1])

        for var in variables:
            if not var.get("enabled", True):
                continue
            module = var.get("module", "")
            score = module_scores.get(module, 80.0)

            # 贡献度：与模块健康分反相关，加随机偏移
            base = (100 - score) / 100
            name_hash = sum(ord(c) for c in var.get("standard_name", "")) % 20 / 100
            contribution = round(min(1.0, max(0.05, base * 0.8 + name_hash * 0.3)), 2)

            # 状态判定
            if contribution > 0.5:
                status = "预警"
            elif contribution > 0.3:
                status = "关注"
            else:
                status = "正常"

            # 模拟当前值
            unit = var.get("unit", "")
            name_lower = var.get("standard_name", "")
            if "temp" in name_lower:
                current_value = round(80 + score * 2 + name_hash * 10, 1)
            elif "pressure" in name_lower:
                current_value = round(2 + score * 0.05, 2)
            elif "flow" in name_lower:
                current_value = round(10 + score * 0.3, 1)
            elif "vibration" in name_lower:
                current_value = round(1 + (100 - score) * 0.1, 2)
            elif "power" in name_lower or "voltage" in name_lower or "current" in name_lower:
                current_value = round(100 + score * 2 + name_hash * 20, 1)
            else:
                current_value = round(score + name_hash * 10, 2)

            result.append({
                "variable": var.get("standard_name", ""),
                "chinese_name": var.get("chinese_name", ""),
                "module": module,
                "current_value": current_value,
                "unit": unit,
                "contribution_degree": contribution,
                "status": status,
            })

        # 按贡献度降序排列
        result.sort(key=lambda x: x["contribution_degree"], reverse=True)
        return result

    @staticmethod
    def compute_system_status_summary(
        status: dict,
        df: pd.DataFrame,
    ) -> dict:
        """生成系统状态摘要数据（4 个区块）。"""
        # 数据质量指标
        if not df.empty:
            missing_rate = round(df.isna().sum().sum() / (df.shape[0] * df.shape[1]) * 100, 2) if df.size > 0 else 0
            valid_rate = round(100 - missing_rate, 2)
        else:
            missing_rate = 0
            valid_rate = 0

        # 模块评分排序
        module_scores = status.get("module_scores", {})
        sorted_modules = sorted(module_scores.items(), key=lambda x: x[1])

        # 主要贡献变量（取前 3 个低分模块的代表变量）
        focus_vars = []
        from src.visualization.dashboard_components import MODULE_SHORT_CHINESE
        for mod_id, _ in sorted_modules[:2]:
            focus_vars.append(MODULE_SHORT_CHINESE.get(mod_id, mod_id))

        return {
            "data_link": {
                "excel_imported": True,
                "dcs_status": "Mock 模拟运行",
                "quality_metrics": {
                    "missing_rate": f"{missing_rate}%",
                    "abnormal_jump_rate": "0.3%",
                    "frozen_value_ratio": "0.1%",
                    "valid_sample_rate": f"{valid_rate}%",
                    "data_source": "Excel 历史数据 (Mock DCS)",
                },
            },
            "model_status": {
                "pca": "已加载",
                "pls": "预留接口",
                "if_model": "已加载",
                "health_index": "已启用",
                "intelligent": "待训练",
                "version": "v1.0-demo",
            },
            "risk_sources": {
                "statistical_residual": {
                    "label": "统计残差异常",
                    "value": f"{status.get('pca_anomaly_score', 0):.2f}",
                    "active": status.get("pca_anomaly_score", 0) > 1.0,
                },
                "module_score": {
                    "label": "模块评分异常",
                    "value": f"{sorted_modules[0][1]:.1f}" if sorted_modules else "N/A",
                    "active": sorted_modules[0][1] < 60 if sorted_modules else False,
                },
                "complex_coupling": {
                    "label": "复杂耦合残差",
                    "value": "0.35",
                    "active": False,
                },
                "event_rules": {
                    "label": "事件规则触发",
                    "value": "0",
                    "active": False,
                },
            },
            "recommended_focus": {
                "module": MODULE_SHORT_CHINESE.get(sorted_modules[0][0], "") if sorted_modules else "",
                "variable": focus_vars[0] if focus_vars else "",
                "coupling": f"{focus_vars[0]} → {focus_vars[1]}" if len(focus_vars) >= 2 else "",
            },
        }
