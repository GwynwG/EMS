"""日志工具模块。"""
from __future__ import annotations

import logging
import sys

from src.utils.app_paths import ensure_directory


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """获取带控制台和文件输出的 logger。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 文件
    log_dir = ensure_directory("outputs/logs")
    fh = logging.FileHandler(log_dir / "system.log", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
