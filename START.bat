@echo off
echo ╔═══════════════════════════════════════════════════════════╗
echo ║        УК ЖКХ - Система управления заявками              ║
echo ║              Автоматический запуск                        ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Проверка PostgreSQL
echo [1/3] Checking PostgreSQL...
echo.
echo Make sure PostgreSQL is running!
echo If not started, the backend will fail.
echo.
timeout /t 2 >nul

REM Запуск бэкенда в отдельном окне
echo [2/3] Starting Backend API Server...
start "УК ЖКХ - Backend API" cmd /k start_backend.bat
echo ✓ Backend starting in new window...
echo.
timeout /t 3 >nul

REM Запуск фронтенда в отдельном окне
echo [3/3] Starting Frontend Web Server...
start "УК ЖКХ - Frontend" cmd /k start_frontend.bat
echo ✓ Frontend starting in new window...
echo.

echo ╔═══════════════════════════════════════════════════════════╗
echo ║                  ✓ ALL SERVICES STARTED                  ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo Backend API:  http://127.0.0.1:8000
echo API Docs:     http://127.0.0.1:8000/docs
echo Frontend:     http://127.0.0.1:5500
echo.
echo Login credentials:
echo   Username: admin
echo   Password: admin123
echo.
echo To stop services: close both console windows
echo.

REM Автоматически открыть браузер (опционально)
timeout /t 3 >nul
echo Opening browser...
start http://127.0.0.1:5500

echo.
echo Press any key to close this window...
pause >nul
