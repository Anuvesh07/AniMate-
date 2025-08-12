@echo off
echo 🚀 Starting Anime Guesser Application...
echo This will start all services using Docker Compose
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ docker-compose not found. Please install Docker Compose.
    pause
    exit /b 1
)

echo 📦 Building and starting services...
docker-compose up --build

echo.
echo 🎉 Application should be running at:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8080
echo    CLIP Service: http://localhost:8001
echo.
echo Note: First startup may take 5-10 minutes to download CLIP model and populate database.
pause