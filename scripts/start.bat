@echo off
REM Quick Start Script for SVN Trading Bot
REM This script provides easy access to common tasks

echo 🤖 SVN Trading Bot - Quick Start
echo ================================

echo.
echo Select an option:
echo 1. Deploy to Vercel
echo 2. Run local development
echo 3. Migrate database
echo 4. Open documentation
echo 5. Exit

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo 🚀 Starting Vercel deployment...
    call scripts\deploy.bat
) else if "%choice%"=="2" (
    echo 💻 Starting local development server...
    vercel dev
) else if "%choice%"=="3" (
    echo 📊 Starting database migration...
    python scripts\migrate_db.py
) else if "%choice%"=="4" (
    echo 📖 Opening documentation...
    start docs\DEPLOYMENT_GUIDE.md
) else if "%choice%"=="5" (
    echo 👋 Goodbye!
    exit /b 0
) else (
    echo ❌ Invalid choice. Please try again.
    pause
    goto start
)

pause
