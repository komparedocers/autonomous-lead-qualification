#!/bin/bash

# Lead Qualification Platform Startup Script

set -e

echo "======================================"
echo "Lead Qualification Platform"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please update it with your API keys."
    echo ""
    echo "Important: Set your AI provider API keys in .env:"
    echo "  - OPENAI_API_KEY (for OpenAI GPT-4)"
    echo "  - ANTHROPIC_API_KEY (for Claude)"
    echo ""
    read -p "Press Enter to continue once you've updated .env..."
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🚀 Starting Lead Qualification Platform..."
echo ""

# Pull images
echo "📥 Pulling Docker images..."
docker-compose pull

# Build services
echo "🔨 Building services..."
docker-compose build

# Start services
echo "▶️  Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "======================================"
echo "✅ Platform is starting up!"
echo "======================================"
echo ""
echo "Access the platform:"
echo "  🌐 Dashboard:    http://localhost:3000"
echo "  🔧 API:          http://localhost:8080"
echo "  📊 Grafana:      http://localhost:3001 (admin/admin)"
echo "  📈 Prometheus:   http://localhost:9090"
echo "  🗄️  MinIO:        http://localhost:9001 (admin/admin_password_123)"
echo "  🔍 OpenSearch:   http://localhost:9200"
echo "  🕸️  Neo4j:        http://localhost:7474 (neo4j/password123)"
echo ""
echo "View logs:"
echo "  docker-compose logs -f [service-name]"
echo ""
echo "Stop all services:"
echo "  docker-compose down"
echo ""
echo "For more information, see README.md"
echo ""
