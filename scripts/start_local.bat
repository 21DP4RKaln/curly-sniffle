@echo off
echo ===============================================
echo   SVN Trading Bot - MT5 AI Monitoring Platform
echo ===============================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python nav instalēts! Lūdzu instalējiet Python 3.9+
    echo    Lejupielādējiet no: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if .env.local exists
if not exist ".env.local" (
    echo ⚠️  .env.local fails nav atrasts!
    echo    Kopējot .env.example uz .env.local un konfigurējot...
    copy ".env.example" ".env.local"
    echo.
    echo ✅ .env.local fails izveidots!
    echo    Lūdzu rediģējiet .env.local failu ar saviem datiem:
    echo    - ALLOWED_EMAILS=jūsu@epasts.lv
    echo    - SMTP_USER=jūsu@gmail.com  
    echo    - SMTP_PASSWORD=jūsu-app-password
    echo.
    echo Pēc konfigurācijas palaižiet skriptu atkārtoti.
    pause
    exit /b 1
)

echo 🔍 Pārbaudam dependencies...

:: Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo 📦 Instalējam Python paketes...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Kļūda instalējot paketes!
        pause
        exit /b 1
    )
    echo ✅ Paketes instalētas veiksmīgi!
) else (
    echo ⚠️  requirements.txt nav atrasts!
)

echo.
echo 🚀 Palaižam SVN Trading Bot platformu...
echo.
echo 📱 Platforma būs pieejama: http://localhost:5000
echo 🔑 Izmantojiet savu e-pastu pieteikšanās
echo 📊 Dashboard: http://localhost:5000/dashboard
echo.

:: Start the Flask application
set FLASK_APP=api/index.py
set FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5000

echo.
echo Platformu apstādināja.
pause
