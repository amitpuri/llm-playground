"""
MCP connectors using LangChain MCP adapters for GitHub and PostgreSQL integration.
"""
import time
import json
import re
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from .models import MCPConnector, MCPGitHubConfig, MCPPostgresConfig, GitHubIssue, ResearchPaper, DebugInfo


class BaseMCPConnector(MCPConnector):
    """Base class for MCP connectors with common functionality."""
    
    def __init__(self, url: str, auth_token: Optional[str] = None):
        self.url = url
        # Note: auth_token is not used in this implementation
        # Authentication should be handled by the MCP server configuration
        self._client: Optional[MultiServerMCPClient] = None
        self._server_name: str = ""
    
    def _get_connection_config(self) -> Dict[str, Any]:
        """Get connection configuration for the MCP server."""
        # Determine transport based on URL
        if "sse" in self.url.lower():
            transport = "sse"
        else:
            transport = "streamable_http"
            
        config = {
            "url": self.url,
            "transport": transport
        }
        # Remove auth_token from config as it's not supported by MultiServerMCPClient
        # Authentication should be handled by the MCP server itself or via headers
        return config
    
    async def connect(self) -> MultiServerMCPClient:
        """Connect to the MCP server."""
        if self._client is None:
            try:
                connections = {
                    self._server_name: self._get_connection_config()
                }
                self._client = MultiServerMCPClient(connections)
                # Test the connection by trying to get tools
                await self._client.get_tools(server_name=self._server_name)
            except Exception as e:
                print(f"[MCP] Connection failed for {self._server_name}: {e}")
                # Don't raise the exception, just log it and return None
                self._client = None
                return None
        return self._client
    
    def _extract_fenced_json(self, text: str) -> Optional[str]:
        """Extract JSON from fenced code blocks."""
        if not isinstance(text, str):
            return None
        
        # Try ```json ... ```
        match = re.search(r"```json\s*(.*?)\s*```", text, re.S | re.I)
        if match:
            return match.group(1)
        
        # Try ``` ... ``` with JSON content
        match = re.search(r"```\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", text, re.S)
        if match:
            return match.group(1)
        
        return None
    
    def _try_parse_json(self, text: str) -> Optional[Any]:
        """Try to parse JSON from text."""
        try:
            return json.loads(text)
        except Exception:
            return None
    
    async def fetch_data(self, **kwargs) -> Dict[str, Any]:
        """Fetch data from the MCP server."""
        raise NotImplementedError("Subclasses must implement fetch_data")


class GitHubMCPConnector(BaseMCPConnector):
    """GitHub MCP connector using LangChain MCP adapters."""
    
    def __init__(self, config: MCPGitHubConfig):
        super().__init__(config.url, config.auth_token)
        self.config = config
        self._server_name = "github"
        
        # Extract owner from repo if not provided
        if not self.config.owner and self.config.repo:
            if '/' in self.config.repo:
                self.config.owner = self.config.repo.split('/')[0]
    
    def is_enabled(self) -> bool:
        """Check if the connector is enabled."""
        return self.config.enabled
    
    async def fetch_data(self, limit_issues: int = 3, limit_comments: int = 5) -> Dict[str, Any]:
        """Fetch GitHub issues and comments."""
        start_time = time.time()
        debug_info = DebugInfo(
            operation="fetch_github_issues",
            response_time=0.0
        )
        
        try:
            client = await self.connect()
            
            if client is None:
                debug_info.response_time = time.time() - start_time
                debug_info.error = "Failed to connect to MCP server"
                debug_info.mcp_calls = [{"error_type": "ConnectionFailed", "details": "Client is None"}]
                return {
                    "issues": [],
                    "debug": debug_info.__dict__
                }
            
            # Get tools from GitHub MCP server
            tools = await client.get_tools(server_name=self._server_name)
            
            issues = []
            
            # Find the list_issues tool
            list_issues_tool = None
            list_comments_tool = None
            
            for tool in tools:
                if "list_issues" in tool.name.lower():
                    list_issues_tool = tool
                elif "list_issue_comments" in tool.name.lower():
                    list_comments_tool = tool
            
            if list_issues_tool:
                # Use the tool to list issues
                try:
                    issues_result = await list_issues_tool.ainvoke({
                        "owner": self.config.owner,
                        "repo": self.config.repo,
                        "state": "open",
                        "per_page": limit_issues
                    })
                except Exception as e:
                    print(f"[MCP] Error invoking list_issues tool: {e}")
                    issues_result = []
                
                if issues_result and isinstance(issues_result, list):
                    for issue_data in issues_result[:limit_issues]:
                        comments = []
                        
                        # Get comments for this issue if we have the tool
                        if list_comments_tool:
                            try:
                                comments_result = await list_comments_tool.ainvoke({
                                    "owner": self.config.owner,
                                    "repo": self.config.repo,
                                    "issue_number": issue_data.get("number", 0),
                                    "per_page": limit_comments
                                })
                                
                                if comments_result and isinstance(comments_result, list):
                                    for comment_data in comments_result[:limit_comments]:
                                        comments.append({
                                            "id": comment_data.get("id"),
                                            "user": comment_data.get("user", {}).get("login", "Unknown"),
                                            "body": comment_data.get("body", ""),
                                            "created_at": comment_data.get("created_at"),
                                            "updated_at": comment_data.get("updated_at")
                                        })
                            except Exception as e:
                                print(f"Error fetching comments: {e}")
                        
                        github_issue = GitHubIssue(
                            number=issue_data.get("number", 0),
                            title=issue_data.get("title", ""),
                            body=issue_data.get("body", ""),
                            state=issue_data.get("state", "open"),
                            created_at=issue_data.get("created_at", ""),
                            updated_at=issue_data.get("updated_at", ""),
                            comments=comments
                        )
                        issues.append(github_issue)
            
            debug_info.response_time = time.time() - start_time
            debug_info.mcp_calls = [{
                "issues_fetched": len(issues),
                "repo": f"{self.config.owner}/{self.config.repo}",
                "tools_found": len(tools)
            }]
            
            return {
                "issues": [issue.__dict__ for issue in issues],
                "debug": debug_info.__dict__
            }
            
        except Exception as e:
            debug_info.response_time = time.time() - start_time
            debug_info.error = f"MCP connection failed: {str(e)}"
            debug_info.mcp_calls = [{"error_type": type(e).__name__, "details": str(e)}]
            
            print(f"[MCP] GitHub connector error: {e}")
            return {
                "issues": [],
                "debug": debug_info.__dict__
            }


class PostgresMCPConnector(BaseMCPConnector):
    """PostgreSQL MCP connector using LangChain MCP adapters."""
    
    def __init__(self, config: MCPPostgresConfig):
        super().__init__(config.url, config.auth_token)
        self.config = config
        self._server_name = "postgres"
    
    def is_enabled(self) -> bool:
        """Check if the connector is enabled."""
        return self.config.enabled
    
    async def fetch_data(self, limit_rows: int = 8, sql_query: str = None) -> Dict[str, Any]:
        """Fetch research papers from PostgreSQL."""
        start_time = time.time()
        debug_info = DebugInfo(
            operation="fetch_research_papers",
            response_time=0.0
        )
        
        try:
            client = await self.connect()
            
            if client is None:
                debug_info.response_time = time.time() - start_time
                debug_info.error = "Failed to connect to MCP server"
                debug_info.mcp_calls = [{"error_type": "ConnectionFailed", "details": "Client is None"}]
                return {
                    "rows": [],
                    "debug": debug_info.__dict__
                }
            
            # Get tools from PostgreSQL MCP server
            tools = await client.get_tools(server_name=self._server_name)
            
            papers = []
            
            # Find the execute_sql tool
            execute_sql_tool = None
            for tool in tools:
                if "execute_sql" in tool.name.lower() or "sql" in tool.name.lower():
                    execute_sql_tool = tool
                    break
            
            if execute_sql_tool:
                # Execute SQL query
                if sql_query is None:
                    sql_query = self.config.sample_sql
                if "LIMIT" not in sql_query.upper():
                    sql_query += f" LIMIT {limit_rows}"
                
                result = await execute_sql_tool.ainvoke({"sql": sql_query})
                
                # Parse the result - it's a string containing a list representation
                parsed_result = result
                if isinstance(result, str):
                    try:
                        # Use eval() to parse the string representation of the list
                        # This is safe because we're only parsing database query results
                        import datetime
                        import zoneinfo
                        eval_globals = {
                            'datetime': datetime,
                            'zoneinfo': zoneinfo
                        }
                        parsed_result = eval(result, eval_globals)
                    except Exception as e:
                        print(f"[MCP] Failed to parse result string: {e}")
                        parsed_result = result
                
                if parsed_result and isinstance(parsed_result, list):
                    for row in parsed_result:
                        # Convert datetime objects to strings for JSON serialization
                        processed_row = {}
                        for key, value in row.items():
                            if hasattr(value, 'isoformat'):  # datetime objects
                                processed_row[key] = value.isoformat()
                            else:
                                processed_row[key] = value
                        
                        # Map the actual database columns to ResearchPaper fields
                        paper = ResearchPaper(
                            title=processed_row.get("title", "Unknown Title"),
                            authors=processed_row.get("authors", "Unknown Authors"),
                            abstract=processed_row.get("abstract", ""),
                            date=processed_row.get("date", ""),
                            category=processed_row.get("category", ""),
                            url=processed_row.get("url", "")
                        )
                        papers.append(paper)
            
            debug_info.response_time = time.time() - start_time
            debug_info.mcp_calls = [{
                "papers_fetched": len(papers),
                "sql_query": sql_query,
                "tools_found": len(tools)
            }]
            
            return {
                "rows": [paper.__dict__ for paper in papers],
                "debug": debug_info.__dict__
            }
            
        except Exception as e:
            debug_info.response_time = time.time() - start_time
            debug_info.error = f"MCP connection failed: {str(e)}"
            debug_info.mcp_calls = [{"error_type": type(e).__name__, "details": str(e)}]
            
            print(f"[MCP] PostgreSQL connector error: {e}")
            return {
                "rows": [],
                "debug": debug_info.__dict__
            }


class MCPConnectorFactory:
    """Factory for creating MCP connectors."""
    
    @classmethod
    def create_github_connector(cls, config: MCPGitHubConfig) -> GitHubMCPConnector:
        """Create a GitHub MCP connector."""
        return GitHubMCPConnector(config)
    
    @classmethod
    def create_postgres_connector(cls, config: MCPPostgresConfig) -> PostgresMCPConnector:
        """Create a PostgreSQL MCP connector."""
        return PostgresMCPConnector(config)
