@echo off
echo 🧪 Testing Anime Guesser Setup...
echo.

REM Test 1: Check if Docker is running
echo 1. Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo    ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
) else (
    echo    ✅ Docker is running
)

REM Test 2: Check if docker-compose is available
echo 2. Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo    ❌ Docker Compose not found. Please install Docker Compose.
    pause
    exit /b 1
) else (
    echo    ✅ Docker Compose is available
)

REM Test 3: Build services
echo 3. Building services...
docker-compose build --no-cache
if errorlevel 1 (
    echo    ❌ Build failed. Check the logs above.
    pause
    exit /b 1
) else (
    echo    ✅ All services built successfully
)

REM Test 4: Start services
echo 4. Starting services...
docker-compose up -d

REM Wait for services to start
echo 5. Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Test 5: Check service health
echo 6. Testing service health...

REM Test backend
curl -s http://localhost:8080/api/health >nul 2>&1
if errorlevel 1 (
    echo    ❌ Backend API is not responding
) else (
    echo    ✅ Backend API is responding
)

REM Test CLIP service
echo 7. Testing CLIP service (this may take a few minutes on first run)...
for /l %%i in (1,1,30) do (
    curl -s http://localhost:8001/health >nul 2>&1
    if not errorlevel 1 (
        echo    ✅ CLIP service is responding
        goto :clip_ready
    ) else (
        echo    ⏳ Waiting for CLIP service... (%%i/30)
        timeout /t 10 /nobreak >nul
    )
)
:clip_ready

REM Test frontend
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo    ❌ Frontend is not responding
) else (
    echo    ✅ Frontend is responding
)

echo.
echo 🎉 Setup test complete!
echo.
echo If all tests passed, you can access:
echo    Frontend: http://localhost:3000
echo    Backend API: http://localhost:8080
echo    CLIP Service: http://localhost:8001
echo.
echo To stop services: docker-compose down
pause