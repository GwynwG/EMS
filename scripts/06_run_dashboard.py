"""脚本 06: 启动 Streamlit 仪表盘。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    app_path = project_root / "app" / "streamlit_app.py"

    print(f"启动 Streamlit 仪表盘: {app_path}")
    print("访问地址: http://localhost:8501")
    print("按 Ctrl+C 停止")

    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(app_path),
         "--server.port", "8501",
         "--server.headless", "true",
         "--theme.base", "dark"],
        cwd=str(project_root),
    )


if __name__ == "__main__":
    main()
