param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$DesktopRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $ProjectRoot

function Remove-ProjectPath {
    param([string]$RelativePath)

    $target = Join-Path $ProjectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $target)) {
        return
    }

    $resolved = (Resolve-Path -LiteralPath $target).Path
    if (-not $resolved.StartsWith($ProjectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove path outside project root: $resolved"
    }

    Remove-Item -LiteralPath $resolved -Recurse -Force
}

$Python = "python"
if (Test-Path -LiteralPath (Join-Path $ProjectRoot ".venv\Scripts\python.exe")) {
    $Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
}

Write-Host "Project root: $ProjectRoot"
Write-Host "Python: $Python"

if (-not $SkipInstall) {
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -r desktop_windows\requirements.txt
}

Remove-ProjectPath "desktop_windows\build\datamonitor"
Remove-ProjectPath "desktop_windows\dist\DataMonitor"

& $Python -m PyInstaller `
    --clean `
    --noconfirm `
    --distpath (Join-Path $DesktopRoot "dist") `
    --workpath (Join-Path $DesktopRoot "build") `
    desktop_windows\packaging\datamonitor.spec

$ExePath = Join-Path $DesktopRoot "dist\DataMonitor\DataMonitor.exe"
if (-not (Test-Path -LiteralPath $ExePath)) {
    throw "Build finished without expected executable: $ExePath"
}

Write-Host ""
Write-Host "Build completed: $ExePath"
Write-Host "Run it with: desktop_windows\dist\DataMonitor\DataMonitor.exe"
