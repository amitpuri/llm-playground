@echo off
setlocal enabledelayedexpansion

REM MCP Atlassian Docker Container Runner (Windows)
REM This script pulls and runs the MCP Atlassian server using environment variables from .env

echo [INFO] MCP Atlassian Docker Container Runner
echo ================================================

REM Check if .env file exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo [INFO] Please create a .env file with your Atlassian configuration.
    pause
    exit /b 1
)

REM Load environment variables from .env file
echo [INFO] Loading environment variables from .env file...
for /f "tokens=1,* delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" (
        set "%%a=%%b"
    )
)

REM Validate required environment variables
set "missing_vars="
if "%ATLASSIAN_BASE_URL%"=="" set "missing_vars=!missing_vars! ATLASSIAN_BASE_URL"
if "%ATLASSIAN_USERNAME%"=="" set "missing_vars=!missing_vars! ATLASSIAN_USERNAME"
if "%ATLASSIAN_API_TOKEN%"=="" set "missing_vars=!missing_vars! ATLASSIAN_API_TOKEN"
if "%ATLASSIAN_MCP_URL%"=="" set "missing_vars=!missing_vars! ATLASSIAN_MCP_URL"

if not "!missing_vars!"=="" (
    echo [ERROR] Missing required environment variables:!missing_vars!
    pause
    exit /b 1
)

REM Extract port from MCP URL (simple extraction)
set "MCP_PORT=8081"
for /f "tokens=2 delims=:" %%a in ("%ATLASSIAN_MCP_URL%") do (
    for /f "tokens=1 delims=/" %%b in ("%%a") do set "MCP_PORT=%%b"
)

echo [INFO] Using port: %MCP_PORT%

REM Container configuration
set "CONTAINER_NAME=mcp-atlassian"
set "IMAGE_NAME=ghcr.io/sooperset/mcp-atlassian:latest"

REM Stop and remove existing container if it exists
echo [INFO] Checking for existing container...
docker ps -a --format "table {{.Names}}" | findstr /c:"%CONTAINER_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Container '%CONTAINER_NAME%' already exists. Stopping and removing...
    docker stop %CONTAINER_NAME% >nul 2>&1
    docker rm %CONTAINER_NAME% >nul 2>&1
    echo [SUCCESS] Existing container removed.
)

REM Check if port is already in use (Windows version)
netstat -an | findstr ":%MCP_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port %MCP_PORT% is already in use!
    echo [INFO] Please stop the service using port %MCP_PORT% or change the port in your .env file.
    pause
    exit /b 1
)

REM Pull the latest image
echo [INFO] Pulling latest MCP Atlassian image...
docker pull %IMAGE_NAME%
if %errorlevel% neq 0 (
    echo [ERROR] Failed to pull image!
    pause
    exit /b 1
)
echo [SUCCESS] Image pulled successfully.

REM Run the container
echo [INFO] Starting MCP Atlassian container...
docker run -d ^
    --name %CONTAINER_NAME% ^
    -p %MCP_PORT%:%MCP_PORT% ^
    -e ATLASSIAN_BASE_URL="%ATLASSIAN_BASE_URL%" ^
    -e ATLASSIAN_USERNAME="%ATLASSIAN_USERNAME%" ^
    -e ATLASSIAN_API_TOKEN="%ATLASSIAN_API_TOKEN%" ^
    -e JIRA_URL="%ATLASSIAN_BASE_URL%" ^
    -e CONFLUENCE_URL="%ATLASSIAN_BASE_URL%/wiki" ^
    --restart unless-stopped ^
    %IMAGE_NAME%

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start container!
    pause
    exit /b 1
)

REM Wait a moment for container to start
timeout /t 3 /nobreak >nul

REM Check if container is running
docker ps --format "table {{.Names}}" | findstr /c:"%CONTAINER_NAME%" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] MCP Atlassian container started successfully!
    echo [INFO] Container name: %CONTAINER_NAME%
    echo [INFO] MCP URL: %ATLASSIAN_MCP_URL%
    echo [INFO] Port: %MCP_PORT%
    
    REM Show container logs
    echo [INFO] Container logs (last 10 lines):
    docker logs --tail 10 %CONTAINER_NAME%
    
    echo.
    echo [SUCCESS] MCP Atlassian server is ready!
    echo [INFO] You can now run your Python scripts to connect to the MCP server.
    echo [INFO] Example: python main.py diagnose
    
) else (
    echo [ERROR] Failed to start container!
    echo [INFO] Container logs:
    docker logs %CONTAINER_NAME%
    pause
    exit /b 1
)

REM Show container status
echo.
echo [INFO] Container status:
docker ps --filter "name=%CONTAINER_NAME%" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo [INFO] Useful commands:
echo   - View logs: docker logs -f %CONTAINER_NAME%
echo   - Stop container: docker stop %CONTAINER_NAME%
echo   - Remove container: docker rm %CONTAINER_NAME%
echo   - Restart container: docker restart %CONTAINER_NAME%

echo.
echo [INFO] Press any key to exit...
pause >nul
