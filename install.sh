#!/bin/bash

# Configuration
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Function to handle cleanup on exit
cleanup() {
    echo "Stopping servers..."
    # Kill all child processes of this script
    pkill -P $$
    wait
    echo "Servers stopped."
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM EXIT

echo "--- Mattermost Bot Setup & Run ---"

# 1. Check/Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# 2. Activate Virtual Environment
source "$VENV_DIR/bin/activate"

# 3. Install Dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Checking dependencies..."
    pip install -r "$REQUIREMENTS_FILE" > /dev/null
    if [ $? -eq 0 ]; then
         echo "Dependencies installed."
    else
         echo "Error installing dependencies."
         exit 1
    fi
else
    echo "Warning: $REQUIREMENTS_FILE not found."
fi

# 4. Check .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found! Please create one based on Readme.md"
fi

# 5. Start Servers
echo "Starting MCP Server (server.py)..."
python server.py &
MCP_PID=$!

echo "Starting Mattermost Bot (mattermost.py)..."
python mattermost.py &
BOT_PID=$!

echo "Servers are running. Press Ctrl+C to stop."
echo "MCP PID: $MCP_PID"
echo "Bot PID: $BOT_PID"

# Wait for both processes to keep script running
wait $MCP_PID $BOT_PID
