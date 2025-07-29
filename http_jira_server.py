#!/usr/bin/env python3
import json
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import uvicorn

from jira_config import JiraConfig
from jira_service import JiraService


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jira-http-server")

# Initialize Jira service
config = JiraConfig()
jira_service = JiraService(config)

# Create FastAPI app
app = FastAPI(
    title="Jira MCP HTTP Server",
    description="HTTP wrapper for Jira MCP tools",
    version="1.0.0"
)


def format_ticket_summary(ticket):
    """Format ticket for list responses"""
    return {
        "key": ticket.key,
        "id": ticket.id,
        "summary": ticket.fields.summary if ticket.fields else None,
        "status": ticket.fields.status.name if ticket.fields and ticket.fields.status else None,
        "assignee": ticket.fields.assignee.display_name if ticket.fields and ticket.fields.assignee else None,
        "updated": ticket.fields.updated if ticket.fields else None
    }


def format_ticket_detailed(ticket):
    """Format ticket for detailed responses"""
    return {
        "key": ticket.key,
        "id": ticket.id,
        "self": ticket.self,
        "summary": ticket.fields.summary if ticket.fields else None,
        "description": ticket.fields.description if ticket.fields else None,
        "status": ticket.fields.status.name if ticket.fields and ticket.fields.status else None,
        "priority": ticket.fields.priority.name if ticket.fields and ticket.fields.priority else None,
        "issuetype": ticket.fields.issuetype.name if ticket.fields and ticket.fields.issuetype else None,
        "assignee": {
            "displayName": ticket.fields.assignee.display_name,
            "emailAddress": ticket.fields.assignee.email_address
        } if ticket.fields and ticket.fields.assignee else None,
        "reporter": {
            "displayName": ticket.fields.reporter.display_name,
            "emailAddress": ticket.fields.reporter.email_address
        } if ticket.fields and ticket.fields.reporter else None,
        "created": ticket.fields.created if ticket.fields else None,
        "updated": ticket.fields.updated if ticket.fields else None
    }


@app.get("/api/jira/tickets/recent")
async def get_recent_tickets(limit: int = Query(default=10)):
    """Get recently updated tickets from the last 7 days"""
    try:
        logger.info("Getting recent tickets")
        tickets = jira_service.get_recently_updated_tickets(limit)
        result = [format_ticket_summary(ticket) for ticket in tickets]
        logger.info(f"Found {len(result)} tickets")
        return result
    except Exception as e:
        logger.error(f"Error getting recent tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jira/tickets/assigned")
async def get_my_assigned_tickets(limit: int = Query(default=10)):
    """Get tickets assigned to current user"""
    try:
        logger.info("Getting my assigned tickets")
        tickets = jira_service.get_my_assigned_tickets(limit)
        result = [format_ticket_summary(ticket) for ticket in tickets]
        return result
    except Exception as e:
        logger.error(f"Error getting assigned tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jira/tickets/project/{project_key}")
async def get_tickets_by_project(project_key: str, limit: int = Query(default=10)):
    """Get tickets by project key"""
    try:
        logger.info(f"Getting tickets for project: {project_key}")
        tickets = jira_service.get_tickets_by_project(project_key, limit)
        result = [format_ticket_summary(ticket) for ticket in tickets]
        return result
    except Exception as e:
        logger.error(f"Error getting project tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jira/tickets/search")
async def search_tickets(jql: str = Query(), limit: int = Query(default=10)):
    """Search tickets using JQL query"""
    try:
        logger.info(f"Searching for tickets with JQL: {jql}")
        tickets = jira_service.search_tickets(jql, limit)
        result = [format_ticket_summary(ticket) for ticket in tickets]
        return result
    except Exception as e:
        logger.error(f"Error searching tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jira/tickets/search/text")
async def search_tickets_by_text(text: str = Query(), limit: int = Query(default=10)):
    """Search tickets by text content"""
    try:
        logger.info(f"Searching for tickets containing text: {text}")
        tickets = jira_service.search_tickets_by_text(text, limit)
        result = [format_ticket_summary(ticket) for ticket in tickets]
        return result
    except Exception as e:
        logger.error(f"Error searching tickets by text: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jira/ticket/{ticket_key}")
async def get_ticket(ticket_key: str):
    """Get detailed ticket information by key"""
    try:
        logger.info(f"Getting ticket: {ticket_key}")
        ticket = jira_service.get_ticket(ticket_key)
        result = format_ticket_detailed(ticket)
        return result
    except Exception as e:
        logger.error(f"Error getting ticket {ticket_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/jira/ticket/{ticket_key}/transitions")
async def get_ticket_transitions(ticket_key: str):
    """Get available status transitions for a ticket"""
    try:
        logger.info(f"Getting transitions for ticket: {ticket_key}")
        transitions = jira_service.get_available_transitions(ticket_key)
        return {"transitions": transitions}
    except Exception as e:
        logger.error(f"Error getting transitions for {ticket_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jira/ticket/{ticket_key}/status")
async def change_ticket_status(ticket_key: str, request: dict):
    """Change the status of a ticket"""
    try:
        status_name = request.get("status")
        if not status_name:
            raise HTTPException(status_code=400, detail="status is required")
        
        logger.info(f"Changing status of {ticket_key} to {status_name}")
        result = jira_service.change_ticket_status(ticket_key, status_name)
        return result
    except ValueError as e:
        logger.error(f"Validation error changing status of {ticket_key}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error changing status of {ticket_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# MCP Protocol endpoints
@app.post("/")
async def mcp_rpc_endpoint(request: dict):
    """Main MCP JSON-RPC endpoint"""
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": "jira-http-server",
                        "version": "1.0.0"
                    }
                }
            }
            
        elif method == "tools/list":
            tools = [
                {
                    "name": "get_ticket",
                    "description": "Retrieves details of a specific Jira ticket by its key",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "ticket_key": {"type": "string", "description": "The Jira ticket key"}
                        },
                        "required": ["ticket_key"]
                    }
                },
                {
                    "name": "search_tickets",
                    "description": "Searches for Jira tickets matching the given JQL query",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "jql_query": {"type": "string", "description": "JQL query"},
                            "max_results": {"type": "integer", "description": "Max results", "default": 50}
                        },
                        "required": ["jql_query"]
                    }
                },
                {
                    "name": "search_tickets_by_text",
                    "description": "Searches for Jira tickets containing specific text",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Text to search"},
                            "max_results": {"type": "integer", "description": "Max results", "default": 50}
                        },
                        "required": ["text"]
                    }
                },
                {
                    "name": "get_tickets_by_project",
                    "description": "Gets all tickets for a specific Jira project",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "project_key": {"type": "string", "description": "Project key"},
                            "max_results": {"type": "integer", "description": "Max results", "default": 50}
                        },
                        "required": ["project_key"]
                    }
                },
                {
                    "name": "get_my_assigned_tickets",
                    "description": "Gets all Jira tickets assigned to the current user",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "max_results": {"type": "integer", "description": "Max results", "default": 50}
                        }
                    }
                },
                {
                    "name": "get_recently_updated_tickets",
                    "description": "Gets recently updated Jira tickets from the last 7 days",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "max_results": {"type": "integer", "description": "Max results", "default": 50}
                        }
                    }
                },
                {
                    "name": "get_ticket_transitions",
                    "description": "Get available status transitions for a Jira ticket",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "ticket_key": {"type": "string", "description": "The Jira ticket key"}
                        },
                        "required": ["ticket_key"]
                    }
                },
                {
                    "name": "change_ticket_status",
                    "description": "Change the status of a Jira ticket (e.g., 'In Progress', 'Done', 'To Do')",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "ticket_key": {"type": "string", "description": "The Jira ticket key"},
                            "status_name": {"type": "string", "description": "The target status name or transition name"}
                        },
                        "required": ["ticket_key", "status_name"]
                    }
                }
            ]
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools
                }
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "get_ticket":
                ticket = jira_service.get_ticket(arguments.get("ticket_key"))
                result = format_ticket_detailed(ticket)
                
            elif tool_name == "search_tickets":
                tickets = jira_service.search_tickets(
                    arguments.get("jql_query"), 
                    arguments.get("max_results")
                )
                result = [format_ticket_summary(ticket) for ticket in tickets]
                
            elif tool_name == "search_tickets_by_text":
                tickets = jira_service.search_tickets_by_text(
                    arguments.get("text"), 
                    arguments.get("max_results")
                )
                result = [format_ticket_summary(ticket) for ticket in tickets]
                
            elif tool_name == "get_tickets_by_project":
                tickets = jira_service.get_tickets_by_project(
                    arguments.get("project_key"), 
                    arguments.get("max_results")
                )
                result = [format_ticket_summary(ticket) for ticket in tickets]
                
            elif tool_name == "get_my_assigned_tickets":
                tickets = jira_service.get_my_assigned_tickets(arguments.get("max_results"))
                result = [format_ticket_summary(ticket) for ticket in tickets]
                
            elif tool_name == "get_recently_updated_tickets":
                tickets = jira_service.get_recently_updated_tickets(arguments.get("max_results"))
                result = [format_ticket_summary(ticket) for ticket in tickets]
                
            elif tool_name == "get_ticket_transitions":
                ticket_key = arguments.get("ticket_key")
                transitions = jira_service.get_available_transitions(ticket_key)
                result = {"transitions": transitions}
                
            elif tool_name == "change_ticket_status":
                ticket_key = arguments.get("ticket_key")
                status_name = arguments.get("status_name")
                result = jira_service.change_ticket_status(ticket_key, status_name)
                
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
                
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
            
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
            
    except Exception as e:
        logger.error(f"Error in MCP RPC: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "jira-http-server"}


if __name__ == "__main__":
    logger.info("Starting Jira HTTP Server on port 8090")
    uvicorn.run(app, host="0.0.0.0", port=8090)