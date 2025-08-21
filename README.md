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
- Node.js and npm (for MCP Inspector)
- Access to AI provider APIs (OpenAI, Anthropic, Google, Ollama)
- GitHub API access (for GitHub client)
- PostgreSQL database (for PostgreSQL client)

## 🎯 Demo Flow: From Testing to End-to-End

This playground follows a logical progression for learning and testing MCP servers:

1. **🔍 MCP Inspector** - Test individual MCP servers interactively
2. **📊 Individual MCP Clients** - Run GitHub and PostgreSQL MCP clients separately
3. **🌐 Web Playground** - End-to-end experience with multiple AI providers and MCP connectors

## 🔍 Step 1: MCP Inspector - Interactive Testing

MCP Inspector is a powerful debugging and development tool that allows you to inspect, test, and debug MCP servers interactively. Start here to understand how your MCP servers work.

### Installation

```bash
# Install MCP Inspector globally
npm install -g @modelcontextprotocol/inspector

# Or install locally in your project
npm install @modelcontextprotocol/inspector
```

### Testing GitHub MCP Server

1. **Launch MCP Inspector with GitHub MCP**:
   ```bash
   # Direct command line connection to GitHub MCP
   mcp-inspector --url https://api.githubcopilot.com/mcp --header "Authorization: Bearer ghp_XXXXXXXXXXXXXXXXXXXX" --token ghp_XXXXXXXXXXXXXXXXXXXX
   ```
   
   **Note**: Replace `ghp_XXXXXXXXXXXXXXXXXXXX` with your actual GitHub Personal Access Token.

2. **Alternative: Launch MCP Inspector GUI**:
   ```bash
   mcp-inspector
   ```
   
   Then connect to GitHub MCP Server:
   - Click "Connect to Server"
   - Select "GitHub" or enter: `https://api.githubcopilot.com/mcp/`
   - Configure authentication with your GitHub token

3. **Test GitHub Operations**:
   ```json
   // Example: List issues
   {
     "owner": "amitpuri",
     "repo": "mcp-clients-playground",
     "state": "open"
   }
   ```

### Testing PostgreSQL MCP Server

1. **Set up Database Connection**:
   ```bash
   # Set your database connection
   export DATABASE_URI="postgresql://user:password@localhost:5432/dbname"
   
   # Start the PostgreSQL MCP server
   postgres-mcp --access-mode=unrestricted --transport=sse
   ```

2. **Launch MCP Inspector**:
   ```bash
   mcp-inspector
   ```

3. **Connect to PostgreSQL MCP Server**:
   - Click "Connect to Server"
   - Select "PostgreSQL" or enter: `http://localhost:8000/sse`
   - No authentication required for local setup

4. **Test Database Operations**:
   ```sql
   -- Example: Query research papers
   SELECT url, title, date, abstract, category 
   FROM research_papers.ai_research_papers 
   ORDER BY date DESC 
   LIMIT 5;
   ```

### MCP Inspector Features

- **Interactive Tool Testing**: Test individual MCP tools with custom parameters
- **Request/Response Monitoring**: View detailed request and response data
- **Schema Inspection**: Browse tool schemas and documentation
- **Error Debugging**: Identify and troubleshoot connection and authentication issues
- **Performance Analysis**: Monitor tool execution times and performance
- **Multi-Server Support**: Connect to multiple MCP servers simultaneously

## 📊 Step 2: Individual MCP Clients

Once you've tested the MCP servers with Inspector, run the individual clients to see them in action.

### Database Setup - Sample Research Data

Before running the PostgreSQL MCP client, you need to set up the database with sample research data.

#### Quick Setup

1. **Install dependencies:**
   ```bash
   cd database
   pip install -r requirements.txt
   ```

2. **Configure environment (optional):**
   ```bash
   cp env_example.txt .env
   # Edit .env file to customize database connection if needed
   ```

3. **Run the setup script:**
   ```bash
   python setup_database.py
   ```

#### What the Setup Creates

**Schema: `research_papers`**

**Tables:**
- **`ai_research_papers`** - Main table containing AI research papers
  - `id` (SERIAL PRIMARY KEY)
  - `title` (VARCHAR(500))
  - `authors` (TEXT[]) - Array of author names
  - `abstract` (TEXT)
  - `publication_date` (DATE)
  - `journal` (VARCHAR(200))
  - `doi` (VARCHAR(100))
  - `keywords` (TEXT[]) - Array of keywords
  - `citation_count` (INTEGER)
  - `created_at` (TIMESTAMP)
  - `updated_at` (TIMESTAMP)

- **`research_topics`** - Research topic categories
  - `id` (SERIAL PRIMARY KEY)
  - `name` (VARCHAR(200) UNIQUE)
  - `description` (TEXT)
  - `parent_topic_id` (INTEGER) - Self-referencing for hierarchical topics
  - `created_at` (TIMESTAMP)

- **`paper_topics`** - Junction table linking papers to topics
  - `paper_id` (INTEGER) - Foreign key to ai_research_papers
  - `topic_id` (INTEGER) - Foreign key to research_topics
  - Primary key: (paper_id, topic_id)

**Views:**
- **`papers_with_topics`** - Convenient view showing papers with their associated topics

**Sample Data:**
- **7 Research Topics:** Machine Learning, Natural Language Processing, Computer Vision, Deep Learning, Reinforcement Learning, AI Ethics, Large Language Models
- **5 Research Papers:** Including famous papers like "Attention Is All You Need", "BERT", "GANs", "ResNet", and "AlphaGo"

#### Database Connection

The setup uses the following connection string by default:
```
postgresql://user:password@localhost:5432/dbname
```

**Note**: If your password contains special characters, URL-encode them. For example:
- `@` becomes `%40`
- `#` becomes `%23`
- `%` becomes `%25`
- `&` becomes `%26`

Example: `password@123` becomes `password%40123`

You can customize this by:
1. Creating a `.env` file with your own `DATABASE_URI`
2. Setting the `DATABASE_URI` environment variable
3. The script will fall back to the default if neither is provided

#### Verification

After setup, you can verify the installation by running:

```sql
-- Check tables
SELECT schemaname, tablename FROM pg_tables WHERE schemaname = 'research_papers';

-- Check sample data
SELECT COUNT(*) FROM research_papers.ai_research_papers;
SELECT COUNT(*) FROM research_papers.research_topics;

-- View papers with topics
SELECT title, topics FROM research_papers.papers_with_topics LIMIT 3;
```

### GitHub MCP Server - Reading Issues

The GitHub client allows you to fetch and analyze GitHub issues using the MCP protocol.

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

### PostgreSQL MCP Server - Reading Local Database

The PostgreSQL client enables you to query and analyze local PostgreSQL databases using MCP.

**Prerequisite**: Make sure you've completed the [Database Setup](#database-setup---sample-research-data) above before running this client.

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

## 🌐 Step 3: Web Playground - End-to-End Experience

The web playground provides an interactive interface for testing multiple AI providers and MCP connectors simultaneously. This is the final step where you can see everything working together.

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

### Troubleshooting

- **Connection Issues**: Use the connection status indicator to verify server connectivity
- **Authentication Problems**: Check token configuration and permissions
- **Tool Errors**: View detailed error messages and stack traces
- **Performance Issues**: Monitor execution times and identify bottlenecks
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

## 🎮 Complete Demo Flow

Follow this step-by-step progression to experience the full MCP playground:

### Step 1: Test with MCP Inspector
```bash
# Install MCP Inspector
npm install -g @modelcontextprotocol/inspector

# Test GitHub MCP
mcp-inspector --url https://api.githubcopilot.com/mcp --header "Authorization: Bearer YOUR_TOKEN" --token YOUR_TOKEN

# Test PostgreSQL MCP (after starting postgres-mcp server)
mcp-inspector
# Connect to http://localhost:8000/sse
```

### Step 2: Run Individual MCP Clients
```bash
# Set up database first (required for PostgreSQL client)
cd database
pip install -r requirements.txt
python setup_database.py

# GitHub Issues Client
cd ../github-issues
python main.py

# PostgreSQL Client (in another terminal)
cd ../pg
python main.py
```

### Step 3: End-to-End Web Playground
```bash
# Install and configure playground
cd playground
pip install -r requirements.txt
cp ../github-issues/env_example.txt .env
# Edit .env with your API keys

# Start the web playground
python app.py
# Open http://localhost:5000 in your browser
```

### What You'll Experience
1. **MCP Inspector**: Interactive testing of individual MCP tools
2. **Individual Clients**: See how each MCP server works independently
3. **Web Playground**: Complete integration with multiple AI providers and MCP connectors

## References

- [One Month in MCP: What I Learned the Hard Way](https://www.reddit.com/r/mcp/comments/1mub6g6/one_month_in_mcp_what_i_learned_the_hard_way/)
    - **STDIO: Powerful but painful** — Good for quick tasks; becomes impractical and labor-intensive for managing multiple servers.
    - **Local setups don’t scale** — Quick to start but hard to maintain and share for teams; local-first is risky and difficult to scale without automation.
    - **Dynamic allocation is key** — Spin up servers only when needed instead of keeping many running, which streamlines management and reduces headaches.
    - **Tool naming collisions cause problems** — Avoid duplicate names by using namespaces/groups to prevent silent failures with multiple servers.
    - **~40 tools limit bottleneck** — LLM performance drops beyond 40 tools; bundle tools thoughtfully for each workflow instead of loading too many.

- [Model Context Protocol (MCP) Curriculum for Beginners](https://github.com/microsoft/mcp-for-beginners/)
  
![Authorization flow](https://raw.githubusercontent.com/Azure-Samples/remote-mcp-apim-functions-python/refs/heads/main/infra/app/apim-oauth/diagrams/images/mcp-client-auth.png)


- [Context Engineering: An Emerging Concept in the MCP Ecosystem](https://github.com/microsoft/mcp-for-beginners/tree/main/05-AdvancedTopics/mcp-contextengineering)

  
```mermaid
graph LR
    A[User Input] --> B[Context Assembly]
    B --> C[Model Processing]
    C --> D[Response Generation]
    D --> E[State Management]
    E -->|Next Interaction| A
    
    style A fill:#A8D5BA,stroke:#000000,stroke-width:2px,color:#000000,font-weight:bold
    style B fill:#7FB3D5,stroke:#000000,stroke-width:2px,color:#000000,font-weight:bold
    style C fill:#F5CBA7,stroke:#000000,stroke-width:2px,color:#000000,font-weight:bold
    style D fill:#C39BD3,stroke:#000000,stroke-width:2px,color:#000000,font-weight:bold
    style E fill:#F9E79F,stroke:#000000,stroke-width:2px,color:#000000,font-weight:bold
```

```mermaid
sequenceDiagram
    participant User
    participant App
    participant MCP Server
    participant AI Model

    User->>App: Ask Question
    App->>MCP Server: Initial Request
    MCP Server->>AI Model: Minimal Context
    AI Model->>MCP Server: Initial Response
    
    alt Needs More Context
        MCP Server->>MCP Server: Identify Missing Context
        MCP Server->>MCP Server: Load Additional Context
        MCP Server->>AI Model: Enhanced Context
        AI Model->>MCP Server: Final Response
    end
    
    MCP Server->>App: Response
    App->>User: Answer
```

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
