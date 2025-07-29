#!/bin/bash

# Start the Jira HTTP Server
echo "Starting Jira HTTP Server..."

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

# Start the HTTP server
echo "Starting HTTP server on http://localhost:8090..."
python http_jira_server.py