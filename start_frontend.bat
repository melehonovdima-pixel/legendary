@echo off
echo ===================================
echo    Frontend Web Server - Start
echo ===================================
echo.

REM Переход в папку front
cd front

REM Запуск веб-сервера на порту 5500
echo Starting web server on http://localhost:5500
echo.
echo Press Ctrl+C to stop
echo.

python -m http.server 5500
