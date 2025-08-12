#!/bin/bash

echo "🧪 Testing Anime Guesser Setup..."
echo ""

# Test 1: Check if Docker is running
echo "1. Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo "   ✅ Docker is running"
else
    echo "   ❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Test 2: Check if docker-compose is available
echo "2. Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "   ✅ Docker Compose is available"
else
    echo "   ❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Test 3: Build services
echo "3. Building services..."
if docker-compose build --no-cache; then
    echo "   ✅ All services built successfully"
else
    echo "   ❌ Build failed. Check the logs above."
    exit 1
fi

# Test 4: Start services
echo "4. Starting services..."
docker-compose up -d

# Wait for services to start
echo "5. Waiting for services to start..."
sleep 10

# Test 5: Check service health
echo "6. Testing service health..."

# Test backend
if curl -s http://localhost:8080/api/health > /dev/null; then
    echo "   ✅ Backend API is responding"
else
    echo "   ❌ Backend API is not responding"
fi

# Test CLIP service (might take longer to start)
echo "7. Testing CLIP service (this may take a few minutes on first run)..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null; then
        echo "   ✅ CLIP service is responding"
        break
    else
        echo "   ⏳ Waiting for CLIP service... ($i/30)"
        sleep 10
    fi
done

# Test frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Frontend is responding"
else
    echo "   ❌ Frontend is not responding"
fi

echo ""
echo "🎉 Setup test complete!"
echo ""
echo "If all tests passed, you can access:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8080"
echo "   CLIP Service: http://localhost:8001"
echo ""
echo "To stop services: docker-compose down"