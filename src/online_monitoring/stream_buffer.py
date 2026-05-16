"""实时数据流缓冲区。

管理从 DCS 接收的实时数据流，支持滑动窗口读取。
"""
from __future__ import annotations

from collections import deque
from typing import Any

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)


class StreamBuffer:
    """实时数据流缓冲区。"""

    def __init__(self, max_size: int = 500) -> None:
        self.max_size = max_size
        self._buffer: deque[pd.Series] = deque(maxlen=max_size)
        self._total_received: int = 0

    def push(self, row: pd.Series | dict) -> None:
        """推入一条数据。"""
        if isinstance(row, dict):
            row = pd.Series(row)
        self._buffer.append(row)
        self._total_received += 1

    def push_batch(self, df: pd.DataFrame) -> None:
        """推入一批数据。"""
        for _, row in df.iterrows():
            self.push(row)

    def get_window(self, size: int | None = None) -> pd.DataFrame:
        """获取最近 N 条数据作为 DataFrame。"""
        if not self._buffer:
            return pd.DataFrame()

        size = size or len(self._buffer)
        size = min(size, len(self._buffer))

        items = list(self._buffer)[-size:]
        return pd.DataFrame(items)

    def get_latest(self, n: int = 1) -> pd.DataFrame:
        """获取最新 N 条数据。"""
        return self.get_window(n)

    @property
    def current_size(self) -> int:
        return len(self._buffer)

    @property
    def total_received(self) -> int:
        return self._total_received

    @property
    def is_full(self) -> bool:
        return len(self._buffer) >= self.max_size

    def clear(self) -> None:
        """清空缓冲区。"""
        self._buffer.clear()
        self._total_received = 0

    def to_dataframe(self) -> pd.DataFrame:
        """转为 DataFrame。"""
        if not self._buffer:
            return pd.DataFrame()
        return pd.DataFrame(list(self._buffer))
