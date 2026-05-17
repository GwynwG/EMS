# DataMonitor Windows 桌面版

这个目录专门放 Windows 桌面封装相关代码，普通网页端仍然使用项目根目录的 `app/streamlit_app.py`、`src/`、`configs/`、`data/` 和 `outputs/`。

桌面版的路径隔离由 `desktop_windows/runtime/` 完成：打包或运行桌面启动器时，配置、导入数据、模型、报告和日志会优先写入 `%LOCALAPPDATA%/DataMonitor`。直接运行项目根目录的网页端不会启用这套桌面路径逻辑。

## 目录说明

```text
desktop_windows/
├─ app/streamlit_app.py          # 桌面版 Streamlit 入口副本
├─ launcher.py                   # 双击启动器
├─ runtime/                      # 桌面版专用路径覆盖层
├─ packaging/
│  ├─ build_windows.ps1          # PyInstaller 主构建脚本
│  ├─ build_windows.bat          # 双击备用构建入口
│  ├─ datamonitor.spec           # PyInstaller spec
│  └─ installer.iss              # Inno Setup 脚本
├─ requirements.txt              # 桌面封装额外依赖
└─ tests/                        # 桌面封装隔离测试
```

## 本地启动桌面版

在项目根目录运行：

```powershell
python desktop_windows/launcher.py
```

启动器会自动尝试 `8501`、`8502`、`8503`、`8504`，启动成功后自动打开默认浏览器。

## 打包

```powershell
.\desktop_windows\packaging\build_windows.ps1
```

如果依赖已经安装过：

```powershell
.\desktop_windows\packaging\build_windows.ps1 -SkipInstall
```

产物位于：

```text
desktop_windows/dist/DataMonitor/DataMonitor.exe
```

发布解压版时要保留整个 `desktop_windows/dist/DataMonitor/` 目录。

## 生成安装包

先完成 PyInstaller 打包，然后用 Inno Setup 打开：

```text
desktop_windows/packaging/installer.iss
```

安装包输出到：

```text
desktop_windows/dist_installer/
```

默认安装包文件名：

```text
DataMonitor_Setup_v0.1.0.exe
```

## 用户运行数据

桌面版运行数据目录：

```text
%LOCALAPPDATA%/DataMonitor
```

首次运行会自动创建：

- `data/`
- `data/raw_excel/`
- `data/raw_dcs/`
- `data/processed/`
- `data/samples/`
- `data/demo/`
- `outputs/models/`
- `outputs/reports/`
- `outputs/logs/`
- `outputs/figures/`
- `configs/`

默认配置会从安装资源复制到用户目录。后续用户上传的数据、模型输出、报告和日志优先写入用户目录。

## 网页端不受影响

网页端继续使用原来的命令：

```powershell
streamlit run app/streamlit_app.py
```

这条命令仍按项目根目录解析 `configs/`、`data/`、`outputs/`，不会主动使用 `%LOCALAPPDATA%/DataMonitor`。
