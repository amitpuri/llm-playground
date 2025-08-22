#!/usr/bin/env python3
"""
Detailed Debug Script for Atlassian MCP Client

This script provides detailed debugging information to identify why
data operations are not working despite tools being available.
"""

import asyncio
import json
import sys
from atlassian_client import AtlassianMCPClient


async def debug_detailed():
    """Run detailed debugging to identify issues."""
    print("🔍 Detailed Atlassian MCP Debug")
    print("=" * 60)
    
    async with AtlassianMCPClient() as client:
        print(f"✅ Connected to: {client.mcp_url}")
        
        # Test 1: List all tools with details
        print("\n📋 Test 1: Tool Discovery")
        print("-" * 40)
        tools = await client.list_available_tools()
        
        print(f"Jira tools ({len(tools['jira'])}):")
        for tool in sorted(tools['jira']):
            print(f"  - {tool}")
        
        print(f"\nConfluence tools ({len(tools['confluence'])}):")
        for tool in sorted(tools['confluence']):
            print(f"  - {tool}")
        
        # Test 2: Test each Jira tool individually
        print("\n📋 Test 2: Individual Jira Tool Testing")
        print("-" * 40)
        
        jira_tests = [
            ("jira_get_all_projects", {}, "Get all projects"),
            ("jira_get_agile_boards", {}, "Get agile boards"),
            ("jira_get_user_profile", {}, "Get user profile"),
            ("jira_search_fields", {}, "Get search fields"),
            ("jira_get_link_types", {}, "Get link types"),
            ("jira_search", {"jql": "ORDER BY created DESC"}, "Basic search"),
            ("jira_search", {"jql": "project = polaris"}, "Project search"),
            ("jira_search", {"jql": ""}, "Empty search"),
        ]
        
        for tool_name, params, description in jira_tests:
            print(f"\n🔧 Testing: {description}")
            print(f"   Tool: {tool_name}")
            print(f"   Params: {params}")
            
            success, result = await client.test_tool(tool_name, params)
            if success:
                if isinstance(result, list):
                    print(f"   ✅ SUCCESS: List with {len(result)} items")
                    if result:
                        print(f"   📄 Sample: {result[0]}")
                elif isinstance(result, dict):
                    print(f"   ✅ SUCCESS: Dict with keys: {list(result.keys())}")
                    if 'issues' in result:
                        print(f"   📄 Issues: {len(result.get('issues', []))}")
                    if 'total' in result:
                        print(f"   📄 Total: {result.get('total')}")
                else:
                    print(f"   ✅ SUCCESS: {type(result)} - {str(result)[:100]}")
            else:
                print(f"   ❌ FAILED: {result}")
        
        # Test 3: Test Confluence tools
        print("\n📄 Test 3: Individual Confluence Tool Testing")
        print("-" * 40)
        
        confluence_tests = [
            ("confluence_search", {"query": ""}, "Empty search"),
            ("confluence_search", {"query": "test"}, "Basic search"),
            ("confluence_search", {"cql": ""}, "Empty CQL"),
            ("confluence_search", {"cql": "space = SD"}, "Space search"),
            ("confluence_get_page", {"pageId": "2588673"}, "Get specific page"),
        ]
        
        for tool_name, params, description in confluence_tests:
            print(f"\n🔧 Testing: {description}")
            print(f"   Tool: {tool_name}")
            print(f"   Params: {params}")
            
            success, result = await client.test_tool(tool_name, params)
            if success:
                if isinstance(result, list):
                    print(f"   ✅ SUCCESS: List with {len(result)} items")
                elif isinstance(result, dict):
                    print(f"   ✅ SUCCESS: Dict with keys: {list(result.keys())}")
                    if 'results' in result:
                        print(f"   📄 Results: {len(result.get('results', []))}")
                    if 'totalSize' in result:
                        print(f"   📄 Total: {result.get('totalSize')}")
                else:
                    print(f"   ✅ SUCCESS: {type(result)} - {str(result)[:100]}")
            else:
                print(f"   ❌ FAILED: {result}")
        
        # Test 4: Test with different parameter combinations
        print("\n🔧 Test 4: Parameter Variation Testing")
        print("-" * 40)
        
        # Test Jira search with different parameter combinations
        jira_search_variations = [
            {"jql": "ORDER BY created DESC"},
            {"jql": "ORDER BY created DESC", "maxResults": 5},
            {"jql": "ORDER BY created DESC", "startAt": 0},
            {"jql": "ORDER BY created DESC", "fields": "summary,status"},
            {"jql": "project = polaris"},
            {"jql": "created >= -30d"},
            {"jql": "status != Done"},
            {"jql": "assignee = currentUser()"},
        ]
        
        for i, params in enumerate(jira_search_variations, 1):
            print(f"\n🔧 Jira Search Variation {i}: {params}")
            success, result = await client.test_tool("jira_search", params)
            if success:
                if isinstance(result, dict):
                    issues = result.get('issues', [])
                    total = result.get('total', 0)
                    print(f"   ✅ SUCCESS: {total} total, {len(issues)} returned")
                else:
                    print(f"   ✅ SUCCESS: {type(result)}")
            else:
                print(f"   ❌ FAILED: {result}")
        
        # Test 5: Check if there are any working tools that return data
        print("\n🔍 Test 5: Finding Working Data Sources")
        print("-" * 40)
        
        # Test tools that might work even with empty data
        working_tests = [
            ("jira_get_all_projects", {}, "Projects"),
            ("jira_get_agile_boards", {}, "Boards"),
            ("jira_search_fields", {}, "Search Fields"),
            ("jira_get_link_types", {}, "Link Types"),
        ]
        
        working_data = {}
        for tool_name, params, description in working_tests:
            success, result = await client.test_tool(tool_name, params)
            if success and result:
                working_data[description] = result
                print(f"✅ {description}: {len(result) if isinstance(result, list) else 'data'}")
            else:
                print(f"❌ {description}: No data")
        
        # Test 6: Try to create a test issue to see if write operations work
        print("\n🔧 Test 6: Testing Write Operations")
        print("-" * 40)
        
        # Test if we can create a simple issue (this might fail due to permissions)
        test_issue_data = {
            "project": {"key": "polaris"},
            "summary": "Test Issue from MCP Client",
            "description": "This is a test issue created by the MCP client for debugging",
            "issuetype": {"name": "Task"}
        }
        
        print("🔧 Testing issue creation...")
        success, result = await client.test_tool("jira_create_issue", {"fields": test_issue_data})
        if success:
            print(f"   ✅ SUCCESS: Issue created - {result}")
        else:
            print(f"   ❌ FAILED: {result}")
            print("   (This is expected if you don't have create permissions)")
        
        # Summary
        print("\n📊 Debug Summary")
        print("=" * 60)
        print(f"✅ MCP Connection: Working")
        print(f"✅ Tool Discovery: {len(tools['jira']) + len(tools['confluence'])} tools available")
        print(f"📋 Working Data Sources: {len(working_data)}")
        
        if working_data:
            print("\n📄 Available Data:")
            for source, data in working_data.items():
                if isinstance(data, list):
                    print(f"   {source}: {len(data)} items")
                else:
                    print(f"   {source}: {type(data)}")
        
        print("\n💡 Recommendations:")
        if not working_data:
            print("   - The Atlassian instance appears to be empty")
            print("   - Check if you have the correct permissions")
            print("   - Verify the API token has sufficient scope")
        else:
            print("   - Some tools are working, but search operations may be failing")
            print("   - Check if there are any issues in the Atlassian instance")
            print("   - Verify the project keys and space keys are correct")


if __name__ == "__main__":
    asyncio.run(debug_detailed())
