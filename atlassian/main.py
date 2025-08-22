#!/usr/bin/env python3
"""
Atlassian MCP Client - Main Script

This script provides a command-line interface for interacting with Atlassian services
(Jira and Confluence) through the Model Context Protocol (MCP).

Usage:
    python main.py diagnose                    # Run diagnostics
    python main.py read-issue MDP-6           # Read specific Jira issue
    python main.py read-page 2588673          # Read specific Confluence page
    python main.py search-jira "project = polaris" # Search Jira issues
    python main.py search-confluence "test"   # Search Confluence pages
    python main.py list-tools                 # List available tools
"""

import asyncio
import json
import sys
from typing import Optional
from atlassian_client import (
    AtlassianMCPClient, 
    diagnose_atlassian_instance,
    read_jira_issue,
    read_confluence_page,
    search_jira_issues,
    search_confluence_pages
)


def print_json(data: dict, indent: int = 2) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def print_issue_details(issue: dict) -> None:
    """Print formatted Jira issue details."""
    if not issue:
        print("❌ Issue not found or not accessible")
        return
    
    print(f"\n📋 Issue: {issue['key']}")
    print(f"🆔 ID: {issue['id']}")
    print(f"📝 Summary: {issue['fields']['summary']}")
    print(f"📊 Status: {issue['fields']['status']}")
    print(f"⚡ Priority: {issue['fields']['priority']}")
    print(f"👤 Assignee: {issue['fields']['assignee']}")
    print(f"📅 Created: {issue['fields']['created']}")
    print(f"🔄 Updated: {issue['fields']['updated']}")
    
    if issue['fields']['description']:
        print(f"\n📄 Description:")
        print(issue['fields']['description'][:500] + "..." if len(issue['fields']['description']) > 500 else issue['fields']['description'])
    
    if issue['comments']:
        print(f"\n💬 Comments ({len(issue['comments'])}):")
        for i, comment in enumerate(issue['comments'], 1):
            print(f"  {i}. {comment['author']} ({comment['created']}):")
            print(f"     {comment['body'][:200] + '...' if len(comment['body']) > 200 else comment['body']}")


def print_page_details(page: dict) -> None:
    """Print formatted Confluence page details."""
    if not page:
        print("❌ Page not found or not accessible")
        return
    
    print(f"\n📄 Page: {page['title']}")
    print(f"🆔 ID: {page['id']}")
    print(f"🏢 Space: {page['space_key']}")
    print(f"📊 Status: {page['status']}")
    print(f"📈 Version: {page['version']}")
    print(f"📅 Created: {page['created']}")
    print(f"🔄 Updated: {page['updated']}")
    
    if page['content']:
        print(f"\n📝 Content:")
        print(page['content'][:1000] + "..." if len(page['content']) > 1000 else page['content'])


def print_diagnostics(diagnostics: dict) -> None:
    """Print formatted diagnostics results."""
    print("\n🔍 Atlassian Instance Diagnostics")
    print("=" * 50)
    
    # Connection status
    status = diagnostics['connection']['status']
    if status == 'connected':
        print("✅ Connection: Connected to MCP server")
    else:
        print(f"❌ Connection: {status}")
    
    print(f"🌐 MCP URL: {diagnostics['connection']['mcp_url']}")
    
    # Tools summary
    tools = diagnostics['tools']
    print(f"\n🛠️  Available Tools:")
    print(f"   Total: {tools['available']}")
    print(f"   Jira: {tools['jira']}")
    print(f"   Confluence: {tools['confluence']}")
    
    # Jira status
    jira = diagnostics['jira']
    print(f"\n📋 Jira Status:")
    print(f"   Projects: {jira['projects']}")
    print(f"   Boards: {jira['boards']}")
    print(f"   Search Fields: {jira['search_fields']}")
    print(f"   User Profile: {'✅' if jira['user_profile'] else '❌'}")
    
    # Confluence status
    confluence = diagnostics['confluence']
    print(f"\n📄 Confluence Status:")
    print(f"   Pages: {confluence['pages']}")
    print(f"   Search Working: {'✅' if confluence['search_working'] else '❌'}")
    
    # Recent issues
    issues = diagnostics['issues']
    if issues:
        print(f"\n📝 Recent Issues ({len(issues)}):")
        for issue in issues[:5]:  # Show first 5
            key = issue.get('key', 'N/A')
            summary = issue.get('fields', {}).get('summary', 'N/A')
            status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
            print(f"   {key}: {summary} [{status}]")
    else:
        print(f"\n📝 Recent Issues: None found")


async def main():
    """Main function handling command-line arguments."""
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == "diagnose":
            print("🔍 Running diagnostics...")
            diagnostics = await diagnose_atlassian_instance()
            print_diagnostics(diagnostics)
            
            # Save diagnostics to file
            async with AtlassianMCPClient() as client:
                filename = client.save_to_file(diagnostics, "diagnostics")
                print(f"\n💾 Diagnostics saved to: {filename}")
        
        elif command == "read-issue":
            if len(sys.argv) < 3:
                print("❌ Usage: python main_new.py read-issue <issue-key>")
                return
            
            issue_key = sys.argv[2]
            print(f"📋 Reading issue: {issue_key}")
            issue = await read_jira_issue(issue_key)
            print_issue_details(issue)
            
            if issue:
                async with AtlassianMCPClient() as client:
                    filename = client.save_to_file(issue, f"issue_{issue_key}")
                    print(f"\n💾 Issue data saved to: {filename}")
        
        elif command == "read-page":
            if len(sys.argv) < 3:
                print("❌ Usage: python main_new.py read-page <page-id>")
                return
            
            page_id = sys.argv[2]
            print(f"📄 Reading page: {page_id}")
            page = await read_confluence_page(page_id)
            print_page_details(page)
            
            if page:
                async with AtlassianMCPClient() as client:
                    filename = client.save_to_file(page, f"page_{page_id}")
                    print(f"\n💾 Page data saved to: {filename}")
        
        elif command == "search-jira":
            if len(sys.argv) < 3:
                print("❌ Usage: python main.py search-jira <jql-query>")
                return
            
            jql = sys.argv[2]
            print(f"🔍 Searching Jira: {jql}")
            
            result = await search_jira_issues(jql)
            issues = result.get('issues', [])
            total = result.get('total', 0)
            
            print(f"\n📋 Found {total} issues (showing {len(issues)}):")
            for issue in issues:
                key = issue.get('key', 'N/A')
                summary = issue.get('fields', {}).get('summary', 'N/A')
                status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
                print(f"  {key}: {summary} [{status}]")
            
            if issues:
                async with AtlassianMCPClient() as client:
                    filename = client.save_to_file(result, f"jira_search_{jql.replace(' ', '_')}")
                    print(f"\n💾 Search results saved to: {filename}")
        
        elif command == "search-confluence":
            if len(sys.argv) < 3:
                print("❌ Usage: python main_new.py search-confluence <query>")
                return
            
            query = sys.argv[2]
            space_key = sys.argv[3] if len(sys.argv) > 3 else None
            print(f"🔍 Searching Confluence: {query}")
            if space_key:
                print(f"   Space: {space_key}")
            
            result = await search_confluence_pages(query, space_key)
            pages = result.get('results', [])
            total = result.get('totalSize', 0)
            
            print(f"\n📄 Found {total} pages (showing {len(pages)}):")
            for page in pages:
                page_id = page.get('id', 'N/A')
                title = page.get('title', 'N/A')
                space = page.get('space', {}).get('key', 'N/A')
                print(f"  {page_id}: {title} [{space}]")
            
            if pages:
                async with AtlassianMCPClient() as client:
                    filename = client.save_to_file(result, f"confluence_search_{query.replace(' ', '_')}")
                    print(f"\n💾 Search results saved to: {filename}")
        
        elif command == "list-tools":
            print("🛠️  Listing available tools...")
            async with AtlassianMCPClient() as client:
                tools = await client.list_available_tools()
                
                print(f"\n📋 Jira Tools ({len(tools['jira'])}):")
                for tool in sorted(tools['jira']):
                    print(f"  - {tool}")
                
                print(f"\n📄 Confluence Tools ({len(tools['confluence'])}):")
                for tool in sorted(tools['confluence']):
                    print(f"  - {tool}")
                
                if tools['other']:
                    print(f"\n🔧 Other Tools ({len(tools['other'])}):")
                    for tool in sorted(tools['other']):
                        print(f"  - {tool}")
        
        else:
            print(f"❌ Unknown command: {command}")
            print(__doc__)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
