@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MirrorSync Git Initialization
echo ========================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Git not found. Please install Git for Windows
    exit /b 1
)

REM Initialize repository
echo Initializing Git repository...
git init
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to initialize repository
    exit /b 1
)

REM Add all files
echo Adding files...
git add .

REM Create initial commit
echo Creating initial commit...
git commit -m "Initial commit: MirrorSync Controller - Unified Android Device Management System"
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create commit
    exit /b 1
)

REM Show status
echo.
echo ========================================
echo Git repository initialized!
echo ========================================
echo.
git log --oneline -1
echo.
echo Next steps:
echo 1. Add remote: git remote add origin https://github.com/your-org/MirrorSyncController.git
echo 2. Push: git push -u origin main
echo.
pause