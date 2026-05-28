"""Windows launcher for the DataDiagnostics Streamlit application."""
from __future__ import annotations

import atexit
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Iterable

if getattr(sys, "frozen", False):
    _BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    _PROJECT_ROOT = _BUNDLE_ROOT
else:
    _DESKTOP_ROOT = Path(__file__).resolve().parent
    _BUNDLE_ROOT = _DESKTOP_ROOT
    _PROJECT_ROOT = _DESKTOP_ROOT.parent

_RUNTIME_ROOT = _BUNDLE_ROOT / "runtime"
if _RUNTIME_ROOT.exists():
    sys.path.insert(0, str(_RUNTIME_ROOT))
sys.path.insert(1, str(_PROJECT_ROOT))

from desktop_runtime.app_paths import get_install_dir, get_resource_path, initialize_user_data


DEFAULT_PORTS = (8501, 8502, 8503, 8504)
SERVER_FLAG = "--streamlit-server"


def is_port_available(port: int) -> bool:
    """Return True when localhost can bind the given port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def find_available_port(candidate_ports: Iterable[int] = DEFAULT_PORTS) -> int:
    """Pick the first available port from the candidate list."""
    for port in candidate_ports:
        if is_port_available(int(port)):
            return int(port)
    raise RuntimeError("No available Streamlit port found in 8501-8504.")


def find_streamlit_app() -> Path:
    """Locate app/streamlit_app.py in development or PyInstaller bundles."""
    app_path = get_resource_path("app/streamlit_app.py")
    if not app_path.exists():
        raise FileNotFoundError(f"Streamlit app not found: {app_path}")
    return app_path


def build_streamlit_args(app_path: str | Path, port: int) -> list[str]:
    """Build Streamlit CLI arguments shared by development and bundled runs."""
    return [
        "run",
        str(app_path),
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
        "--global.developmentMode",
        "false",
        "--client.toolbarMode",
        "minimal",
        "--logger.level",
        "error",
    ]


def _server_environment(port: int) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "STREAMLIT_SERVER_HEADLESS": "true",
            "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false",
            "STREAMLIT_GLOBAL_DEVELOPMENT_MODE": "false",
            "STREAMLIT_CLIENT_TOOLBAR_MODE": "minimal",
            "STREAMLIT_SERVER_PORT": str(port),
        }
    )
    return env


def _child_command(app_path: Path, port: int) -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable, SERVER_FLAG, str(app_path), str(port)]
    return [sys.executable, str(Path(__file__).resolve()), SERVER_FLAG, str(app_path), str(port)]


def wait_for_server(url: str, timeout_sec: float = 30.0) -> bool:
    """Wait until the local Streamlit server answers HTTP requests."""
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0):
                return True
        except (OSError, urllib.error.URLError):
            time.sleep(0.5)
    return False


def run_streamlit_server(app_path: str | Path, port: int) -> None:
    """Run Streamlit inside the child process."""
    initialize_user_data()
    from src.utils.logger import get_logger

    get_logger(__name__).info("DataDiagnostics Streamlit server starting on port %s", port)
    from streamlit.web.cli import main as streamlit_main

    sys.argv = ["streamlit"] + build_streamlit_args(app_path, port)
    streamlit_main()


def terminate_process_tree(proc: subprocess.Popen) -> None:
    """Best-effort child process cleanup when the launcher exits."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def launch() -> int:
    """Start Streamlit, open the browser, and keep the launcher attached."""
    initialize_user_data()
    app_path = find_streamlit_app()
    port = find_available_port()
    url = f"http://127.0.0.1:{port}"

    from src.utils.logger import get_logger

    get_logger(__name__).info("DataDiagnostics launcher starting: %s", url)

    print("Starting DataDiagnostics...")
    print(f"Application: {app_path}")
    print(f"Local URL: {url}")
    print("Close this window or press Ctrl+C to stop the application.")

    proc = subprocess.Popen(
        _child_command(app_path, port),
        cwd=str(get_install_dir()),
        env=_server_environment(port),
    )
    atexit.register(terminate_process_tree, proc)

    def _handle_signal(signum, _frame) -> None:
        terminate_process_tree(proc)
        raise SystemExit(128 + int(signum))

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle_signal)
        except (ValueError, OSError):
            pass

    if wait_for_server(url):
        webbrowser.open(url)
    else:
        print("Streamlit is still starting; opening the browser anyway.")
        webbrowser.open(url)

    try:
        return proc.wait()
    finally:
        terminate_process_tree(proc)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == SERVER_FLAG:
        if len(argv) != 3:
            raise SystemExit(f"Usage: {SERVER_FLAG} <app_path> <port>")
        run_streamlit_server(argv[1], int(argv[2]))
        return 0
    return launch()


if __name__ == "__main__":
    raise SystemExit(main())
