"""ECharts Streamlit 组件（bi-directional component）。

支持节点和边的点击回调，通过 Streamlit.setComponentValue 将点击事件传回 Python。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

# 组件构建目录
_BUILD_DIR = Path(__file__).resolve().parent / "echarts_component_build"

# 声明 bi-directional 组件
_component_func = components.declare_component("echarts_graph", path=str(_BUILD_DIR))


def st_echarts_graph(
    option: dict[str, Any],
    height: int = 720,
    key: str | None = None,
) -> Any:
    """渲染可交互的 ECharts 图表。

    点击节点返回: {"action": "node_click", "nodeId": "..."}
    点击边返回:   {"action": "edge_click", "edgeId": "source__target", "source": "...", "target": "..."}
    """
    option_str = json.dumps(option, ensure_ascii=False)
    return _component_func(option=option_str, default=None, height=height + 20, key=key)
