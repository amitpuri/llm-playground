![AI Generated](https://img.shields.io/badge/AI-Generated-blueviolet?style=for-the-badge&logo=openai&logoColor=white)

# MCP Clients Playground

A comprehensive playground for experimenting with Model Context Protocol (MCP) servers, featuring a web-based interface for testing multiple AI providers and MCP connectors.

## 🎯 Overview

This repository provides a complete environment for working with MCP servers, including:
- **Web Playground**: Interactive web interface for testing AI providers and MCP connectors
- **GitHub MCP Client**: Fetch and analyze GitHub issues using MCP
- **PostgreSQL MCP Client**: Query and analyze PostgreSQL databases using MCP
- **Database Setup**: Complete database setup with sample research data

## 🔒 Security Notice

**⚠️ IMPORTANT: Never commit API keys, tokens, or sensitive credentials to version control!**

- The `playground/settings.json` file is **NOT** tracked by git (added to `.gitignore`)
- Always use environment variables (`.env` files) for sensitive configuration
- Keep your API keys secure and never share them publicly
- If you accidentally commit sensitive information, immediately rotate/regenerate your keys

## 📁 Project Structure

```
mcp-clients-playground/
├── playground/              # 🆕 Web-based MCP Playground
│   ├── app.py              # Flask web application
│   ├── settings.json       # Configuration file (NOT tracked by git)
│   ├── requirements.txt    # Python dependencies
│   ├── static/             # Frontend assets
│   │   └── main.js         # JavaScript functionality
│   └── templates/          # HTML templates
│       ├── base.html       # Base template
│       └── index.html      # Main interface
├── github-issues/          # GitHub MCP Server - reading issues
│   ├── main.py            # Main GitHub client application
│   ├── issue_fetch.py     # Issue fetching utilities
│   ├── diagnose.py        # Diagnostic tools
│   ├── requirements.txt   # Python dependencies
│   └── env_example.txt    # Environment configuration template
├── pg/                    # PostgreSQL MCP Server - reading local database
│   ├── main.py           # Main PostgreSQL client application
│   ├── requirements.txt  # Python dependencies
│   └── env_example.txt   # Environment configuration template
└── database/              # Database setup scripts
    ├── setup_schema.sql  # SQL schema and sample data
    ├── setup_database.py # Python setup script
    ├── requirements.txt  # Python dependencies
    └── README.md         # Setup instructions
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip or uv package manager
- Access to AI provider APIs (OpenAI, Anthropic, Google, Ollama)
- GitHub API access (for GitHub client)
- PostgreSQL database (for PostgreSQL client)

## 🌐 Web Playground (NEW!)

The web playground provides an interactive interface for testing multiple AI providers and MCP connectors simultaneously.

### Features

- **Multi-Provider Support**: OpenAI, Anthropic, Google Gemini, and Ollama
- **MCP Integration**: GitHub and PostgreSQL MCP connectors
- **Smart Prompt Optimization**: Uses Ollama (gemma3:270m) to optimize prompts
- **Real-time Chat Interface**: Interactive conversation with AI models
- **Settings Management**: Web-based configuration interface
- **Debug Logging**: Comprehensive logging for troubleshooting

### Installation

```bash
cd playground
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
```bash
cp ../github-issues/env_example.txt .env
```

2. Configure your environment variables:
```bash
# AI Provider Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key
OLLAMA_BASE_URL=http://localhost:11434

# MCP Configuration
GITHUB_TOKEN=your_github_personal_access_token
MCP_SERVER_URL=https://api.githubcopilot.com/mcp/
MCP_SSE_SERVER_URL=http://localhost:8000/sse
GITHUB_REPO=owner/repo

# Optional: Custom settings file path
PLAYGROUND_SETTINGS_PATH=settings.json
```

**🔒 Security Note**: The `settings.json` file is automatically ignored by git. Your API keys and tokens will be loaded from environment variables and stored locally only.

### Usage

```bash
# Start the web playground
python app.py
```

Then open your browser to `http://localhost:5000`

### Web Interface Features

- **Chat Tab**: Interactive conversation with selected AI providers
- **Settings Tab**: Configure AI providers and MCP connectors
- **Debug Tab**: View detailed logs and error messages
- **Prompt Optimization**: Automatically optimize prompts using Ollama
- **MCP Connector Status**: Visual indicators for enabled MCP services

## 📊 GitHub MCP Server - Reading Issues

The GitHub client allows you to fetch and analyze GitHub issues using the MCP protocol.

### Installation

```bash
cd github-issues
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
```bash
cp env_example.txt .env
```

2. Configure your environment variables:
```bash
# GitHub Configuration
GITHUB_TOKEN=your_github_personal_access_token_here

# MCP Server Configuration
MCP_SERVER_URL=https://api.githubcopilot.com/mcp/

# Logging Configuration (optional)
LOG_LEVEL=INFO
GITHUB_REPO=owner/repo

# for issue_fetch.py
ISSUE_NUMBER=number
```

### Usage

```bash
# Run the main GitHub client
python main.py

# Fetch specific issues
python issue_fetch.py

# Run diagnostics
python diagnose.py
```

### Features

- Fetch open issues from GitHub repositories
- Retrieve issue comments and metadata
- Export issue data to JSON format
- Diagnostic tools for troubleshooting
- Support for GraphQL-style responses

## 🗄️ PostgreSQL MCP Server - Reading Local Database

The PostgreSQL client enables you to query and analyze local PostgreSQL databases using MCP.

### Database Setup

First, set up the database with sample data:

```bash
cd database
pip install -r requirements.txt
python setup_database.py
```

This will create:
- A `research_papers` schema with tables for AI research papers
- Sample data including famous papers like "Attention Is All You Need", "BERT", "GANs", etc.
- Proper indexes and views for efficient querying

### Installation

1. Install the PostgreSQL MCP server:

```bash
# Using pipx (recommended)
pipx install postgres-mcp

# Or using uv
uv pip install postgres-mcp
```

2. Install Python dependencies:

```bash
cd pg
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
```bash
cp env_example.txt .env
```

2. Configure your environment variables:
```bash
POSTGRES_MCP_URL=http://localhost:8000/sse
```

### Running the PostgreSQL MCP Server

1. Set your database connection string:
```bash
export DATABASE_URI="postgresql://user:password@localhost:5432/dbname"
```

**Note**: If your password contains special characters, URL-encode them. For example:
- `@` becomes `%40`
- `#` becomes `%23`
- `%` becomes `%25`
- `&` becomes `%26`

Example: `password@123` becomes `password%40123`

2. Run the PostgreSQL MCP server:
```bash
# Run with SSE transport (HTTP) - serves at :8000/sse
postgres-mcp --access-mode=unrestricted --transport=sse
```

### Usage

```bash
# Run the main PostgreSQL client
python main.py
```

### Features

- Execute SQL queries against PostgreSQL databases
- Fetch table schemas and metadata
- Retrieve sample data from tables
- JSON-safe data handling
- Support for complex data types (datetime, UUID, etc.)

## 🔧 Configuration

### Environment Variables

All components use environment variables for configuration. See the respective `env_example.txt` files for detailed options.

### MCP Server URLs

- **GitHub**: `https://api.githubcopilot.com/mcp/`
- **PostgreSQL**: `http://localhost:8000/sse` (when using SSE transport)

### Settings File (Playground)

The playground uses a `settings.json` file for configuration. **This file is NOT tracked by git for security reasons.**

```json
{
  "providers": {
    "openai": {
      "enabled": false,
      "name": "OpenAI",
      "base_url": "https://api.openai.com/v1",
      "api_key": "",
      "temperature": 0.2,
      "default_model": "gpt-5"
    },
    "anthropic": {
      "enabled": true,
      "name": "Anthropic",
      "base_url": "https://api.anthropic.com",
      "api_key": "",
      "temperature": 0.2,
      "default_model": "claude-3-7-sonnet-latest"
    },
    "ollama": {
      "enabled": true,
      "name": "Ollama",
      "base_url": "http://localhost:11434",
      "api_key": "",
      "temperature": 0.2,
      "default_model": "gemma3:270m"
    },
    "google": {
      "enabled": false,
      "name": "Google",
      "base_url": "https://generativelanguage.googleapis.com",
      "api_key": "",
      "temperature": 0.2,
      "default_model": "gemini-2.5-pro"
    }
  },
  "mcp": {
    "github": {
      "enabled": true,
      "url": "https://api.githubcopilot.com/mcp/",
      "auth_token": "",
      "repo": "owner/repo"
    },
    "postgres": {
      "enabled": true,
      "url": "http://localhost:8000/sse",
      "auth_token": "",
      "sample_sql": "SELECT url, title, date, abstract, category FROM research_papers.ai_research_papers ORDER BY date DESC LIMIT 5;"
    }
  }
}
```

**🔒 Security**: API keys and tokens are loaded from environment variables and should never be hardcoded in this file.

## 📝 Examples

### Web Playground Example

```python
# The playground automatically handles MCP client initialization
# and provides a web interface for testing

# Start the server
python app.py

# Access the web interface at http://localhost:5000
# Configure providers and MCP connectors through the settings tab
# Use the chat interface to interact with AI models and MCP services
```

### GitHub Issues Example

```python
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

# Initialize client
client = Client(
    "github",
    auth=BearerAuth(os.getenv("GITHUB_TOKEN")),
    server_url=os.getenv("MCP_SERVER_URL")
)

# Fetch issues
issues = await client.call_tool("list_issues", {
    "owner": "owner",
    "repo": "repo",
    "state": "open"
})
```

### PostgreSQL Example

```python
from fastmcp import Client

# Initialize client
client = Client("postgres", server_url=os.getenv("POSTGRES_MCP_URL"))

# Execute SQL query
result = await client.call_tool("execute_sql", {
    "sql": "SELECT * FROM research_papers.ai_research_papers LIMIT 10"
})
```

## 🛠️ Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure your API tokens have the necessary permissions
2. **Connection Issues**: Verify MCP server URLs and network connectivity
3. **Data Parsing**: Check that response data matches expected formats
4. **Ollama Connection**: Ensure Ollama is running locally for prompt optimization

### Diagnostic Tools

- Use the **Debug Tab** in the web playground for detailed logging
- Use `diagnose.py` in the GitHub client for troubleshooting
- Check server logs for detailed error messages
- Verify environment variable configuration

### Web Playground Troubleshooting

- **Provider Not Working**: Check API keys and base URLs in settings
- **MCP Connectors Not Responding**: Verify MCP server URLs and authentication
- **Prompt Optimization Failing**: Ensure Ollama is running with gemma3:270m model

## 📚 Dependencies

### Web Playground
- `flask>=2.0.0`
- `python-dotenv>=1.0.0`
- `requests>=2.25.0`
- `fastmcp>=0.1.0`

### GitHub Client
- `fastmcp>=0.1.0`
- `pydantic>=2.0.0`
- `httpx>=0.24.0`
- `python-dotenv>=1.0.0`

### PostgreSQL Client
- `postgres-mcp` (installed via pipx/uv)
- `fastmcp>=0.1.0`
- `python-dotenv>=1.0.0`

### Database Setup
- `psycopg2-binary>=2.9.0`

## 🎮 Getting Started with the Playground

1. **Install Dependencies**:
   ```bash
   cd playground
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp ../github-issues/env_example.txt .env
   # Edit .env with your API keys
   ```

3. **Start the Server**:
   ```bash
   python app.py
   ```

4. **Access the Interface**:
   - Open `http://localhost:5000` in your browser
   - Go to Settings tab to configure providers and MCP connectors
   - Use the Chat tab to interact with AI models and MCP services

5. **Test MCP Integration**:
   - Enable GitHub and/or PostgreSQL MCP connectors
   - Ask questions that require data from these services
   - Watch as the AI models use MCP tools to fetch and analyze data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

**🔒 Security Guidelines for Contributors**:
- Never commit API keys, tokens, or sensitive credentials
- Always use environment variables for configuration
- Test with dummy/placeholder values
- If you find exposed credentials, report them immediately

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
