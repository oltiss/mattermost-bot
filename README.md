# Mattermost AI Database Assistant 🤖📊

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/docker-available-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A smart Mattermost bot that bridges the gap between your chat team and your data. Powered by **Ollama** and the **Model Context Protocol (MCP)**, this bot allows users to query a PostgreSQL database using natural language.

## 🚀 Features

- **Natural Language SQL**: Ask questions in English, get answers from your database.
- **Schema Aware**: The bot inspects your database schema (`get_database_schema`) to write accurate queries.
- **Secure by Design**:
  - Runs in a read-only database session.
  - Restricted to `SELECT` statements.
  - Uses MCP to isolate database tools from the LLM logic.
- **Docker Ready**: Fully containerized setup for easy deployment.

## 🛠 Architecture

The project consists of two main services running in Docker:

1.  **Bot Service (`mattermost.py`)**: Handles Mattermost webhooks and manages the conversation state.
2.  **MCP Server (`server.py`)**: A dedicated tool server that executes database queries.

They communicate via the Model Context Protocol (MCP) over SSE (Server-Sent Events).

## 📋 Prerequisites

- **Docker** and **Docker Compose** installed.
- **Ollama** running (locally or on a network server) with a model pulled (e.g., `llama3.1`).
- **PostgreSQL** database.
- **Mattermost** server (admin access required to set up webhooks).

## ⚙️ Configuration

1.  **Clone the repository**:

    ```bash
    git clone <repository-url>
    cd mattermost-bot
    ```

2.  **Create a `.env` file**:
    Create a file named `.env` in the root directory with the following content:

    ```ini
    # --- Mattermost Settings ---
    # Token provided by Mattermost Outgoing Webhook
    MATTERMOST_TOKEN=your_mattermost_token
    # Port for the Flask bot
    FLASK_PORT=5000

    # --- Ollama Settings ---
    # URL where Ollama is running.
    # If running on the host machine, use http://host.docker.internal:11434
    OLLAMA_HOST=http://host.docker.internal:11434
    OLLAMA_MODEL=llama3.1:latest

    # --- MCP Settings ---
    # Internal Docker URL for the MCP server (do not change unless you rename services)
    MCP_SERVER_URL=http://mcp-server:8000/sse

    # --- Database Settings ---
    DB_HOST=host.docker.internal
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASS=your_password
    DB_SCHEMA=public
    ```

## 🐳 Running with Docker

1.  **Start the services**:

    ```bash
    docker-compose up -d --build
    ```

2.  **Check logs**:

    ```bash
    docker-compose logs -f
    ```

3.  **Stop services**:
    ```bash
    docker-compose down
    ```

## 🔌 Mattermost Integration

1.  Go to **Main Menu > Integrations > Outgoing Webhooks**.
2.  Click **Add Outgoing Webhook**.
3.  Fill in the details:
    - **Content Type**: `application/x-www-form-urlencoded`
    - **Trigger Words**: `!db`, `!ask` (or your preference).
    - **Callback URLs**: `http://<YOUR_SERVER_IP>:5000/`
4.  Copy the **Token** displayed after creation and paste it into your `.env` file as `MATTERMOST_TOKEN`.
5.  Restart the bot container if you changed the `.env` file:
    ```bash
    docker-compose restart bot
    ```

## 🧪 Usage

In any Mattermost channel where the webhook is configured:

> **User**: !db Show me the last 5 users who registered.
>
> **Bot**: 🧠 Thinking... (Query: !db Show me the last 5 users who registered.)
>
> **Bot**: Here are the last 5 users:
> | id | username | created_at |
> |---|---|---|
> | 101 | alice | 2023-10-01 |
> ...

## 🛡 Security Notes

- The MCP server enforces a **Read-Only** session on the PostgreSQL connection.
- Only `SELECT` statements are allowed by the `query_database` tool.
- Ensure your database user (`DB_USER`) has appropriate permissions (least privilege).
