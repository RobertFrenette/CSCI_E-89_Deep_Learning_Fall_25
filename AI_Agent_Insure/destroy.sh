#!/bin/bash

set -e

# Suppress warnings by default (set SHOW_WARNINGS=1 to show them)
if [ "${SHOW_WARNINGS:-}" != "1" ]; then
    export COMPOSE_IGNORE_ORPHANS=1
    filter_warnings() {
        "$@" 2>&1 | grep -v -i -E '(warn|warning|deprecated)' || true
    }
else
    filter_warnings() {
        "$@"
    }
fi

echo "🔥 Destroying AI Insurance Infrastructure..."
echo ""

# Delete deployment log file if it exists
if [ -f "logs/deploy.log" ]; then
    echo "🗑️  Removing deployment log file..."
    rm -f logs/deploy.log
    echo "✅ Deployment log removed"
    echo ""
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    exit 1
fi

# Step 1: Run docker-compose down (stops everything first)
echo "🛑 Step 1: Running docker-compose down..."
filter_warnings docker-compose down
echo "✅ docker-compose down completed"

# Step 2: Ensure all containers are deleted
echo ""
echo "🧹 Step 2: Ensuring all containers are deleted..."
containers=(
    "insure-postgres" "insure-mongodb" "insure-chromadb" "insure-admin-backend"
    "insure-admin-frontend" "insure-client-backend" "insure-client-frontend"
    "insure-ollama" "insure-ai-agent" "insure-dashboard"
)
for container in "${containers[@]}"; do
    if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
        docker rm -f "$container" 2>/dev/null && echo "   ✅ Removed: $container" || true
    fi
done
echo "✅ All containers checked/removed"

# Step 3: Ensure all volumes are deleted (after containers)
echo ""
echo "🧹 Step 3: Ensuring all volumes are deleted..."
# Try multiple naming patterns for each volume
volumes=("postgres-data" "mongo-data" "chromadb-data" "ollama-models")
for volume_base in "${volumes[@]}"; do
    for vol_name in "ai_agent_insure_${volume_base}" "insure_${volume_base}" "${volume_base}"; do
        if docker volume ls --format "{{.Name}}" | grep -q "^${vol_name}$"; then
            docker volume rm -f "$vol_name" 2>/dev/null && echo "   ✅ Removed: $vol_name" || true
            break
        fi
    done
done
# Remove any remaining project volumes
remaining=$(docker volume ls --format "{{.Name}}" | grep -E "(insure|postgres|mongo|chromadb|ollama)" || true)
if [ -n "$remaining" ]; then
    echo "$remaining" | while read -r vol; do
        [ -n "$vol" ] && docker volume rm -f "$vol" 2>/dev/null && echo "   ✅ Removed: $vol" || true
    done
fi
# Prune orphaned volumes
docker volume prune -f 2>/dev/null && echo "   ✅ Orphaned volumes removed" || true
echo "✅ All volumes checked/removed"

# Step 4: Ensure all images are deleted (after volumes)
echo ""
echo "🧹 Step 4: Ensuring all images are deleted..."
# Remove images from docker-compose config
images=$(docker-compose config --images 2>/dev/null | grep -v "^$" || true)
if [ -n "$images" ]; then
    echo "$images" | while read -r image; do
        [ -n "$image" ] && docker rmi -f "$image" 2>/dev/null && echo "   ✅ Removed: $image" || true
    done
fi
# Remove built images explicitly
built_images=(
    "insure-admin-backend:latest" "insure-admin-frontend:latest"
    "insure-client-backend:latest" "insure-client-frontend:latest" "insure-dashboard:latest"
    "ai_agent_insure-admin-backend:latest" "ai_agent_insure-admin-frontend:latest"
    "ai_agent_insure-client-backend:latest" "ai_agent_insure-client-frontend:latest"
    "ai_agent_insure-dashboard:latest"
)
for image in "${built_images[@]}"; do
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${image}$"; then
        docker rmi -f "$image" 2>/dev/null && echo "   ✅ Removed: $image" || true
    fi
done
# Remove any remaining project images
remaining=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "^(insure-|ai_agent_insure-)" || true)
if [ -n "$remaining" ]; then
    echo "$remaining" | while read -r image; do
        [ -n "$image" ] && [ "$image" != "<none>:<none>" ] && \
            docker rmi -f "$image" 2>/dev/null && echo "   ✅ Removed: $image" || true
    done
fi
echo "✅ All images checked/removed"

# Step 5: Delete the docker network (after images)
echo ""
echo "🌐 Step 5: Deleting Docker network..."
if docker network inspect insure-network &> /dev/null 2>&1; then
    docker network rm insure-network 2>/dev/null && echo "✅ Network removed!" || echo "ℹ️  Network removal attempted"
else
    echo "ℹ️  Network 'insure-network' does not exist"
fi

# Step 6: Run docker image prune (last step, after network)
echo ""
echo "🧹 Step 6: Pruning unused Docker images..."
filter_warnings docker image prune -f
echo "✅ Unused Docker images pruned!"

# Step 7: Clean up test artifacts (optional - local filesystem cleanup)
echo ""
echo "🧹 Step 7: Cleaning up test artifacts..."
# Remove Python virtual environments created during testing
test_venvs=(
    "client-app/backend/venv"
    "client-app/frontend/venv"
    "ai-agent/venv"
)
for venv_path in "${test_venvs[@]}"; do
    if [ -d "$venv_path" ]; then
        rm -rf "$venv_path" && echo "   ✅ Removed: $venv_path" || true
    fi
done
echo "✅ Test artifacts cleaned up"

echo ""
echo "✅ Destruction complete!"
echo ""
echo "To verify: docker network ls | grep insure"
