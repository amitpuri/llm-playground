# MCP Atlassian Docker Container Runner (PowerShell)
# This script pulls and runs the MCP Atlassian server using environment variables from .env

param(
    [switch]$Force,
    [switch]$NoPull
)

# Function to write colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

Write-Host "MCP Atlassian Docker Container Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Error ".env file not found!"
    Write-Status "Please create a .env file with your Atlassian configuration."
    exit 1
}

# Load environment variables from .env file
Write-Status "Loading environment variables from .env file..."
$envVars = Get-Content ".env" | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' } | ForEach-Object {
    $key, $value = $_ -split '=', 2
    [PSCustomObject]@{ Key = $key.Trim(); Value = $value.Trim() }
}

# Set environment variables
foreach ($var in $envVars) {
    Set-Variable -Name $var.Key -Value $var.Value -Scope Script
}

# Validate required environment variables
$requiredVars = @("ATLASSIAN_BASE_URL", "ATLASSIAN_USERNAME", "ATLASSIAN_API_TOKEN", "ATLASSIAN_MCP_URL")
$missingVars = @()

foreach ($var in $requiredVars) {
    if ([string]::IsNullOrEmpty((Get-Variable -Name $var -ErrorAction SilentlyContinue).Value)) {
        $missingVars += $var
    }
}

if ($missingVars.Count -gt 0) {
    Write-Error "Missing required environment variables:"
    foreach ($var in $missingVars) {
        Write-Host "  - $var" -ForegroundColor Red
    }
    exit 1
}

# Extract port from MCP URL
$mcpPort = 8081  # Default port
if ($ATLASSIAN_MCP_URL -match ':(\d+)') {
    $mcpPort = $matches[1]
}

Write-Status "Using port: $mcpPort"

# Container configuration
$containerName = "mcp-atlassian"
$imageName = "ghcr.io/sooperset/mcp-atlassian:latest"

# Stop and remove existing container if it exists
Write-Status "Checking for existing container..."
$existingContainer = docker ps -a --format "table {{.Names}}" | Select-String "^$containerName$"
if ($existingContainer) {
    Write-Warning "Container '$containerName' already exists. Stopping and removing..."
    docker stop $containerName 2>$null
    docker rm $containerName 2>$null
    Write-Success "Existing container removed."
}

# Check if port is already in use
$portInUse = Get-NetTCPConnection -LocalPort $mcpPort -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($portInUse) {
    Write-Warning "Port $mcpPort is already in use!"
    Write-Status "Please stop the service using port $mcpPort or change the port in your .env file."
    exit 1
}

# Pull the latest image (unless --NoPull is specified)
if (-not $NoPull) {
    Write-Status "Pulling latest MCP Atlassian image..."
    $pullResult = docker pull $imageName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to pull image!"
        Write-Host $pullResult -ForegroundColor Red
        exit 1
    }
    Write-Success "Image pulled successfully."
} else {
    Write-Warning "Skipping image pull (--NoPull specified)"
}

# Run the container
Write-Status "Starting MCP Atlassian container..."
$dockerRunCmd = @(
    "run", "-d",
    "--name", $containerName,
    "-p", "$mcpPort`:$mcpPort",
    "-e", "ATLASSIAN_BASE_URL=$ATLASSIAN_BASE_URL",
    "-e", "ATLASSIAN_USERNAME=$ATLASSIAN_USERNAME",
    "-e", "ATLASSIAN_API_TOKEN=$ATLASSIAN_API_TOKEN",
    "-e", "JIRA_URL=$ATLASSIAN_BASE_URL",
    "-e", "CONFLUENCE_URL=$ATLASSIAN_BASE_URL/wiki",
    "--restart", "unless-stopped",
    $imageName
)

$runResult = docker @dockerRunCmd 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to start container!"
    Write-Host $runResult -ForegroundColor Red
    exit 1
}

# Wait a moment for container to start
Start-Sleep -Seconds 3

# Check if container is running
$runningContainer = docker ps --format "table {{.Names}}" | Select-String "^$containerName$"
if ($runningContainer) {
    Write-Success "MCP Atlassian container started successfully!"
    Write-Status "Container name: $containerName"
    Write-Status "MCP URL: $ATLASSIAN_MCP_URL"
    Write-Status "Port: $mcpPort"
    
    # Show container logs
    Write-Status "Container logs (last 10 lines):"
    docker logs --tail 10 $containerName
    
    Write-Host ""
    Write-Success "MCP Atlassian server is ready!"
    Write-Status "You can now run your Python scripts to connect to the MCP server."
    Write-Status "Example: python main.py diagnose"
    
} else {
    Write-Error "Failed to start container!"
    Write-Status "Container logs:"
    docker logs $containerName
    exit 1
}

# Show container status
Write-Host ""
Write-Status "Container status:"
docker ps --filter "name=$containerName" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

Write-Host ""
Write-Status "Useful commands:"
Write-Host "  - View logs: docker logs -f $containerName" -ForegroundColor Gray
Write-Host "  - Stop container: docker stop $containerName" -ForegroundColor Gray
Write-Host "  - Remove container: docker rm $containerName" -ForegroundColor Gray
Write-Host "  - Restart container: docker restart $containerName" -ForegroundColor Gray

Write-Host ""
Write-Status "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
