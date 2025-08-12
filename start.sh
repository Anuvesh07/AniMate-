#!/bin/bash

echo "🚀 Starting Anime Guesser Application..."
echo "This will start all services using Docker Compose"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

echo "📦 Building and starting services..."
docker-compose up --build

echo ""
echo "🎉 Application should be running at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8080"
echo "   CLIP Service: http://localhost:8001"
echo ""
echo "Note: First startup may take 5-10 minutes to download CLIP model and populate database."