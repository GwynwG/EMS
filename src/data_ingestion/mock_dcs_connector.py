"""Mock DCS 连接器。

使用预处理好的历史数据模拟实时数据流，用于在线监测原型验证。
替换真实 DCS 时只需实现 DCSConnectorBase 并注入即可。
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from src.data_ingestion.dcs_connector_base import DCSConnectorBase
from src.utils.config_loader import _resolve_path
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MockDCSConnector(DCSConnectorBase):
    """基于 CSV 文件的 Mock DCS 连接器。"""

    def __init__(self, data_source: str | Path, noise_std: float = 0.01) -> None:
        self._data_source = _resolve_path(data_source)
        self._noise_std = noise_std
        self._data: pd.DataFrame | None = None
        self._cursor: int = 0
        self._connected: bool = False

    def connect(self) -> bool:
        """加载数据文件并标记连接成功。"""
        if not self._data_source.exists():
            logger.error(f"Mock 数据源不存在: {self._data_source}")
            return False

        self._data = pd.read_csv(self._data_source, encoding="utf-8-sig")
        # 尝试解析时间索引
        if "timestamp" in self._data.columns:
            self._data["timestamp"] = pd.to_datetime(self._data["timestamp"])
        self._cursor = 0
        self._connected = True
        logger.info(f"Mock DCS 已连接: {len(self._data)} 行数据")
        return True

    def disconnect(self) -> None:
        self._connected = False
        self._data = None
        self._cursor = 0
        logger.info("Mock DCS 已断开")

    def is_connected(self) -> bool:
        return self._connected and self._data is not None

    def read_latest(self, tags: list[str], n_rows: int = 1) -> pd.DataFrame:
        """读取下一批数据（模拟实时推进）。"""
        if not self.is_connected() or self._data is None:
            return pd.DataFrame()

        end = min(self._cursor + n_rows, len(self._data))
        if self._cursor >= len(self._data):
            # 循环回起点
            self._cursor = 0
            end = min(n_rows, len(self._data))

        chunk = self._data.iloc[self._cursor:end].copy()

        # 添加微量噪声模拟实时波动
        if self._noise_std > 0:
            numeric_cols = chunk.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                noise = np.random.normal(0, self._noise_std * chunk[col].std(), len(chunk))
                chunk[col] = chunk[col] + noise

        self._cursor = end
        return chunk

    def read_range(
        self,
        tags: list[str],
        start_time: pd.Timestamp,
        end_time: pd.Timestamp,
    ) -> pd.DataFrame:
        """读取时间范围数据。"""
        if not self.is_connected() or self._data is None:
            return pd.DataFrame()

        if "timestamp" in self._data.columns:
            mask = (self._data["timestamp"] >= start_time) & (self._data["timestamp"] <= end_time)
            return self._data.loc[mask].copy()
        return pd.DataFrame()

    def get_available_tags(self) -> list[str]:
        if self._data is not None:
            return [c for c in self._data.columns if c != "timestamp"]
        return []

    def reset(self) -> None:
        """重置游标到起点。"""
        self._cursor = 0

    @property
    def progress(self) -> float:
        """返回数据读取进度百分比。"""
        if self._data is None or len(self._data) == 0:
            return 0.0
        return self._cursor / len(self._data) * 100.0
