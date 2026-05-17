from __future__ import annotations

import socket
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import launcher


class LauncherTests(unittest.TestCase):
    def test_find_available_port_skips_ports_that_are_already_bound(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
            occupied.bind(("127.0.0.1", 0))
            occupied.listen(1)
            blocked_port = occupied.getsockname()[1]

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as free:
                free.bind(("127.0.0.1", 0))
                free_port = free.getsockname()[1]

            self.assertEqual(
                launcher.find_available_port([blocked_port, free_port]),
                free_port,
            )

    def test_build_streamlit_args_uses_headless_local_server_flags(self) -> None:
        args = launcher.build_streamlit_args("app/streamlit_app.py", 8502)

        self.assertEqual(args[0:2], ["run", "app/streamlit_app.py"])
        self.assertIn("--server.port", args)
        self.assertIn("8502", args)
        self.assertIn("--server.headless", args)
        self.assertIn("true", args)
        self.assertIn("--browser.gatherUsageStats", args)
        self.assertIn("false", args)
        self.assertIn("--global.developmentMode", args)
        self.assertIn("false", args)


if __name__ == "__main__":
    unittest.main()
