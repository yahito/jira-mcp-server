#!/usr/bin/env python3
import asyncio
import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from jira_config import JiraConfig
from jira_service import JiraService


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-mcp-server")

# Initialize Jira service
config = JiraConfig()
jira_service = JiraService(config)

# Create MCP server
server = Server("jira-mcp-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available Jira tools."""
    return [
        Tool(
            name="get_ticket",
            description="Retrieves details of a specific Jira ticket by its key",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_key": {
                        "type": "string",
                        "description": "The Jira ticket key (e.g., PROJECT-123)"
                    }
                },
                "required": ["ticket_key"]
            }
        ),
        Tool(
            name="search_tickets",
            description="Searches for Jira tickets matching the given JQL query",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql_query": {
                        "type": "string",
                        "description": "JQL query to search for tickets"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50
                    }
                },
                "required": ["jql_query"]
            }
        ),
        Tool(
            name="search_tickets_by_text",
            description="Searches for Jira tickets containing specific text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to search for in tickets"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="get_tickets_by_project",
            description="Gets all tickets for a specific Jira project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {
                        "type": "string",
                        "description": "The project key (e.g., PROJ)"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50
                    }
                },
                "required": ["project_key"]
            }
        ),
        Tool(
            name="get_my_assigned_tickets",
            description="Gets all Jira tickets assigned to the current user",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_recently_updated_tickets",
            description="Gets recently updated Jira tickets from the last 7 days",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "get_ticket":
            ticket_key = arguments.get("ticket_key")
            if not ticket_key:
                raise ValueError("ticket_key is required")
            
            ticket = jira_service.get_ticket(ticket_key)
            result = {
                "key": ticket.key,
                "id": ticket.id,
                "summary": ticket.fields.summary if ticket.fields else None,
                "description": ticket.fields.description if ticket.fields else None,
                "status": ticket.fields.status.name if ticket.fields and ticket.fields.status else None,
                "priority": ticket.fields.priority.name if ticket.fields and ticket.fields.priority else None,
                "assignee": ticket.fields.assignee.display_name if ticket.fields and ticket.fields.assignee else None,
                "reporter": ticket.fields.reporter.display_name if ticket.fields and ticket.fields.reporter else None,
                "created": ticket.fields.created if ticket.fields else None,
                "updated": ticket.fields.updated if ticket.fields else None
            }
            
        elif name == "search_tickets":
            jql_query = arguments.get("jql_query")
            max_results = arguments.get("max_results")
            
            tickets = jira_service.search_tickets(jql_query, max_results)
            result = []
            for ticket in tickets:
                result.append({
                    "key": ticket.key,
                    "id": ticket.id,
                    "summary": ticket.fields.summary if ticket.fields else None,
                    "status": ticket.fields.status.name if ticket.fields and ticket.fields.status else None,
                    "assignee": ticket.fields.assignee.display_name if ticket.fields and ticket.fields.assignee else None,
                    "updated": ticket.fields.updated if ticket.fields else None
                })
                
        elif name == "search_tickets_by_text":
            text = arguments.get("text")
            max_results = arguments.get("max_results")
            
            tickets = jira_service.search_tickets_by_text(text, max_results)
            result = []
            for ticket in tickets:
                result.append({
                    "key": ticket.key,
                    "id": ticket.id,
                    "summary": ticket.fields.summary if ticket.fields else None,
                    "status": ticket.fields.status.name if ticket.fields and ticket.fields.status else None,
                    "assignee": ticket.fields.assignee.display_name if ticket.fields and ticket.fields.assignee else None,
                    "updated": ticket.fields.updated if ticket.fields else None
                })
                
        elif name == "get_tickets_by_project":
            project_key = arguments.get("project_key")
            max_results = arguments.get("max_results")
            
            tickets = jira_service.get_tickets_by_project(project_key, max_results)
            result = []
            for ticket in tickets:
                result.append({
                    "key": ticket.key,
                    "id": ticket.id,
                    "summary": ticket.fields.summary if ticket.fields else None,
                    "status": ticket.fields.status.name if ticket.fields and ticket.fields.status else None,
                    "assignee": ticket.fields.assignee.display_name if ticket.fields and ticket.fields.assignee else None,
                    "updated": ticket.fields.updated if ticket.fields else None
                })
                
        elif name == "get_my_assigned_tickets":
            max_results = arguments.get("max_results")
            
            tickets = jira_service.get_my_assigned_tickets(max_results)
            result = []
            for ticket in tickets:
                result.append({
                    "key": ticket.key,
                    "id": ticket.id,
                    "summary": ticket.fields.summary if ticket.fields else None,
                    "status": ticket.fields.status.name if ticket.fields and ticket.fields.status else None,
                    "assignee": ticket.fields.assignee.display_name if ticket.fields and ticket.fields.assignee else None,
                    "updated": ticket.fields.updated if ticket.fields else None
                })
                
        elif name == "get_recently_updated_tickets":
            max_results = arguments.get("max_results")
            
            tickets = jira_service.get_recently_updated_tickets(max_results)
            result = []
            for ticket in tickets:
                result.append({
                    "key": ticket.key,
                    "id": ticket.id,
                    "summary": ticket.fields.summary if ticket.fields else None,
                    "status": ticket.fields.status.name if ticket.fields and ticket.fields.status else None,
                    "assignee": ticket.fields.assignee.display_name if ticket.fields and ticket.fields.assignee else None,
                    "updated": ticket.fields.updated if ticket.fields else None
                })
                
        else:
            raise ValueError(f"Unknown tool: {name}")
            
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
        
    except Exception as e:
        logger.error(f"Error in {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Jira MCP Server")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jira-mcp-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())