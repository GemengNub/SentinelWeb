@echo off
REM ============================================================
REM Sentinel - Quick Start (Docker Mode)
REM ============================================================
REM Just run this file to start everything in Docker!
REM ============================================================

title Sentinel
color 0A

echo.
echo ========================================
echo   SENTINEL - Quick Start
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found!
    echo.
    echo Please install Docker Desktop:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

REM Create .env if missing
if not exist "backend\.env" (
    echo Creating environment file...
    copy "backend\.env.example" "backend\.env" >nul
)

echo Stopping existing services...
echo.

REM Stop any existing services
docker-compose -f infra\docker-compose.yml down

echo Building and starting services (with rebuild)...
echo.

REM Build and start all services (--force-recreate to pick up new tasks)
docker-compose -f infra\docker-compose.yml up -d --build --force-recreate

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start services
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   SUCCESS! Services are running
echo ========================================
echo.
echo   Application:  http://localhost:3000
echo   API:          http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo.
echo   Data Sources (Celery Beat):
echo   - USGS Earthquakes (every 60s)
echo   - OpenWeather (every 60s)
echo   - NOAA Weather Alerts (every 60s)
echo   - PAGASA Earthquakes (every 60s)
echo   - JMA Earthquakes (every 60s)
echo   - NASA FIRMS Wildfire (every 60s)
echo.
echo   Run 'docker-compose -f infra\docker-compose.yml logs -f' to see logs
echo   Run 'docker-compose -f infra\docker-compose.yml down' to stop
echo.
echo Opening application in browser...
start http://localhost:3000

pause
