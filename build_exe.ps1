$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "IT Support Diagnostic Toolkit wird gebaut..." -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonPath)) {
    Write-Host "Fehler: Virtuelle Umgebung wurde nicht gefunden." -ForegroundColor Red
    Write-Host "Erwarteter Pfad: $pythonPath"
    exit 1
}

if (Test-Path ".\build") {
    Remove-Item ".\build" -Recurse -Force
}

if (Test-Path ".\dist") {
    Remove-Item ".\dist" -Recurse -Force
}

if (Test-Path ".\IT-Support-Diagnostic-Toolkit.spec") {
    Remove-Item ".\IT-Support-Diagnostic-Toolkit.spec" -Force
}

& $pythonPath -m PyInstaller `
    --name "IT-Support-Diagnostic-Toolkit" `
    --onefile `
    --noconsole `
    --clean `
    --paths "." `
    --hidden-import "src.services.scan_comparison_service" `
    --hidden-import "src.gui.comparison_window" `
    --collect-all "customtkinter" `
    --collect-all "matplotlib" `
    "src\gui\app.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Der Build ist fehlgeschlagen." -ForegroundColor Red
    exit $LASTEXITCODE
}

$exePath = Join-Path $projectRoot "dist\IT-Support-Diagnostic-Toolkit.exe"

if (-not (Test-Path $exePath)) {
    Write-Host ""
    Write-Host "Fehler: Die EXE wurde nicht erstellt." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Build erfolgreich." -ForegroundColor Green
Write-Host "EXE: $exePath"
Write-Host ""

Start-Process explorer.exe -ArgumentList "/select,`"$exePath`""
