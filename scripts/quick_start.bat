@echo off
echo ====================================
echo    SVN Trading Bot - Quick Setup
echo ====================================
echo.

REM Check if .env.local exists
if exist ".env.local" (
    echo ✅ .env.local already exists
) else (
    echo 📝 Creating .env.local file...
    echo # Environment Variables for SVN Trading Bot > .env.local
    echo DATABASE_URL=sqlite:///svnbot.db >> .env.local
    echo SECRET_KEY=svn-bot-secret-key-change-this-in-production >> .env.local
    echo ALLOWED_EMAILS=sitvain12@gmail.com >> .env.local
    echo. >> .env.local
    echo # Email Configuration (Optional for production^) >> .env.local
    echo SMTP_HOST=smtp.gmail.com >> .env.local
    echo SMTP_PORT=587 >> .env.local
    echo SMTP_USER= >> .env.local
    echo SMTP_PASSWORD= >> .env.local
    echo ✅ Created .env.local file
)

echo.
echo 📦 Installing Python dependencies...
python -m pip install -r requirements.txt

echo.
echo 🚀 Starting local development server...
echo.
echo 📋 Setup Information:
echo    - Authorized Email: sitvain12@gmail.com
echo    - Local URL: http://localhost:5000
echo    - Development mode: Codes will be shown in console
echo.
echo 💡 To configure email sending:
echo    1. Edit .env.local file
echo    2. Add your Gmail App Password to SMTP_USER and SMTP_PASSWORD
echo.

pause
echo.
echo Starting server...
python -c "from api.auth import app; app.run(debug=True, port=5000)"
