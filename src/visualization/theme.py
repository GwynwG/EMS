"""深色极简工业主题 — 严格控制颜色数量。

仅 4 类颜色：黑灰系 / 蓝强调 / 红风险 / 灰文字
所有可视化组件应从此模块导入颜色和字体常量。
"""
from __future__ import annotations

# ════════════════════════════════════════════════════════════
# 背景色（黑灰系）
# ════════════════════════════════════════════════════════════
BG_MAIN = "#252A33"           # 页面背景（深灰底，不纯黑）
BG_SIDEBAR = "#252526"        # 侧边栏背景
BG_CONTENT = "#1F232A"        # 主内容区域背景
BG_CARD = "#2A2D33"           # 卡片背景（统一）
BG_CARD_SOFT = "#2A2D33"      # 与卡片背景统一
BG_GRAPH_WRAP = "#202225"     # 拓扑图容器背景
BG_GRAPH_INNER = "#1B1D21"    # 拓扑图内部背景

# ════════════════════════════════════════════════════════════
# 边框色
# ════════════════════════════════════════════════════════════
BORDER_MAIN = "#3A3F46"        # 主边框
BORDER_SOFT = "#3A3F46"        # 次级边框（统一）

# 节点默认边框
NODE_BORDER_DEFAULT = "#4B5563"

# ════════════════════════════════════════════════════════════
# 文字色（灰系）
# ════════════════════════════════════════════════════════════
TEXT_MAIN = "#F1F5F9"          # 主文字
TEXT_SECONDARY = "#A7B0BD"     # 次级文字
TEXT_MUTED = "#6B7280"         # 弱文字
TEXT_DESC = "#8B95A3"          # 节点说明文字

# 标签背景
BG_LABEL = "#252830"           # 关系标签底板背景

# ════════════════════════════════════════════════════════════
# 主强调色（蓝）— 仅此一种强调色
# ════════════════════════════════════════════════════════════
ACCENT_BLUE = "#4FC1FF"

# ════════════════════════════════════════════════════════════
# 风险色（红）— 仅用于高风险
# ════════════════════════════════════════════════════════════
RISK_RED = "#FF6B6B"

# ════════════════════════════════════════════════════════════
# 兼容别名（旧代码引用）
# ════════════════════════════════════════════════════════════
LINE_BLUE = ACCENT_BLUE
LINE_ORANGE = ACCENT_BLUE      # 反馈线也用蓝色，不再用橙色
MODEL_PURPLE = TEXT_MUTED       # 智能模型不再用紫色
RESIDUAL_GRAY = TEXT_MUTED      # 残差灰色

# ════════════════════════════════════════════════════════════
# 状态等级映射（极简：蓝/灰/红）
# ════════════════════════════════════════════════════════════
STATUS_COLORS: dict[str, str] = {
    "normal": ACCENT_BLUE,      # 正常 — 蓝色
    "attention": TEXT_SECONDARY, # 关注 — 灰色
    "warning": TEXT_SECONDARY,   # 预警 — 灰色
    "severe": RISK_RED,          # 严重 — 红色
}

STATUS_BG: dict[str, str] = {
    "normal": "rgba(79,193,255,0.08)",
    "attention": "rgba(167,176,189,0.08)",
    "warning": "rgba(167,176,189,0.08)",
    "severe": "rgba(255,107,107,0.08)",
}

# ════════════════════════════════════════════════════════════
# 拓扑图节点 — 统一样式，不按模块分色
# ════════════════════════════════════════════════════════════
NODE_FILL = "#2A2D33"
NODE_STROKE = "#4B5563"
NODE_STROKE_WIDTH = 1.5
NODE_RADIUS = 12

NODE_GROUP_COLORS: dict[str, dict[str, str]] = {
    "core":      {"fill": NODE_FILL, "stroke": NODE_STROKE},
    "diagnosis": {"fill": NODE_FILL, "stroke": NODE_STROKE},
    "residual":  {"fill": NODE_FILL, "stroke": NODE_STROKE},
    "model":     {"fill": NODE_FILL, "stroke": NODE_STROKE},
}

# ════════════════════════════════════════════════════════════
# 拓扑图边颜色 — 仅蓝+灰
# ════════════════════════════════════════════════════════════
EDGE_COLORS: dict[str, dict[str, float | str]] = {
    "main":      {"stroke": ACCENT_BLUE,  "width": 2.2},
    "feedback":  {"stroke": ACCENT_BLUE,  "width": 2.2},
    "auxiliary": {"stroke": TEXT_MUTED,    "width": 1.5},
}

# 选中高亮色
SELECTED_COLOR = ACCENT_BLUE
SELECTED_STROKE_WIDTH = 3.0

# ════════════════════════════════════════════════════════════
# 字体
# ════════════════════════════════════════════════════════════
FONT_FAMILY = '"Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif'
FONT_MONO = '"Cascadia Code", "Fira Code", "Consolas", monospace'

# ════════════════════════════════════════════════════════════
# 驾驶舱新增常量
# ════════════════════════════════════════════════════════════
BG_SUMMARY_BLOCK = "#2A2D33"    # 系统状态摘要区块背景
BORDER_SUMMARY = "#3A3F46"      # 摘要区块边框
TABLE_HEADER_BG = "#2A2D33"     # 表格头背景
TABLE_ROW_ALT = "#252830"       # 表格交替行背景
HIGHLIGHT_ROW_BG = "rgba(79,193,255,0.08)"  # 选中行高亮背景
