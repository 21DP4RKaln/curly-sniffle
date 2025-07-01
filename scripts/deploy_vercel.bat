@echo off
echo ====================================
echo   SVN Trading Bot - Vercel Deploy
echo ====================================
echo.

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed
    echo 📥 Install from: https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js found

REM Check/Install Vercel CLI
echo 📦 Checking Vercel CLI...
vercel --version >nul 2>&1
if errorlevel 1 (
    echo 📥 Installing Vercel CLI...
    npm install -g vercel
)
echo ✅ Vercel CLI ready

REM Check environment file
if not exist ".env.local" (
    echo ⚠️  No .env.local file found
    echo 📝 Creating from template...
    echo DATABASE_URL=postgresql://username:password@hostname:port/database > .env.local
    echo SECRET_KEY=your-secret-key-here-32-chars-minimum >> .env.local
    echo ALLOWED_EMAILS=sitvain12@gmail.com >> .env.local
    echo SMTP_HOST=smtp.gmail.com >> .env.local
    echo SMTP_PORT=587 >> .env.local
    echo SMTP_USER=your-email@gmail.com >> .env.local
    echo SMTP_PASSWORD=your-app-password >> .env.local
    echo.
    echo 🔧 Please edit .env.local with your actual values before deployment!
    pause
)

echo.
echo 🚀 Deploying to Vercel...
echo.
echo 📋 Remember to set these environment variables in Vercel dashboard:
echo    - DATABASE_URL (PostgreSQL connection string)
echo    - SECRET_KEY (32+ character random string)
echo    - ALLOWED_EMAILS (sitvain12@gmail.com)
echo    - SMTP_HOST (smtp.gmail.com)
echo    - SMTP_PORT (587)
echo    - SMTP_USER (your Gmail address)
echo    - SMTP_PASSWORD (your Gmail App Password)
echo.

vercel --prod

echo.
echo ✅ Deployment completed!
echo.
echo 📝 Next steps:
echo    1. Set environment variables in Vercel dashboard
echo    2. Test login with authorized email
echo    3. Check that email sending works
echo.
pause
