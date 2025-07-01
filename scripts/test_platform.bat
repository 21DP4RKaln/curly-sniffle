@echo off
echo ===============================================
echo   SVN Trading Bot - Test Suite
echo ===============================================
echo.

:: Set environment variables for testing
set FLASK_APP=api/index.py
set FLASK_ENV=development

echo 🧪 Testējam API endpoints...
echo.

:: Test 1: Health check
echo [1/5] Health check...
curl -s http://localhost:5000/health > nul 2>&1
if errorlevel 1 (
    echo ❌ Servera nav pieejams. Palaižiet start_local.bat vispirms.
    pause
    exit /b 1
) else (
    echo ✅ Serveris darbojas
)

:: Test 2: Test endpoint
echo [2/5] API test endpoint...
curl -s "http://localhost:5000/api/test" | find "ok" > nul
if errorlevel 1 (
    echo ❌ API test neizdevās
) else (
    echo ✅ API test izdevās
)

:: Test 3: Login page
echo [3/5] Login page...
curl -s "http://localhost:5000/login" | find "SVN Trading Bot" > nul
if errorlevel 1 (
    echo ❌ Login page neizdevās
) else (
    echo ✅ Login page darbojas
)

:: Test 4: Dashboard redirect (should need auth)
echo [4/5] Dashboard auth check...
curl -s "http://localhost:5000/dashboard" | find "SVN Trading Bot" > nul
if errorlevel 1 (
    echo ❌ Dashboard nav pieejams
) else (
    echo ✅ Dashboard darbojas
)

:: Test 5: Database initialization
echo [5/5] Database check...
if exist "svnbot.db" (
    echo ✅ Database fails eksistē
) else (
    echo ⚠️  Database fails nav atrasts (izveidosies pirmajā API izsaukumā)
)

echo.
echo ===============================================
echo   Test rezultāti
echo ===============================================
echo.
echo 🌐 Platforma URL: http://localhost:5000
echo 🔐 Login: http://localhost:5000/login  
echo 📊 Dashboard: http://localhost:5000/dashboard
echo 🧪 API Test: http://localhost:5000/api/test
echo.
echo Pārbaudiet vai viss darbojas brauswerī!
echo.
pause
