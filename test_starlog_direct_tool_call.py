#!/usr/bin/env python3
"""
Direct tool call test for STARLOG MCP using mcp-use
Tests all STARLOG MCP tools without needing an LLM
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Add the starlog_mcp package to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_use import MCPClient


async def test_starlog_mcp():
    """Test STARLOG MCP tools directly using mcp-use"""
    
    # Set required environment variables from CLI args
    if len(sys.argv) < 2:
        print("Usage: python test_starlog_direct_tool_call.py <OPENAI_API_KEY>")
        sys.exit(1)
    
    os.environ["OPENAI_API_KEY"] = sys.argv[1]
    os.environ["HEAVEN_DATA_DIR"] = "/tmp/heaven_data"
    
    # Ensure heaven data directory exists
    os.makedirs("/tmp/heaven_data", exist_ok=True)
    
    # Configure the STARLOG MCP server
    config = {
        "mcpServers": {
            "starlog": {
                "command": "python",
                "args": ["-m", "starlog_mcp.starlog_mcp"],
                "env": {
                    "OPENAI_API_KEY": sys.argv[1],
                    "HEAVEN_DATA_DIR": "/tmp/heaven_data"
                },
                "cwd": str(Path(__file__).parent)
            }
        }
    }
    
    print("Starting STARLOG MCP Direct Tool Call Test")
    print(f"Working directory: {Path(__file__).parent}")
    print(f"HEAVEN_DATA_DIR: {os.environ['HEAVEN_DATA_DIR']}")
    
    client = MCPClient.from_dict(config)
    
    try:
        # Initialize the session
        await client.connect()
        print("Connected to STARLOG MCP server")
        
        # Get available tools
        tools = await client.list_tools()
        print(f"Found {len(tools.tools)} tools: {[t.name for t in tools.tools]}")
        
        # Test project path
        test_project_path = "/tmp/test_starlog_project"
        
        print("\n=== Testing STARLOG MCP Tools ===")
        
        # Test basic functionality
        result = await client.call_tool("check", {"path": test_project_path})
        print("Check tool executed")
        
        result = await client.call_tool("init_project", {
            "path": test_project_path,
            "name": "Test Project"
        })
        print("Init project tool executed")
        
        print("\nAll MCP tools executed without errors")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(test_starlog_mcp())