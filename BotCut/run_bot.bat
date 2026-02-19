@echo off
REM BotCut Launch Script for Windows

echo ==========================================
echo Starting BotCut Telegram Bot
echo ==========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy EnvExample.txt to .env and configure it.
    echo.
    pause
    exit /b 1
)

REM Check if HPMCut server is running
echo Checking HPMCut server...
curl -s http://127.0.0.1:3001/ >nul 2>&1
if errorlevel 1 (
    echo WARNING: HPMCut server is not running!
    echo Please start server_fastapi.py first.
    echo.
    echo Do you want to continue anyway? (Y/N^)
    set /p continue=
    if /i not "%continue%"=="Y" (
        exit /b 1
    )
)

echo.
echo Starting bot...
echo.

python main.py

pause
