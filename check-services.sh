#!/bin/bash

echo "🔍 Checking Anime Guesser Services..."
echo ""

# Check Docker containers
echo "📦 Docker Containers:"
docker-compose ps
echo ""

# Check service health
echo "🏥 Service Health Checks:"

echo "Backend API:"
curl -s http://localhost:8080/api/health | jq . 2>/dev/null || echo "❌ Backend not responding"
echo ""

echo "CLIP Service:"
curl -s http://localhost:8001/health | jq . 2>/dev/null || echo "❌ CLIP service not responding"
echo ""

echo "Frontend:"
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is responding"
else
    echo "❌ Frontend not responding"
fi
echo ""

# Check logs if services are down
echo "📋 Recent Logs (last 10 lines each):"
echo ""
echo "Backend logs:"
docker-compose logs --tail=10 backend
echo ""
echo "CLIP service logs:"
docker-compose logs --tail=10 clip-service
echo ""
echo "Frontend logs:"
docker-compose logs --tail=10 frontend