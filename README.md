![AI Generated](https://img.shields.io/badge/AI-Generated-blueviolet?style=for-the-badge&logo=openai&logoColor=white)

# MCP Clients Playground

This repository contains examples and utilities for working with Model Context Protocol (MCP) servers, specifically GitHub and PostgreSQL clients.

## 📁 Project Structure

```
mcp-clients-playground/
├── github-issues/          # GitHub MCP Server - reading issues
│   ├── main.py            # Main GitHub client application
│   ├── issue_fetch.py     # Issue fetching utilities
│   ├── diagnose.py        # Diagnostic tools
│   ├── requirements.txt   # Python dependencies
│   ├── env_example.txt    # Environment configuration template
│   └── *.json            # Sample issue data exports
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
- Access to GitHub API (for GitHub client)
- PostgreSQL database (for PostgreSQL client)

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

## 🔧 Common Configuration

### Environment Variables

Both clients use environment variables for configuration. See the respective `env_example.txt` files for detailed options.

### MCP Server URLs

- **GitHub**: `https://api.githubcopilot.com/mcp/`
- **PostgreSQL**: `http://localhost:8000/sse` (when using SSE transport)

## 📝 Examples

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

1. **Authentication Errors**: Ensure your GitHub token has the necessary permissions
2. **Connection Issues**: Verify MCP server URLs and network connectivity
3. **Data Parsing**: Check that response data matches expected formats

### Diagnostic Tools

- Use `diagnose.py` in the GitHub client for troubleshooting
- Check server logs for detailed error messages
- Verify environment variable configuration

## 📚 Dependencies

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

**Note**: The `requirements.txt` files in the `pg/` and `database/` directories contain the Python dependencies needed for the PostgreSQL client application and database setup scripts.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
