# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


desktop_root = Path(SPECPATH).resolve().parent
project_root = desktop_root.parent


def add_tree(datas, source_root: Path, relative_path: str, target_path: str | None = None) -> None:
    source = source_root / relative_path
    if source.exists():
        datas.append((str(source), (target_path or relative_path).replace("\\", "/")))


def safe_collect_data(package: str):
    try:
        return collect_data_files(package)
    except Exception:
        return []


def safe_collect_metadata(package: str):
    try:
        return copy_metadata(package)
    except Exception:
        return []


def safe_collect_submodules(package: str):
    try:
        return collect_submodules(package)
    except Exception:
        return []


datas = []
add_tree(datas, desktop_root, "app", "app")
add_tree(datas, desktop_root, "runtime", "runtime")
for relative in ("src", "configs", "data/demo", "assets", "outputs"):
    add_tree(datas, project_root, relative)

datas += safe_collect_data("streamlit")
datas += safe_collect_metadata("streamlit")
datas += safe_collect_metadata("altair")

hiddenimports = [
    "streamlit.web.cli",
    "streamlit.runtime.scriptrunner.magic_funcs",
    "streamlit.components.v1",
    "yaml",
    "openpyxl",
    "joblib",
    "sklearn.ensemble",
    "sklearn.ensemble._iforest",
    "sklearn.decomposition",
    "sklearn.decomposition._pca",
    "sklearn.preprocessing",
    "sklearn.preprocessing._data",
    "sklearn.cross_decomposition",
    "sklearn.cross_decomposition._pls",
    "matplotlib",
    "matplotlib.backends.backend_agg",
    "networkx",
    "plotly",
    "streamlit_echarts",
]

for package in ("streamlit.runtime", "streamlit.web", "streamlit_echarts"):
    hiddenimports += safe_collect_submodules(package)

hiddenimports = sorted(set(hiddenimports))

a = Analysis(
    [str(desktop_root / "launcher.py")],
    pathex=[str(desktop_root), str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "IPython",
        "PyQt5",
        "dask",
        "distributed",
        "jupyter",
        "notebook",
        "pytest",
        "skimage",
        "tensorflow",
        "torch",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DataDiagnostics",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DataDiagnostics",
)
