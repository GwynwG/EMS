"""DCS 连接器基类。

定义实时数据源的抽象接口。后续替换真实 DCS 只需继承此基类。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class DCSConnectorBase(ABC):
    """DCS 实时数据连接器基类。"""

    @abstractmethod
    def connect(self) -> bool:
        """建立连接，返回是否成功。"""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接。"""
        ...

    @abstractmethod
    def read_latest(self, tags: list[str], n_rows: int = 1) -> pd.DataFrame:
        """读取最新 N 条数据。"""
        ...

    @abstractmethod
    def read_range(
        self,
        tags: list[str],
        start_time: pd.Timestamp,
        end_time: pd.Timestamp,
    ) -> pd.DataFrame:
        """读取时间范围内的数据。"""
        ...

    @abstractmethod
    def is_connected(self) -> bool:
        """返回连接状态。"""
        ...

    def get_available_tags(self) -> list[str]:
        """返回可用点位列表（可选实现）。"""
        return []
