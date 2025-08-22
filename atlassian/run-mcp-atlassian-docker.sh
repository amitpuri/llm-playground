#!/bin/bash

# MCP Atlassian Docker Container Runner
# This script pulls and runs the MCP Atlassian server using environment variables from .env

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_error ".env file not found!"
    print_status "Please create a .env file with your Atlassian configuration."
    exit 1
fi

# Load environment variables from .env file
print_status "Loading environment variables from .env file..."
source .env

# Validate required environment variables
required_vars=("ATLASSIAN_BASE_URL" "ATLASSIAN_USERNAME" "ATLASSIAN_API_TOKEN" "ATLASSIAN_MCP_URL")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

# Extract port from MCP URL
MCP_PORT=$(echo $ATLASSIAN_MCP_URL | sed -n 's/.*:\([0-9]*\).*/\1/p')
if [ -z "$MCP_PORT" ]; then
    MCP_PORT=8081  # Default port
fi

print_status "Using port: $MCP_PORT"

# Container configuration
CONTAINER_NAME="mcp-atlassian"
IMAGE_NAME="ghcr.io/sooperset/mcp-atlassian:latest"

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_warning "Container '$CONTAINER_NAME' already exists. Stopping and removing..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    print_success "Existing container removed."
fi

# Check if port is already in use
if lsof -Pi :$MCP_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port $MCP_PORT is already in use!"
    print_status "Please stop the service using port $MCP_PORT or change the port in your .env file."
    exit 1
fi

# Pull the latest image
print_status "Pulling latest MCP Atlassian image..."
docker pull $IMAGE_NAME
print_success "Image pulled successfully."

# Run the container
print_status "Starting MCP Atlassian container..."
docker run -d \
    --name $CONTAINER_NAME \
    -p $MCP_PORT:$MCP_PORT \
    -e ATLASSIAN_BASE_URL="$ATLASSIAN_BASE_URL" \
    -e ATLASSIAN_USERNAME="$ATLASSIAN_USERNAME" \
    -e ATLASSIAN_API_TOKEN="$ATLASSIAN_API_TOKEN" \
    -e JIRA_URL="$ATLASSIAN_BASE_URL" \
    -e CONFLUENCE_URL="$ATLASSIAN_BASE_URL/wiki" \
    --restart unless-stopped \
    $IMAGE_NAME

# Wait a moment for container to start
sleep 3

# Check if container is running
if docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_success "MCP Atlassian container started successfully!"
    print_status "Container name: $CONTAINER_NAME"
    print_status "MCP URL: $ATLASSIAN_MCP_URL"
    print_status "Port: $MCP_PORT"
    
    # Show container logs
    print_status "Container logs (last 10 lines):"
    docker logs --tail 10 $CONTAINER_NAME
    
    print_status ""
    print_success "MCP Atlassian server is ready!"
    print_status "You can now run your Python scripts to connect to the MCP server."
    print_status "Example: python main.py diagnose"
    
else
    print_error "Failed to start container!"
    print_status "Container logs:"
    docker logs $CONTAINER_NAME
    exit 1
fi

# Optional: Show container status
print_status ""
print_status "Container status:"
docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

print_status ""
print_status "Useful commands:"
echo "  - View logs: docker logs -f $CONTAINER_NAME"
echo "  - Stop container: docker stop $CONTAINER_NAME"
echo "  - Remove container: docker rm $CONTAINER_NAME"
echo "  - Restart container: docker restart $CONTAINER_NAME"
