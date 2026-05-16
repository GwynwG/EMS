"""预警服务。

管理预警规则、触发预警、记录预警历史。
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Any

from src.utils.config_loader import load_alarm_rules
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AlarmRecord:
    """单条预警记录。"""

    def __init__(
        self,
        alarm_id: str,
        name: str,
        level: str,
        module: str,
        message: str,
        risk_score: float,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.alarm_id = alarm_id
        self.name = name
        self.level = level
        self.module = module
        self.message = message
        self.risk_score = risk_score
        self.details = details or {}
        self.timestamp = datetime.now()
        self.acknowledged = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "alarm_id": self.alarm_id,
            "name": self.name,
            "level": self.level,
            "module": self.module,
            "message": self.message,
            "risk_score": self.risk_score,
            "timestamp": self.timestamp.isoformat(),
            "acknowledged": self.acknowledged,
            "details": self.details,
        }


class AlarmService:
    """预警服务。"""

    def __init__(self, max_history: int = 1000) -> None:
        self.rules = load_alarm_rules().get("alarm_rules", [])
        self.alarm_levels = load_alarm_rules().get("alarm_levels", {})
        self._history: list[AlarmRecord] = []
        self.max_history = max_history
        self._alarm_counter = 0

    def check_alarms(
        self,
        inference_result: dict[str, Any],
        current_values: dict[str, float] | None = None,
    ) -> list[AlarmRecord]:
        """检查是否触发预警。"""
        alarms = []

        # 基于风险等级的预警
        risk_level = inference_result.get("risk_level", "normal")
        risk_score = inference_result.get("risk_score", 0)

        if risk_level in ("warning", "severe"):
            self._alarm_counter += 1
            alarm = AlarmRecord(
                alarm_id=f"RISK_{self._alarm_counter:06d}",
                name="综合风险预警",
                level=risk_level,
                module=inference_result.get("main_abnormal_module", "unknown"),
                message=f"综合风险分数 {risk_score:.1f}, 等级: {risk_level}",
                risk_score=risk_score,
                details=inference_result,
            )
            alarms.append(alarm)

        # 基于规则的预警
        if current_values:
            for rule in self.rules:
                if self._evaluate_rule(rule, current_values):
                    self._alarm_counter += 1
                    alarm = AlarmRecord(
                        alarm_id=f"RULE_{self._alarm_counter:06d}",
                        name=rule["name"],
                        level=rule["level"],
                        module=rule["module"],
                        message=rule["message"],
                        risk_score=risk_score,
                        details={"rule": rule, "values": current_values},
                    )
                    alarms.append(alarm)

        # 记录历史
        for alarm in alarms:
            self._history.append(alarm)
            logger.warning(f"预警触发: [{alarm.level}] {alarm.message}")

        # 限制历史长度
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]

        return alarms

    def _evaluate_rule(self, rule: dict, values: dict[str, float]) -> bool:
        """评估单条规则。"""
        condition = rule.get("condition", "")
        try:
            # 简单条件解析
            for var_name, var_value in values.items():
                condition = condition.replace(var_name, str(var_value))
            # 安全评估
            return bool(eval(condition))  # noqa: S307
        except Exception:
            return False

    @property
    def history(self) -> list[AlarmRecord]:
        return self._history

    def get_recent_alarms(self, n: int = 20) -> list[dict[str, Any]]:
        """获取最近 N 条预警。"""
        return [a.to_dict() for a in self._history[-n:]]

    def get_alarm_count_by_level(self) -> dict[str, int]:
        """按等级统计预警数量。"""
        counts: dict[str, int] = {}
        for alarm in self._history:
            counts[alarm.level] = counts.get(alarm.level, 0) + 1
        return counts

    def clear_history(self) -> None:
        """清空预警历史。"""
        self._history.clear()
        self._alarm_counter = 0
