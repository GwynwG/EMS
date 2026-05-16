"""脚本 05: 运行 Mock DCS 在线监测模拟。"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data_ingestion.mock_dcs_connector import MockDCSConnector
from src.online_monitoring.stream_buffer import StreamBuffer
from src.online_monitoring.online_feature_service import OnlineFeatureService
from src.online_monitoring.online_inference_service import OnlineInferenceService
from src.online_monitoring.alarm_service import AlarmService
from src.visualization.report_generator import ReportGenerator
from src.utils.config_loader import load_app_config, ensure_dir
from src.utils.logger import get_logger

logger = get_logger("05_online")


def main() -> None:
    cfg = load_app_config()
    processed_dir = ensure_dir(cfg["data"]["processed_dir"])
    output_dir = ensure_dir(cfg["output"]["reports_dir"])

    # 初始化组件
    connector = MockDCSConnector(
        data_source=cfg["dcs"]["mock_data_source"],
        noise_std=0.005,
    )
    buffer = StreamBuffer(max_size=cfg["dcs"]["buffer_size"])
    feature_service = OnlineFeatureService(window_size=60)
    inference_service = OnlineInferenceService()
    alarm_service = AlarmService()
    report_gen = ReportGenerator()

    # 加载模型
    inference_service.load_models(str(cfg["output"]["models_dir"]))

    # 连接
    if not connector.connect():
        logger.error("Mock DCS 连接失败")
        return

    logger.info("在线监测启动...")

    # 模拟在线监测
    n_iterations = 100
    batch_size = 5
    results_log = []

    for i in range(n_iterations):
        # 读取数据
        batch = connector.read_latest([], n_rows=batch_size)
        if batch.empty:
            break

        # 推入缓冲区
        buffer.push_batch(batch)

        # 特征提取
        if buffer.current_size >= 60:
            module_features, fused_features = feature_service.extract_features(buffer)

            if not fused_features.empty:
                # 推理
                result = inference_service.infer(fused_features, module_features)

                # 预警检查
                current_values = {}
                latest = buffer.get_latest(1)
                if not latest.empty:
                    for col in latest.columns:
                        try:
                            current_values[col] = float(latest[col].iloc[-1])
                        except (ValueError, TypeError):
                            pass

                alarms = alarm_service.check_alarms(result, current_values)

                # 记录
                results_log.append(result)

                if (i + 1) % 20 == 0:
                    logger.info(
                        f"[{i+1}/{n_iterations}] "
                        f"风险={result['risk_score']:.1f}, "
                        f"等级={result['risk_level']}, "
                        f"HI={result['health_index']:.1f}, "
                        f"主异常={result['main_abnormal_module']}"
                    )

    # 生成报告
    if results_log:
        last_result = results_log[-1]
        report = report_gen.generate_summary_report(last_result)
        report_path = report_gen.save_report(report, str(output_dir / "online_monitoring_report.json"))

        text_report = report_gen.generate_text_report(report)
        print("\n" + text_report)

    # 预警统计
    alarm_counts = alarm_service.get_alarm_count_by_level()
    logger.info(f"预警统计: {alarm_counts}")
    logger.info(f"最近预警: {len(alarm_service.get_recent_alarms())} 条")

    connector.disconnect()
    logger.info("在线监测结束")


if __name__ == "__main__":
    main()
