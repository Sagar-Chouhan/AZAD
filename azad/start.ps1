# Azad Foundation MIS - Windows PowerShell Launcher
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting Azad Foundation MIS (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

$backendDir = Join-Path $PSScriptRoot "backend"
Set-Location $backendDir

$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Host "Error: Virtual environment not found at $pythonExe" -ForegroundColor Red
    exit 1
}

Write-Host "Starting server on http://localhost:8000 ..." -ForegroundColor Green
Write-Host "Application: http://localhost:8000" -ForegroundColor Yellow
Write-Host "API Docs:    http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Gray
Write-Host ""

& $pythonExe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
