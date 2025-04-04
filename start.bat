@echo off
echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Checking ngrok installation...
ngrok --version
if errorlevel 1 (
    echo Error: ngrok is not installed or not in PATH
    pause
    exit /b 1
)

echo Starting Flask application...
start cmd /k "cd /d %~dp0 && python src/app.py"
if errorlevel 1 (
    echo Error: Failed to start Flask application
    pause
    exit /b 1
)

echo Waiting for Flask to start...
timeout /t 10

echo Starting ngrok...
start cmd /k "cd /d %~dp0 && ngrok http --url=dominant-bunny-feasible.ngrok-free.app 5000"
if errorlevel 1 (
    echo Error: Failed to start ngrok
    pause
    exit /b 1
)

echo.
echo ============================================
echo Both services started!
echo Flask is running at http://localhost:5000
echo Public URL: https://dominant-bunny-feasible.ngrok-free.app
echo ============================================
echo.
echo Press any key to exit...
pause > nul 