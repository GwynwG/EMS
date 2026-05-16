"""报告生成器。"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from src.utils.config_loader import ensure_dir
from src.utils.file_utils import save_json
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """监测报告生成器。"""

    def generate_summary_report(
        self,
        risk_result: dict[str, Any],
        data_quality: dict[str, Any] | None = None,
        model_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """生成综合摘要报告。"""
        report = {
            "report_time": datetime.now().isoformat(),
            "risk_assessment": {
                "risk_score": risk_result.get("risk_score", 0),
                "risk_level": risk_result.get("risk_level", "unknown"),
                "health_index": risk_result.get("health_index", 0),
                "main_abnormal_module": risk_result.get("main_abnormal_module", ""),
                "main_abnormal_coupling": risk_result.get("main_abnormal_coupling", ""),
                "module_scores": risk_result.get("module_scores", {}),
            },
        }

        if data_quality:
            report["data_quality"] = data_quality
        if model_info:
            report["model_info"] = model_info

        return report

    def save_report(
        self,
        report: dict[str, Any],
        output_path: str = "outputs/reports/monitoring_report.json",
    ) -> str:
        """保存报告为 JSON。"""
        path = save_json(report, output_path)
        logger.info(f"报告已保存: {path}")
        return str(path)

    def generate_text_report(self, report: dict[str, Any]) -> str:
        """生成文本格式报告。"""
        risk = report.get("risk_assessment", {})
        lines = [
            "=" * 60,
            "特种材料制备设备状态监测报告",
            "=" * 60,
            f"报告时间: {report.get('report_time', '')}",
            "",
            "--- 风险评估 ---",
            f"综合风险分数: {risk.get('risk_score', 0):.2f}",
            f"风险等级: {risk.get('risk_level', 'unknown')}",
            f"健康指数: {risk.get('health_index', 0):.1f}",
            f"主异常模块: {risk.get('main_abnormal_module', '')}",
            f"主异常耦合: {risk.get('main_abnormal_coupling', '')}",
            "",
            "--- 模块评分 ---",
        ]

        for module, score in risk.get("module_scores", {}).items():
            lines.append(f"  {module}: {score:.1f}")

        lines.append("=" * 60)
        return "\n".join(lines)
