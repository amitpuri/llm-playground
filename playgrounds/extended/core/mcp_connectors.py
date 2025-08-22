"""
MCP connectors module following the Strategy pattern.
Each connector implements the MCPConnector interface.
"""
import time
import json
import re
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import asyncio

# Optional: pip install fastmcp
try:
    from fastmcp import Client as MCPClient
    from fastmcp.client.auth import BearerAuth as MCPBearerAuth
except ImportError:
    MCPClient = None
    MCPBearerAuth = None

from .models import MCPConnector, MCPGitHubConfig, MCPPostgresConfig, GitHubIssue, ResearchPaper, DebugInfo


class BaseMCPConnector(MCPConnector):
    """Base class for MCP connectors with common functionality."""
    
    def __init__(self, url: str, auth_token: Optional[str] = None):
        self.url = url
        self.auth_token = auth_token
        self._client = None
    
    def _mcp_connect(self):
        """Create MCP client connection."""
        if MCPClient is None:
            raise RuntimeError("fastmcp not installed. pip install fastmcp")
        
        auth = MCPBearerAuth(self.auth_token) if self.auth_token else None
        return MCPClient(self.url, auth=auth)
    
    async def connect(self) -> Any:
        """Connect to the MCP server."""
        self._client = self._mcp_connect()
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
    
    def _jsonify_tool_result(self, payload: Any) -> Any:
        """Normalize fastmcp ToolResult payloads into python objects."""
        data = getattr(payload, "content", payload)
        if isinstance(data, dict) and "content" in data:
            data = data["content"]
        
        def join_text_chunks(chunks):
            parts = []
            for chunk in chunks:
                text = getattr(chunk, "text", None)
                if isinstance(text, str):
                    parts.append(text)
            return "\n".join(parts).strip()
        
        # Handle list of TextContent
        if isinstance(data, list) and data and hasattr(data[0], "text"):
            raw = join_text_chunks(data)
            if not raw:
                return data
            
            # Try direct JSON
            parsed = self._try_parse_json(raw)
            if parsed is not None:
                return parsed
            
            # Try fenced JSON
            inner = self._extract_fenced_json(raw)
            if inner:
                parsed = self._try_parse_json(inner)
                if parsed is not None:
                    return parsed
            
            # Try naive JSON-ization
            naive = raw.replace("None", "null").replace("True", "true").replace("False", "false")
            naive = re.sub(r"(?<!\\)\'", '"', naive)
            parsed = self._try_parse_json(naive)
            if parsed is not None:
                return parsed
            
            return raw
        
        # Handle single TextContent
        if hasattr(data, "text") and isinstance(getattr(data, "text"), str):
            raw = data.text
            parsed = self._try_parse_json(raw)
            if parsed is not None:
                return parsed
            
            inner = self._extract_fenced_json(raw)
            if inner:
                parsed = self._try_parse_json(inner)
                if parsed is not None:
                    return parsed
            
            naive = raw.replace("None", "null").replace("True", "true").replace("False", "false")
            naive = re.sub(r"(?<!\\)\'", '"', naive)
            parsed = self._try_parse_json(naive)
            if parsed is not None:
                return parsed
            
            return raw
        
        return data


class GitHubMCPConnector(BaseMCPConnector):
    """GitHub MCP connector implementation."""
    
    def __init__(self, config: MCPGitHubConfig):
        super().__init__(config.url, config.auth_token)
        self.config = config
    

    
    async def fetch_issues_and_comments(self, limit_issues: int = 3, 
                                      limit_comments: int = 5) -> Dict[str, Any]:
        """Fetch GitHub issues and comments."""
        debug = DebugInfo()
        
        if not self.config.enabled or not self.config.url or not self.config.repo:
            print(f"[MCP-GitHub] Disabled or not configured: enabled={self.config.enabled}, url={self.config.url}, repo={self.config.repo}")
            return {"issues": [], "debug": {**debug.__dict__, "error": "github_mcp_disabled_or_not_configured"}}
        
        owner_repo = self.config.repo.strip()
        if "/" not in owner_repo:
            print(f"[MCP-GitHub] Invalid repo format: {owner_repo}")
            return {"issues": [], "debug": {**debug.__dict__, "error": "GITHUB repo must be owner/repo"}}
        
        owner, repo = owner_repo.split("/", 1)
        print(f"[MCP-GitHub] Fetching issues from {owner}/{repo}")
        
        try:
            async with self._mcp_connect() as client:
                # List tools
                t0 = time.perf_counter()
                try:
                    print(f"[MCP-GitHub] Listing tools...")
                    tools = await client.list_tools()
                    debug.tools = [getattr(t, "name", None) or t.get("name") for t in tools]
                    print(f"[MCP-GitHub] Available tools: {debug.tools}")
                    debug.calls.append({
                        "tool": "list_tools",
                        "input": {},
                        "ok": True,
                        "duration_ms": int((time.perf_counter() - t0) * 1000),
                        "output_preview": str(debug.tools)[:200],
                    })
                except Exception as e:
                    print(f"[MCP-GitHub] Error listing tools: {e}")
                    debug.calls.append({
                        "tool": "list_tools",
                        "input": {},
                        "ok": False,
                        "duration_ms": int((time.perf_counter() - t0) * 1000),
                        "error": str(e),
                    })
                    return {"issues": [], "debug": debug.__dict__}
            
                # Fetch issues
                items = []
                if "search_issues" in debug.tools:
                    print(f"[MCP-GitHub] Calling search_issues with query: repo:{owner}/{repo} is:issue is:open")
                    result = await client.call_tool("search_issues", {
                        "query": f"repo:{owner}/{repo} is:issue is:open",
                        "page": 1,
                        "per_page": limit_issues
                    })
                    result = self._jsonify_tool_result(result)
                    print(f"[MCP-GitHub] search_issues result: {len(result.get('items', [])) if isinstance(result, dict) else len(result)} items")
                    if isinstance(result, dict) and "items" in result:
                        items = result["items"][:limit_issues]
                    elif isinstance(result, list):
                        items = result[:limit_issues]
                elif "list_issues" in debug.tools:
                    print(f"[MCP-GitHub] Calling list_issues for {owner}/{repo}")
                    result = await client.call_tool("list_issues", {
                        "owner": owner,
                        "repo": repo,
                        "state": "open",
                        "page": 1,
                        "per_page": limit_issues
                    })
                    result = self._jsonify_tool_result(result)
                    if isinstance(result, list):
                        items = result[:limit_issues]
                
                debug.flow.append({"found_open_issues": len(items)})
                
                # Process issues
                detailed_issues = []
                for item in items:
                    issue = await self._process_issue_with_client(client, item, owner, repo, limit_comments)
                    detailed_issues.append(issue.__dict__)
                
                return {"issues": detailed_issues, "debug": debug.__dict__}
            
        except Exception as e:
            return {"issues": [], "debug": {**debug.__dict__, "error": str(e)}}
    
    async def _process_issue_with_client(self, client, item: Dict[str, Any], owner: str, repo: str, 
                                        limit_comments: int) -> GitHubIssue:
        """Process a single issue and fetch its details using the provided client."""
        issue = GitHubIssue(
            number=item.get("number"),
            title=item.get("title", ""),
            state=item.get("state", ""),
            url=item.get("html_url") or item.get("url", ""),
            updated_at=item.get("updated_at", ""),
            labels=[l.get("name") if isinstance(l, dict) else str(l) 
                   for l in (item.get("labels") or [])]
        )
        
        # Fetch detailed issue info
        if issue.number is not None:
            try:
                detailed = await client.call_tool("get_issue", {
                    "owner": owner,
                    "repo": repo,
                    "issue_number": int(issue.number)
                })
                detailed = self._jsonify_tool_result(detailed)
                if isinstance(detailed, dict):
                    issue.body = (detailed.get("body") or "").strip()
                    issue.title = detailed.get("title") or issue.title
                    issue.url = detailed.get("html_url") or detailed.get("url") or issue.url
                    issue.updated_at = detailed.get("updated_at") or issue.updated_at
                    issue.labels = [l.get("name") if isinstance(l, dict) else str(l) 
                                  for l in (detailed.get("labels") or [])]
            except Exception:
                pass
            
            # Fetch comments
            try:
                comments_result = await client.call_tool("get_issue_comments", {
                    "owner": owner,
                    "repo": repo,
                    "issue_number": int(issue.number),
                    "page": 1,
                    "per_page": limit_comments
                })
                comments_result = self._jsonify_tool_result(comments_result)
                if isinstance(comments_result, list):
                    issue.comments = [
                        {
                            "user": (c.get("user") or {}).get("login", ""),
                            "body": (c.get("body") or "").strip(),
                            "created_at": c.get("created_at", "")
                        }
                        for c in comments_result[:limit_comments]
                    ]
            except Exception:
                pass
        
        return issue
    
    def _process_issue(self, item: Dict[str, Any], owner: str, repo: str, 
                      limit_comments: int) -> GitHubIssue:
        """Process a single issue and fetch its details."""
        issue = GitHubIssue(
            number=item.get("number"),
            title=item.get("title", ""),
            state=item.get("state", ""),
            url=item.get("html_url") or item.get("url", ""),
            updated_at=item.get("updated_at", ""),
            labels=[l.get("name") if isinstance(l, dict) else str(l) 
                   for l in (item.get("labels") or [])]
        )
        
        # Fetch detailed issue info
        if issue.number is not None:
            try:
                detailed = asyncio.create_task(
                    self.call_tool("get_issue", {
                        "owner": owner,
                        "repo": repo,
                        "issue_number": int(issue.number)
                    })
                )
                if isinstance(detailed, dict):
                    issue.body = (detailed.get("body") or "").strip()
                    issue.title = detailed.get("title") or issue.title
                    issue.url = detailed.get("html_url") or detailed.get("url") or issue.url
                    issue.updated_at = detailed.get("updated_at") or issue.updated_at
                    issue.labels = [l.get("name") if isinstance(l, dict) else str(l) 
                                  for l in (detailed.get("labels") or [])]
            except Exception:
                pass
            
            # Fetch comments
            try:
                comments_result = asyncio.create_task(
                    self.call_tool("get_issue_comments", {
                        "owner": owner,
                        "repo": repo,
                        "issue_number": int(issue.number),
                        "page": 1,
                        "per_page": limit_comments
                    })
                )
                if isinstance(comments_result, list):
                    for comment in comments_result[:limit_comments]:
                        issue.comments.append({
                            "user": (comment.get("user") or {}).get("login", ""),
                            "body": (comment.get("body") or "").strip(),
                            "created_at": comment.get("created_at", "")
                        })
            except Exception:
                pass
        
        return issue


class PostgresMCPConnector(BaseMCPConnector):
    """PostgreSQL MCP connector implementation."""
    
    def __init__(self, config: MCPPostgresConfig):
        super().__init__(config.url, config.auth_token)
        self.config = config
    

    
    async def fetch_research_papers(self, limit_rows: int = 8) -> Dict[str, Any]:
        """Fetch research papers from PostgreSQL."""
        debug = DebugInfo(sql=self.config.sample_sql.strip())
        
        if not self.config.enabled or not self.config.url:
            print(f"[MCP-PostgreSQL] Disabled or not configured: enabled={self.config.enabled}, url={self.config.url}")
            return {"rows": [], "debug": {**debug.__dict__, "error": "postgres_mcp_disabled_or_not_configured"}}
        
        print(f"[MCP-PostgreSQL] Connecting to: {self.config.url}")
        print(f"[MCP-PostgreSQL] Executing SQL: {debug.sql}")
        
        try:
            async with self._mcp_connect() as client:
                # List tools
                t0 = time.perf_counter()
                try:
                    print(f"[MCP-PostgreSQL] Listing tools...")
                    tools = await client.list_tools()
                    debug.tools = [getattr(t, "name", None) or t.get("name") for t in tools]
                    print(f"[MCP-PostgreSQL] Available tools: {debug.tools}")
                    debug.calls.append({
                        "tool": "list_tools",
                        "input": {},
                        "ok": True,
                        "duration_ms": int((time.perf_counter() - t0) * 1000),
                        "output_preview": str(debug.tools)[:200],
                    })
                except Exception as e:
                    print(f"[MCP-PostgreSQL] Error listing tools: {e}")
                    debug.calls.append({
                        "tool": "list_tools",
                        "input": {},
                        "ok": False,
                        "duration_ms": int((time.perf_counter() - t0) * 1000),
                        "error": str(e),
                    })
                    return {"rows": [], "debug": debug.__dict__}
                
                if "execute_sql" not in debug.tools:
                    print(f"[MCP-PostgreSQL] execute_sql tool not available")
                    return {"rows": [], "debug": {**debug.__dict__, "error": "execute_sql not available"}}
                
                # Execute SQL
                try:
                    print(f"[MCP-PostgreSQL] Executing SQL query...")
                    result = await client.call_tool("execute_sql", {"sql": debug.sql})
                    result = self._jsonify_tool_result(result)
                    print(f"[MCP-PostgreSQL] SQL result: {len(result) if isinstance(result, list) else 'dict'} rows")
                    rows = self._process_sql_result(result, limit_rows)
                    return {"rows": rows, "debug": debug.__dict__}
                except Exception as e:
                    print(f"[MCP-PostgreSQL] Error executing SQL: {e}")
                    return {"rows": [], "debug": {**debug.__dict__, "error": str(e)}}
                    
        except Exception as e:
            print(f"[MCP-PostgreSQL] Connection error: {e}")
            return {"rows": [], "debug": {**debug.__dict__, "error": str(e)}}
    
    def _process_sql_result(self, result: Any, limit_rows: int) -> List[Dict[str, Any]]:
        """Process SQL result into structured format."""
        rows = []
        
        if isinstance(result, list):
            for row in result[:limit_rows]:
                rows.append(row if isinstance(row, dict) else {"raw": str(row)})
        elif isinstance(result, dict):
            if isinstance(result.get("rows"), list):
                for row in result["rows"][:limit_rows]:
                    rows.append(row if isinstance(row, dict) else {"raw": str(row)})
            elif isinstance(result.get("data"), list):
                for row in result["data"][:limit_rows]:
                    rows.append(row if isinstance(row, dict) else {"raw": str(row)})
            else:
                rows.append(result)
        elif isinstance(result, str) and result.strip():
            # Try to parse as JSON
            inner = self._extract_fenced_json(result)
            if inner:
                parsed = self._try_parse_json(inner)
                if parsed is not None:
                    return self._process_sql_result(parsed, limit_rows)
            
            parsed = self._try_parse_json(result)
            if parsed is not None:
                return self._process_sql_result(parsed, limit_rows)
            
            # Try naive JSON-ization
            naive = result.replace("None", "null").replace("True", "true").replace("False", "false")
            naive = re.sub(r"(?<!\\)\'", '"', naive)
            parsed = self._try_parse_json(naive)
            if parsed is not None:
                return self._process_sql_result(parsed, limit_rows)
            
            rows.append({"raw": result[:10000]})
        
        return rows


class MCPConnectorFactory:
    """Factory for creating MCP connector instances."""
    
    @staticmethod
    def create_github_connector(config: MCPGitHubConfig) -> GitHubMCPConnector:
        """Create a GitHub MCP connector."""
        return GitHubMCPConnector(config)
    
    @staticmethod
    def create_postgres_connector(config: MCPPostgresConfig) -> PostgresMCPConnector:
        """Create a PostgreSQL MCP connector."""
        return PostgresMCPConnector(config)
