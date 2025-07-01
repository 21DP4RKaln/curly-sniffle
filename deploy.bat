@echo off
REM SVN Trading Bot - Vercel Deployment Script for Windows
REM Run this script to prepare and deploy your project to Vercel

echo 🚀 SVN Trading Bot - Vercel Deployment
echo ======================================

REM Check if required tools are installed
echo 📋 Checking prerequisites...

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed
    echo 📥 Install from: https://python.org/
    pause
    exit /b 1
)
echo ✅ Python found

REM Check for Git
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git is not installed
    echo 📥 Install from: https://git-scm.com/
    pause
    exit /b 1
)
echo ✅ Git found

REM Check for Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed (required for Vercel CLI^)
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

REM Prepare files for Vercel
echo 📁 Preparing files for Vercel...

if exist "requirements-vercel.txt" (
    copy /Y requirements-vercel.txt requirements.txt >nul
    echo ✅ Updated requirements.txt for Vercel
)

if exist "static\js\main-vercel.js" (
    copy /Y static\js\main-vercel.js static\js\main.js >nul
    echo ✅ Updated main.js for Vercel
)

REM Check environment variables
echo 🔧 Environment variables check...
if not exist ".env.local" (
    echo ⚠️  No .env.local file found
    echo 📝 Creating from template...
    copy .env.example .env.local >nul
    echo 🔧 Please edit .env.local with your actual values:
    echo    - DATABASE_URL
    echo    - SECRET_KEY
    echo    - ALLOWED_EMAILS
    echo.
    pause
)

REM Git initialization
echo 📚 Git repository setup...
if not exist ".git" (
    echo 📝 Initializing Git repository...
    git init
    git add .
    git commit -m "Initial Vercel-ready commit"
    
    echo 🌐 Please create a GitHub repository and run:
    echo    git remote add origin https://github.com/yourusername/svn-trading-bot.git
    echo    git branch -M main
    echo    git push -u origin main
    echo.
    pause
)

REM Database migration (optional)
echo 🗄️  Database migration...
set /p migrate_db="Do you want to migrate existing SQLite data? (y/N): "
if /i "%migrate_db%"=="y" (
    if exist "migrate_db.py" (
        if exist "src\SVNbot.db" (
            echo 📊 Running database migration...
            python migrate_db.py
        ) else (
            echo ⚠️  SQLite database not found, skipping...
        )
    ) else (
        echo ⚠️  Migration script not found, skipping...
    )
)

REM Vercel deployment
echo 🚀 Deploying to Vercel...
echo 📝 This will:
echo    1. Link your GitHub repository
echo    2. Configure environment variables
echo    3. Deploy to production
echo.

REM Login to Vercel
vercel login

REM Deploy
vercel --prod

echo.
echo 🎉 Deployment complete!
echo.
echo 📋 Next steps:
echo    1. Go to Vercel dashboard to add environment variables:
echo       - DATABASE_URL
echo       - SECRET_KEY
echo       - ALLOWED_EMAILS
echo.
echo    2. Test your deployment:
echo       - Visit your Vercel URL
echo       - Test login with authorized email
echo       - Check dashboard functionality
echo.
echo    3. Optional: Configure custom domain in Vercel dashboard
echo.
echo 📖 Need help? Check DEPLOYMENT_GUIDE.md
echo 🔗 Vercel Dashboard: https://vercel.com/dashboard
echo.
pause
