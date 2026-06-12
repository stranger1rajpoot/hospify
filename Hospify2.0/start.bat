@echo off
echo ================================================
echo   HOSPIFY HMS - Setup Script
echo   Pakistan Hospital Management System
echo ================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause & exit
)

echo [1/4] Installing Python dependencies...
cd /d "%~dp0backend"
pip install -r requirements.txt
echo Done!

echo.
echo [2/4] Setting up database...
echo Please ensure XAMPP MySQL is running.
echo Run the SQL file: database\hospify.sql in phpMyAdmin
echo.

echo [3/4] Creating uploads directory...
mkdir uploads 2>nul
echo Done!

echo [4/4] Starting Hospify API server...
echo.
echo ================================================
echo  API Server: http://localhost:5000
echo  Frontend:   http://localhost/Hospify2.0/frontend/
echo  Admin Login: superadmin / Admin@1234
echo ================================================
echo.
python app.py
pause
