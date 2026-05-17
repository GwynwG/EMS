from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

DESKTOP_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = DESKTOP_ROOT.parent
sys.path.insert(0, str(DESKTOP_ROOT / "runtime"))
sys.path.insert(1, str(PROJECT_ROOT))


class AppPathsTests(unittest.TestCase):
    def _load_module(self, install_dir: Path, user_dir: Path):
        env = {
            "DATAMONITOR_INSTALL_DIR": str(install_dir),
            "DATAMONITOR_USER_DATA_DIR": str(user_dir),
        }
        patcher = patch.dict(os.environ, env, clear=False)
        patcher.start()
        self.addCleanup(patcher.stop)

        import desktop_runtime.app_paths as app_paths

        return importlib.reload(app_paths)

    def test_initialize_user_data_creates_runtime_tree_and_copies_configs(self) -> None:
        with tempfile.TemporaryDirectory() as install_tmp, tempfile.TemporaryDirectory() as user_tmp:
            install_dir = Path(install_tmp)
            user_dir = Path(user_tmp)
            (install_dir / "configs").mkdir()
            (install_dir / "configs" / "app_config.yaml").write_text("app:\n  name: demo\n", encoding="utf-8")

            app_paths = self._load_module(install_dir, user_dir)
            app_paths.initialize_user_data()

            expected_dirs = [
                "data",
                "data/raw_excel",
                "data/raw_dcs",
                "data/processed",
                "data/samples",
                "data/demo",
                "outputs",
                "outputs/models",
                "outputs/reports",
                "outputs/logs",
                "outputs/figures",
                "configs",
            ]
            for relative in expected_dirs:
                self.assertTrue((user_dir / relative).is_dir(), relative)
            self.assertEqual(
                (user_dir / "configs" / "app_config.yaml").read_text(encoding="utf-8"),
                "app:\n  name: demo\n",
            )

    def test_initialize_user_data_does_not_overwrite_existing_user_configs(self) -> None:
        with tempfile.TemporaryDirectory() as install_tmp, tempfile.TemporaryDirectory() as user_tmp:
            install_dir = Path(install_tmp)
            user_dir = Path(user_tmp)
            (install_dir / "configs").mkdir()
            (install_dir / "configs" / "app_config.yaml").write_text("install: true\n", encoding="utf-8")
            (user_dir / "configs").mkdir()
            (user_dir / "configs" / "app_config.yaml").write_text("user: true\n", encoding="utf-8")

            app_paths = self._load_module(install_dir, user_dir)
            app_paths.initialize_user_data()

            self.assertEqual(
                (user_dir / "configs" / "app_config.yaml").read_text(encoding="utf-8"),
                "user: true\n",
            )

    def test_resolve_path_prefers_user_runtime_paths_and_falls_back_to_install_resources(self) -> None:
        with tempfile.TemporaryDirectory() as install_tmp, tempfile.TemporaryDirectory() as user_tmp:
            install_dir = Path(install_tmp)
            user_dir = Path(user_tmp)
            (install_dir / "configs").mkdir()
            (install_dir / "data" / "demo").mkdir(parents=True)
            (install_dir / "data" / "demo" / "demo.xlsx").write_text("demo", encoding="utf-8")

            app_paths = self._load_module(install_dir, user_dir)

            self.assertEqual(
                app_paths.resolve_path("outputs/reports/report.json", for_write=True),
                user_dir / "outputs" / "reports" / "report.json",
            )
            self.assertEqual(
                app_paths.resolve_path("data/demo/demo.xlsx"),
                install_dir / "data" / "demo" / "demo.xlsx",
            )


if __name__ == "__main__":
    unittest.main()
