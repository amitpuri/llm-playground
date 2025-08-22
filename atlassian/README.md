# Atlassian MCP Client

A consolidated Python client for interacting with Atlassian services (Jira and Confluence) through the Model Context Protocol (MCP).

## Overview

This client provides a unified interface for:
- **Jira Operations**: Search issues, read specific issues, get projects, boards, and user profiles
- **Confluence Operations**: Search pages, read specific pages, get page children
- **Diagnostics**: Comprehensive health checks and tool discovery
- **Data Export**: Save results to JSON files for further analysis

## Files Structure

```
atlassian/
├── atlassian_client.py    # Main client class and convenience functions
├── main.py               # Command-line interface
├── test_consolidated.py  # Test script for the consolidated client
├── requirements.txt      # Python dependencies
├── env_example.txt       # Environment variables template
├── .env                  # Your actual environment configuration
├── run-mcp-atlassian-docker.sh    # Docker script for Linux/macOS
├── run-mcp-atlassian-docker.bat   # Docker script for Windows CMD
├── run-mcp-atlassian-docker.ps1   # Docker script for Windows PowerShell
└── README.md            # This file
```

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp env_example.txt .env
   # Edit .env with your Atlassian credentials
   ```

3. **Start MCP Server** (Choose one method):

   **Option A: Using Docker Scripts (Recommended)**
   
   For Windows (PowerShell - Recommended):
   ```powershell
   # Run with default settings
   .\run-mcp-atlassian-docker.ps1

   # Run without pulling latest image (faster)
   .\run-mcp-atlassian-docker.ps1 -NoPull

   # Run with force (overwrites existing container)
   .\run-mcp-atlassian-docker.ps1 -Force
   ```

   For Windows (Command Prompt):
   ```cmd
   run-mcp-atlassian-docker.bat
   ```

   For Linux/macOS:
   ```bash
   # Make script executable (first time only)
   chmod +x run-mcp-atlassian-docker.sh

   # Run the script
   ./run-mcp-atlassian-docker.sh
   ```

   **Option B: Manual Docker Command**
   ```bash
   docker run -d --name mcp-atlassian \
     -p 8081:8081 \
     -e ATLASSIAN_BASE_URL=https://your-domain.atlassian.net \
     -e ATLASSIAN_USERNAME=your-email@example.com \
     -e ATLASSIAN_API_TOKEN=your-api-token \
     --transport streamable-http \
     ghcr.io/sooperset/mcp-atlassian:latest
   ```

### 🐳 Docker Scripts Features

The provided Docker scripts offer several advantages:

#### PowerShell Script (Recommended for Windows)
- ✅ **Colored output** for better readability
- ✅ **Parameter support** (`-NoPull`, `-Force`)
- ✅ **Better error handling**
- ✅ **Port availability check**
- ✅ **Container status monitoring**

#### Batch Script
- ✅ **Windows Command Prompt compatible**
- ✅ **Basic error handling**
- ✅ **Port availability check**

#### Bash Script
- ✅ **Unix/Linux/macOS compatible**
- ✅ **Colored output**
- ✅ **Comprehensive error handling**

#### What the Scripts Do
1. **Validate Environment**: Check if `.env` file exists and has required variables
2. **Port Check**: Verify the specified port is available
3. **Container Management**: Stop and remove existing containers if they exist
4. **Image Pull**: Download the latest MCP Atlassian Docker image
5. **Container Start**: Run the container with your configuration
6. **Health Check**: Verify the container started successfully
7. **Status Display**: Show container logs and status

### Prerequisites
- **Docker Desktop** installed and running
- **`.env` file** with your Atlassian configuration
- **PowerShell** (for Windows PowerShell script)

## Usage

### Command Line Interface

The main script provides a comprehensive CLI for all operations:

```bash
# Run diagnostics
python main.py diagnose

# Read specific Jira issue
python main.py read-issue MDP-6

# Read specific Confluence page
python main.py read-page 2588673

# Search Jira issues
python main.py search-jira "project = MDP"

# Search Confluence pages
python main.py search-confluence "Research Paper"

# List available tools
python main.py list-tools
```

### Programmatic Usage

```python
from atlassian_client import AtlassianMCPClient

# Using the client class
async with AtlassianMCPClient() as client:
    # Run diagnostics
    diagnostics = await client.run_diagnostics()
    
    # Read specific issue
    issue = await client.read_specific_issue("MDP-6")
    
    # Search issues
    results = await client.search_jira_issues("project = MDP", 10)

# Using convenience functions
from atlassian_client import read_jira_issue, search_confluence_pages

issue = await read_jira_issue("MDP-6")
pages = await search_confluence_pages("Research Paper", space_key="SD")
```

## Features

### 🔍 Diagnostics
- Connection status verification
- Tool availability discovery
- Jira and Confluence health checks
- Data accessibility testing

### 📋 Jira Operations
- **Search Issues**: JQL-based search with customizable results
- **Read Issues**: Detailed issue information including comments
- **Projects**: List all accessible projects
- **Boards**: Get agile boards information
- **User Profile**: Current user information

### 📄 Confluence Operations
- **Search Pages**: Query-based page search
- **Read Pages**: Full page content and metadata
- **Page Children**: Get child pages of a specific page

### 💾 Data Export
- Automatic JSON file generation with timestamps
- Structured data formatting
- Easy integration with other tools

## Environment Variables

```bash
# Atlassian Configuration
ATLASSIAN_BASE_URL=https://your-domain.atlassian.net
ATLASSIAN_USERNAME=your-email@example.com
ATLASSIAN_API_TOKEN=your-api-token

# MCP Server Configuration
ATLASSIAN_MCP_URL=http://localhost:8081/mcp

# Optional: Jira Configuration
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY

# Optional: Confluence Configuration
CONFLUENCE_SPACE_KEY=YOUR_SPACE_KEY

# Optional: Logging
LOG_LEVEL=INFO
```

## Testing

Run the test script to verify everything works:

```bash
python test_consolidated.py
```

## Next Steps

After successfully running the Docker container:

1. **Test the connection**:
   ```bash
   python main.py diagnose
   ```

2. **Create a project** in your Jira instance (if none exists)

3. **Test issue creation**:
   ```bash
   python main.py search-jira "project = YOUR_PROJECT_KEY"
   ```

## Troubleshooting

### Common Issues

1. **Connection Failed**: Ensure the MCP server is running and accessible
2. **Authentication Error**: Verify your API token has sufficient permissions
3. **No Data Found**: The Atlassian instance might be empty or have permission restrictions
4. **Tool Not Found**: Some tools might not be available in your MCP server version

### Docker Scripts Troubleshooting

#### Port Already in Use
```
[WARNING] Port 8081 is already in use!
```
**Solution**: Change the port in your `.env` file or stop the service using that port.

#### Missing Environment Variables
```
[ERROR] Missing required environment variables: ATLASSIAN_API_TOKEN
```
**Solution**: Check your `.env` file and ensure all required variables are set.

#### Container Failed to Start
```
[ERROR] Failed to start container!
```
**Solution**: Check the container logs with `docker logs mcp-atlassian`

#### Permission Issues (Linux/macOS)
```
Permission denied
```
**Solution**: Make the script executable: `chmod +x run-mcp-atlassian-docker.sh`

### Useful Docker Commands

After running the Docker scripts, you can use these commands:

```bash
# View container logs
docker logs -f mcp-atlassian

# Stop the container
docker stop mcp-atlassian

# Remove the container
docker rm mcp-atlassian

# Restart the container
docker restart mcp-atlassian

# Check container status
docker ps --filter "name=mcp-atlassian"
```

### Debug Mode

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file.

## Architecture

The client uses a layered architecture:

1. **MCP Layer**: Raw communication with the MCP server
2. **Client Layer**: Unified interface for all operations
3. **Utility Layer**: Convenience functions and data formatting
4. **CLI Layer**: Command-line interface for easy usage

## Contributing

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation for new features
4. Ensure backward compatibility

## License

This project follows the same license as the parent repository.
