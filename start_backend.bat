@echo off
echo ===================================
echo    Backend API Server - Start
echo ===================================
echo.

REM Check if .env exists
if not exist .env (
    echo [INFO] .env file not found. Creating from .env.example...
    copy .env.example .env
    echo [SUCCESS] .env file created.
    echo [WARNING] Please configure PostgreSQL connection in .env file!
    echo.
)

REM Check if virtual environment exists
if not exist venv (
    echo [INFO] Virtual environment not found. Creating...
    python -m venv venv
    echo [SUCCESS] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/Update dependencies
echo [INFO] Installing dependencies...
pip install -q -r requirements.txt
echo [SUCCESS] Dependencies installed
echo.

REM Check PostgreSQL
echo [INFO] Checking PostgreSQL connection...
echo [WARNING] Make sure PostgreSQL is running and database is created!
echo [INFO] If database not created, run: psql -U postgres -f init_db.sql
echo.

REM Run the application
echo ===================================
echo    Starting Backend API
echo ===================================
echo.
echo API will be available at: http://127.0.0.1:8000
echo Documentation: http://127.0.0.1:8000/docs
echo.
echo Default admin credentials:
echo   Username: admin
echo   Password: admin123
echo.
echo Press Ctrl+C to stop
echo.

python main.py
