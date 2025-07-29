# Jira MCP Python Server

A Python-based MCP (Model Context Protocol) server that provides Jira integration tools.

## Features

- **Get ticket details** by key
- **Search tickets** with JQL queries
- **Search by text** content
- **Get tickets by project**
- **Get assigned tickets** for current user
- **Get recently updated** tickets (last 7 days)
- **Change ticket status** (In Progress, Done, etc.)
- **Get available transitions** for tickets

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Configuration

Update `jira_config.py` with your Jira credentials:
- `base_url`: Your Jira instance URL
- `username`: Your Jira username/email
- `api_token`: Your Jira API token

## Usage

### HTTP Server (Recommended)
```bash
./start_http_server.sh
```
Server runs on http://localhost:8090

### Pure MCP Server (stdio)
```bash
./start_mcp_server.sh
```

## MCP Configuration

For Windsurf/Claude Desktop, use:

```json
{
  "mcpServers": {
    "jira-python-server": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-http-proxy", "http://localhost:8090"]
    }
  }
}
```

## Available Tools

1. **get_ticket** - Get specific ticket by key
2. **search_tickets** - Search with JQL queries
3. **search_tickets_by_text** - Text-based search
4. **get_tickets_by_project** - Project-specific tickets
5. **get_my_assigned_tickets** - Current user's tickets
6. **get_recently_updated_tickets** - Recent updates
7. **get_ticket_transitions** - Available status transitions
8. **change_ticket_status** - Change ticket status

## REST API Endpoints

- `GET /api/jira/tickets/recent?limit=10`
- `GET /api/jira/tickets/assigned?limit=10`
- `GET /api/jira/tickets/project/{project_key}?limit=10`
- `GET /api/jira/tickets/search?jql=query&limit=10`
- `GET /api/jira/ticket/{ticket_key}`
- `GET /api/jira/ticket/{ticket_key}/transitions`
- `POST /api/jira/ticket/{ticket_key}/status`# jira-mcp-server
