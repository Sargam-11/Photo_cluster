#!/bin/bash

# Deployment script for Photo Gallery application
set -e

# Configuration
ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.${ENVIRONMENT}"

echo "🚀 Deploying Photo Gallery to ${ENVIRONMENT} environment..."

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file $ENV_FILE not found!"
    echo "Please create it based on .env.example"
    exit 1
fi

# Load environment variables
export $(cat $ENV_FILE | grep -v '^#' | xargs)

# Validate required environment variables
required_vars=(
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "SECRET_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set!"
        exit 1
    fi
done

echo "✅ Environment validation passed"

# Create necessary directories
mkdir -p backups logs static

# Pull latest images
echo "📦 Pulling latest Docker images..."
docker-compose -f $COMPOSE_FILE pull

# Build custom images
echo "🔨 Building application images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down

# Start new containers
echo "🚀 Starting new containers..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
timeout=300
elapsed=0

while [ $elapsed -lt $timeout ]; do
    if docker-compose -f $COMPOSE_FILE ps | grep -q "unhealthy"; then
        echo "⏳ Services still starting... (${elapsed}s)"
        sleep 10
        elapsed=$((elapsed + 10))
    else
        echo "✅ All services are healthy!"
        break
    fi
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ Services failed to start within ${timeout} seconds"
    docker-compose -f $COMPOSE_FILE logs
    exit 1
fi

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f $COMPOSE_FILE exec -T backend alembic upgrade head

# Show status
echo "📊 Deployment status:"
docker-compose -f $COMPOSE_FILE ps

echo "✅ Deployment completed successfully!"
echo "🌐 Application should be available at: http://localhost"
echo "📚 API documentation: http://localhost/api/docs"

# Optional: Run smoke tests
if [ "$2" = "--test" ]; then
    echo "🧪 Running smoke tests..."
    ./scripts/smoke_test.sh
fi