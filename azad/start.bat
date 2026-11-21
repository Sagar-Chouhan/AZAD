@echo off
setlocal
echo ===================================================
echo   Starting Azad Foundation MIS (Backend + Frontend)
echo ===================================================
echo.

cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found at backend\.venv
    echo Please make sure backend\.venv is created.
    pause
    exit /b 1
)

echo PostgreSQL Database URL is configured in backend\.env
echo Starting Uvicorn on http://localhost:8000 ...
echo The web application and API are available at: http://localhost:8000
echo Interactive API documentation (Swagger): http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server.
echo.

.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
pause
