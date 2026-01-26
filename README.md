# 🐳 Docker Deployment: Mattermost Bot

This guide allows you to run the Bot and MCP Server in Docker containers, connecting to your existing external Ollama and PostgreSQL services.

## 1. Setup

### Prerequisites
*   Docker & Docker Compose installed on your server.
*   Your project files cloned to the server.

### Configuration
Ensure your `.env` file is set up in the project root.

**Important for Networking:**
Since Docker runs in an isolated network, `localhost` refers to the container, not your server.
*   If Ollama/DB are on the **Host Machine**, use `http://host.docker.internal:11434` (we enabled this mapping in compose).
*   If they are on **Another Server**, use their real IP (e.g., `192.168.1.50`).

Example `.env`:
```env
# Mattermost
MATTERMOST_TOKEN=your_token
FLASK_PORT=5000

# Ollama (External)
OLLAMA_HOST=http://192.168.1.50:11434
MODEL_NAME=llama3.1:latest

# MCP Server
MCP_SERVER_URL=http://mcp-server:8000/sse  # Note: 'mcp-server' is the docker service name!

# Database (External)
DB_HOST=192.168.1.50
DB_NAME=postgres
DB_USER=postgres
DB_PASS=password
```
**CRITICAL**: `MCP_SERVER_URL` must point to `http://mcp-server:8000/sse` because inside the Docker network, the bot sees the other container by its service name `mcp-server`.

## 2. Run

### Start in Background
```bash
docker-compose up -d --build
```

### View Logs
```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f bot
docker-compose logs -f mcp-server
```

### Stop & Remove
```bash
docker-compose down
```

## 3. Verify
*   **Web Check**: `curl http://localhost:5000` (Should see method not allowed or similar Flask response).
*   **Mattermost**: Try `/ask hello` in your chat.
