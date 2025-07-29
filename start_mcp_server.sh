#!/bin/bash

# Start the Jira MCP Server
echo "Starting Jira MCP Server..."

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the MCP server
echo "Starting MCP server..."
python mcp_jira_server.py