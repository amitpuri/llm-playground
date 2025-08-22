"""
Atlassian MCP Client - Consolidated Client for Jira and Confluence Operations

This module provides a unified interface for interacting with Atlassian services
(Jira and Confluence) through the Model Context Protocol (MCP).
"""

import os
import asyncio
import json
import sys
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv
from fastmcp import Client


class AtlassianMCPClient:
    """Unified client for Atlassian MCP operations."""
    
    def __init__(self, mcp_url: Optional[str] = None):
        """Initialize the Atlassian MCP client.
        
        Args:
            mcp_url: MCP server URL. If None, loads from environment.
        """
        load_dotenv()
        self.mcp_url = mcp_url or os.getenv("ATLASSIAN_MCP_URL", "http://localhost:8081/mcp")
        self.client = None
        
    def _to_json_value(self, payload: Any) -> Any:
        """Convert MCP responses into Python JSON structures."""
        data = getattr(payload, "content", payload)
        if isinstance(data, dict) and "content" in data:
            data = data["content"]

        # Handle list of TextContent
        if isinstance(data, list) and data and hasattr(data[0], "text"):
            try:
                return json.loads(data[0].text)
            except Exception:
                try:
                    combined = "".join(tc.text for tc in data if hasattr(tc, "text"))
                    return json.loads(combined)
                except Exception:
                    return [tc.text for tc in data if hasattr(tc, "text")]

        # Handle single TextContent
        if hasattr(data, "text"):
            try:
                return json.loads(data.text)
            except Exception:
                return data.text

        # Already dict/list or None/str
        return data
    
    def _format_json(self, obj: Any) -> str:
        """Format object as JSON string."""
        try:
            return json.dumps(obj, indent=2, ensure_ascii=False)
        except:
            return str(obj)
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.client = Client(self.mcp_url)
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def list_available_tools(self) -> Dict[str, List[str]]:
        """List all available tools categorized by service."""
        tools_list = await self.client.list_tools()
        names = [tool.name for tool in tools_list]
        
        categorized = {
            "jira": [name for name in names if name.startswith("jira_")],
            "confluence": [name for name in names if name.startswith("confluence_")],
            "other": [name for name in names if not name.startswith(("jira_", "confluence_"))]
        }
        
        return categorized
    
    async def test_tool(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, Any]:
        """Test a specific tool with given parameters.
        
        Returns:
            Tuple of (success: bool, result: Any)
        """
        try:
            result = await self.client.call_tool(tool_name, params)
            data = self._to_json_value(result)
            return True, data
        except Exception as e:
            return False, str(e)
    
    # Jira Operations
    async def get_jira_projects(self) -> List[Dict[str, Any]]:
        """Get all Jira projects."""
        success, result = await self.test_tool("jira_get_all_projects", {})
        return result if success and isinstance(result, list) else []
    
    async def get_jira_boards(self) -> List[Dict[str, Any]]:
        """Get all Jira agile boards."""
        success, result = await self.test_tool("jira_get_agile_boards", {})
        return result if success and isinstance(result, list) else []
    
    async def get_jira_search_fields(self) -> List[Dict[str, Any]]:
        """Get Jira search fields."""
        success, result = await self.test_tool("jira_search_fields", {})
        return result if success and isinstance(result, list) else []
    
    async def search_jira_issues(self, jql: str, max_results: int = 50) -> Dict[str, Any]:
        """Search Jira issues using JQL.
        
        Note: Based on MCP server logs, maxResults parameter is not supported.
        """
        # Only use jql parameter - maxResults causes validation errors
        params = {"jql": jql}
        
        success, result = await self.test_tool("jira_search", params)
        return result if success else {"issues": [], "total": 0}
    
    async def get_jira_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get a specific Jira issue by key."""
        success, result = await self.test_tool("jira_get_issue", {"issueKey": issue_key})
        return result if success else None
    
    async def get_jira_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get current user profile."""
        success, result = await self.test_tool("jira_get_user_profile", {})
        return result if success else None
    
    # Confluence Operations
    async def get_confluence_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific Confluence page by ID."""
        success, result = await self.test_tool("confluence_get_page", {"pageId": page_id})
        return result if success else None
    
    async def search_confluence_pages(self, query: str, space_key: Optional[str] = None) -> Dict[str, Any]:
        """Search Confluence pages."""
        params = {"query": query}
        if space_key:
            params["spaceKey"] = space_key
        
        success, result = await self.test_tool("confluence_search", params)
        return result if success else {"results": [], "totalSize": 0}
    
    async def get_confluence_page_children(self, page_id: str) -> List[Dict[str, Any]]:
        """Get child pages of a Confluence page.
        
        Note: Based on MCP server logs, parameter should be 'parent_id' not 'pageId'.
        """
        # Use parent_id instead of pageId based on error logs
        success, result = await self.test_tool("confluence_get_page_children", {"parent_id": page_id})
        return result if success and isinstance(result, list) else []
    
    # Diagnostic Operations
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive diagnostics on the Atlassian instance."""
        diagnostics = {
            "connection": {"status": "unknown", "mcp_url": self.mcp_url},
            "tools": {"available": 0, "jira": 0, "confluence": 0},
            "jira": {"projects": 0, "boards": 0, "search_fields": 0, "user_profile": None},
            "confluence": {"pages": 0, "search_working": False},
            "issues": []
        }
        
        try:
            # Test connection and list tools
            categorized_tools = await self.list_available_tools()
            diagnostics["tools"]["available"] = sum(len(tools) for tools in categorized_tools.values())
            diagnostics["tools"]["jira"] = len(categorized_tools["jira"])
            diagnostics["tools"]["confluence"] = len(categorized_tools["confluence"])
            diagnostics["connection"]["status"] = "connected"
            
            # Test Jira operations
            projects = await self.get_jira_projects()
            diagnostics["jira"]["projects"] = len(projects)
            
            boards = await self.get_jira_boards()
            diagnostics["jira"]["boards"] = len(boards)
            
            search_fields = await self.get_jira_search_fields()
            diagnostics["jira"]["search_fields"] = len(search_fields)
            
            user_profile = await self.get_jira_user_profile()
            diagnostics["jira"]["user_profile"] = user_profile is not None
            
            # Test basic Jira search (without maxResults)
            search_result = await self.search_jira_issues("ORDER BY created DESC")
            diagnostics["issues"] = search_result.get("issues", [])
            
            # Test Confluence operations
            confluence_search = await self.search_confluence_pages("")
            diagnostics["confluence"]["pages"] = confluence_search.get("totalSize", 0)
            diagnostics["confluence"]["search_working"] = confluence_search.get("totalSize", -1) >= 0
            
        except Exception as e:
            diagnostics["connection"]["status"] = f"error: {str(e)}"
        
        return diagnostics
    
    # Utility Operations
    async def read_specific_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Read a specific Jira issue with detailed formatting."""
        issue = await self.get_jira_issue(issue_key)
        if not issue:
            return None
        
        # Format the issue data
        formatted = {
            "key": issue.get("key"),
            "id": issue.get("id"),
            "fields": {
                "summary": issue.get("fields", {}).get("summary"),
                "description": issue.get("fields", {}).get("description"),
                "status": issue.get("fields", {}).get("status", {}).get("name"),
                "priority": issue.get("fields", {}).get("priority", {}).get("name"),
                "assignee": issue.get("fields", {}).get("assignee", {}).get("displayName"),
                "reporter": issue.get("fields", {}).get("reporter", {}).get("displayName"),
                "created": issue.get("fields", {}).get("created"),
                "updated": issue.get("fields", {}).get("updated"),
            },
            "comments": []
        }
        
        # Extract comments
        comments = issue.get("fields", {}).get("comment", {})
        if isinstance(comments, dict):
            comment_list = comments.get("comments", [])
            formatted["comments"] = [
                {
                    "author": comment.get("author", {}).get("displayName"),
                    "created": comment.get("created"),
                    "body": comment.get("body")
                }
                for comment in comment_list
            ]
        
        return formatted
    
    async def read_specific_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Read a specific Confluence page with detailed formatting."""
        page = await self.get_confluence_page(page_id)
        if not page:
            return None
        
        # Format the page data
        formatted = {
            "id": page.get("id"),
            "title": page.get("title"),
            "space_key": page.get("space", {}).get("key"),
            "status": page.get("status"),
            "version": page.get("version", {}).get("number"),
            "created": page.get("created"),
            "updated": page.get("updated"),
            "content": None
        }
        
        # Extract content
        body = page.get("body", {})
        if isinstance(body, dict):
            storage = body.get("storage", {})
            if isinstance(storage, dict):
                formatted["content"] = storage.get("value")
        
        return formatted
    
    def save_to_file(self, data: Any, filename: str) -> str:
        """Save data to a JSON file."""
        timestamp = int(asyncio.get_event_loop().time())
        full_filename = f"{filename}_{timestamp}.json"
        
        with open(full_filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return full_filename


# Convenience functions for common operations
async def diagnose_atlassian_instance(mcp_url: Optional[str] = None) -> Dict[str, Any]:
    """Run diagnostics on the Atlassian instance."""
    async with AtlassianMCPClient(mcp_url) as client:
        return await client.run_diagnostics()

async def read_jira_issue(issue_key: str, mcp_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read a specific Jira issue."""
    async with AtlassianMCPClient(mcp_url) as client:
        return await client.read_specific_issue(issue_key)

async def read_confluence_page(page_id: str, mcp_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read a specific Confluence page."""
    async with AtlassianMCPClient(mcp_url) as client:
        return await client.read_specific_page(page_id)

async def search_jira_issues(jql: str, max_results: int = 50, mcp_url: Optional[str] = None) -> Dict[str, Any]:
    """Search Jira issues."""
    async with AtlassianMCPClient(mcp_url) as client:
        return await client.search_jira_issues(jql, max_results)

async def search_confluence_pages(query: str, space_key: Optional[str] = None, mcp_url: Optional[str] = None) -> Dict[str, Any]:
    """Search Confluence pages."""
    async with AtlassianMCPClient(mcp_url) as client:
        return await client.search_confluence_pages(query, space_key)
