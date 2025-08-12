#!/bin/bash

echo "🚀 Starting Anime Guesser Application..."
echo ""

# Stop any existing containers
echo "Stopping any existing containers..."
docker-compose down

# Clean up any orphaned containers
docker-compose rm -f

# Build and start services
echo "Building and starting services..."
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to start..."
echo "This may take 5-10 minutes on first run to download AI models..."
echo ""

# Wait and check services
sleep 30

echo "Checking service status..."
docker-compose ps

echo ""
echo "🎉 Services are starting up!"
echo ""
echo "You can access:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8080/api/health"
echo "  CLIP Service: http://localhost:8001/health"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo ""