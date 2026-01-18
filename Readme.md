# Ollama Mattermost Bot

A powerful Mattermost Chatbot that integrates with local LLMs via **Ollama** and provides direct **PostgreSQL database** interaction capabilities.

This bot allows you to chat with an AI assistant that can answer general questions and, specifically, query your database using natural language (e.g., "Show me the last 5 users").

## ✨ Features

-   **Local AI Inference**: Uses [Ollama](https://ollama.com/) to run models like Llama 3 locally.
-   **Mattermost Integration**: Communicates via Webhooks / Slash Commands.
-   **Database Tools**: The AI can verify schemas and run **read-only** SQL queries to answer questions about your data.
-   **Tool Use (MCP)**: Implements a Model Context Protocol (MCP) server for modular tool handling.
-   **Background Processing**: Handles long-running AI queries asynchronously to avoid timeouts.

## 🛠️ Prerequisites

*   **Python 3.8+**
*   **Ollama**: Installed and running with a model pulled (e.g., `llama3.1:latest`).
*   **PostgreSQL**: A database to connect to.
*   **Mattermost**: Server with permissions to create Slash Commands.

## 🚀 Installation & Setup

### 1. Clone & Prepare
Ensure you have the project files locally.

### 2. Configure Environment
Create a `.env` file in the root directory. You can copy the template below:

```bash
# Mattermost Configuration
MATTERMOST_TOKEN=your_mattermost_slash_command_token
FLASK_PORT=5000

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
MODEL_NAME=llama3.1:latest

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8000/sse

# Database Configuration (PostgreSQL)
DB_HOST=localhost
DB_NAME=postgres
DB_USER=postgres
DB_PASS=password
DB_SCHEMA=public
```

### 3. Install & Run

#### Option A: 🐳 Docker (Recommended)
This is the easiest way to run the bot.

```bash
docker-compose up --build
```

This will start the **MCP Server** and **Mattermost Bot** in containers.
*   Ensure your `.env` file is present.
*   If your database is on the host machine, you might need to use `host.docker.internal` as `DB_HOST`.

#### Option B: Manual Setup (Python)
If you prefer running without Docker:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Terminal 1: Start MCP Server
python server.py

# Terminal 2: Start Bot
python mattermost.py
```

## 💬 Usage

1.  **Mattermost Setup**:
    *   Go to **Integrations > Slash Commands**.
    *   Add a new command (e.g., `/ask`).
    *   **Request URL**: `http://<your-bot-ip>:5000/` (Ensure this is reachable from Mattermost).
    *   **Method**: `POST`.
    *   Copy the **Token** and paste it into your `.env` as `MATTERMOST_TOKEN`.

2.  **Interact**:
    *   In Mattermost, type: `/ask What is the weather like?` (General chat).
    *   Or: `/ask List all tables in the database.` (Database tool usage).
    *   The bot will respond with "🧠 Thinking..." and then update with the answer.

## 📂 Project Structure

*   `mattermost.py`: Main Flask application handling Mattermost webhooks.
*   `server.py`: FastMCP server defining the database tools (`query_database`, `get_database_schema`).
*   `ai_handler.py`: Logic for connecting to Ollama and routing tool calls to the MCP server.
*   `ai_handler.py`: Logic for connecting to Ollama and routing tool calls to the MCP server.

