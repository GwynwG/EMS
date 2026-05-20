"""深灰工业风主题 — 温和高级的配色体系。

色系：深灰底 / 冷蓝强调 / 红橙风险 / 青绿健康 / 琥珀警告
所有可视化组件应从此模块导入颜色和字体常量。
"""
from __future__ import annotations

# ════════════════════════════════════════════════════════════
# 背景色（深灰系，不再纯黑）
# ════════════════════════════════════════════════════════════
BG_MAIN = "#2B2F36"           # 页面主背景
BG_SIDEBAR = "#252830"        # 侧边栏背景
BG_CONTENT = "#30343B"        # 主内容区域背景
BG_CARD = "#353B45"           # 卡片背景
BG_CARD_SOFT = "#3A404A"      # 二级卡片
BG_GRAPH_WRAP = "#2B2F36"     # 拓扑图容器背景
BG_GRAPH_INNER = "#30343B"    # 拓扑图内部背景

# ════════════════════════════════════════════════════════════
# 边框色
# ════════════════════════════════════════════════════════════
BORDER_MAIN = "#49515D"        # 主边框
BORDER_SOFT = "#4B5563"        # 次级边框

# 节点默认边框
NODE_BORDER_DEFAULT = "#49515D"

# ════════════════════════════════════════════════════════════
# 文字色
# ════════════════════════════════════════════════════════════
TEXT_MAIN = "#F3F4F6"          # 主标题
TEXT_SECONDARY = "#D1D5DB"     # 正文
TEXT_MUTED = "#9CA3AF"         # 辅助文字
TEXT_DESC = "#9CA3AF"          # 节点说明文字

# 标签背景
BG_LABEL = "#2F343D"           # 关系标签底板背景

# ════════════════════════════════════════════════════════════
# 强调色
# ════════════════════════════════════════════════════════════
ACCENT_BLUE = "#60A5FA"        # 冷蓝（主强调色）
RISK_RED = "#F87171"           # 红橙（风险色）
HEALTH_GREEN = "#34D399"       # 青绿（健康色）
WARN_AMBER = "#FBBF24"         # 琥珀（警告色）

# ════════════════════════════════════════════════════════════
# 兼容别名
# ════════════════════════════════════════════════════════════
LINE_BLUE = ACCENT_BLUE
LINE_ORANGE = ACCENT_BLUE
MODEL_PURPLE = TEXT_MUTED
RESIDUAL_GRAY = TEXT_MUTED

# ════════════════════════════════════════════════════════════
# 状态等级映射（蓝/琥珀/琥珀/红橙）
# ════════════════════════════════════════════════════════════
STATUS_COLORS: dict[str, str] = {
    "normal": ACCENT_BLUE,
    "attention": WARN_AMBER,
    "warning": WARN_AMBER,
    "severe": RISK_RED,
}

STATUS_BG: dict[str, str] = {
    "normal": "rgba(96,165,250,0.08)",
    "attention": "rgba(251,191,36,0.08)",
    "warning": "rgba(251,191,36,0.08)",
    "severe": "rgba(248,113,113,0.08)",
}

# ════════════════════════════════════════════════════════════
# 拓扑图节点 — 统一深灰底
# ════════════════════════════════════════════════════════════
NODE_FILL = "#353B45"
NODE_STROKE = "#49515D"
NODE_STROKE_WIDTH = 1.5
NODE_RADIUS = 12

NODE_GROUP_COLORS: dict[str, dict[str, str]] = {
    "core":      {"fill": NODE_FILL, "stroke": NODE_STROKE},
    "diagnosis": {"fill": NODE_FILL, "stroke": NODE_STROKE},
    "residual":  {"fill": NODE_FILL, "stroke": NODE_STROKE},
    "model":     {"fill": NODE_FILL, "stroke": NODE_STROKE},
}

# ════════════════════════════════════════════════════════════
# 拓扑图边颜色
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
BG_SUMMARY_BLOCK = "#353B45"
BORDER_SUMMARY = "#49515D"
TABLE_HEADER_BG = "#353B45"
TABLE_ROW_ALT = "#2F343D"
HIGHLIGHT_ROW_BG = "rgba(96,165,250,0.08)"
