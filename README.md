# Mattermost AI Database Assistant 🤖📊

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Docker](https://img.shields.io/badge/docker-available-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A smart Mattermost bot that bridges the gap between your chat team and your data. Powered by **Ollama** and the **Model Context Protocol (MCP)**, this bot allows users to query a PostgreSQL database using natural language or specific command lookups.

## 🚀 Features

- **Natural Language SQL**: Ask questions in English, get answers from your database.
- **Client Lookup**: Retrieve detailed client information by ID directly from the `clients` table.
- **Schema Aware**: The bot inspects your database schema (`get_database_schema`) to ensure accurate queries.
- **Secure by Design**:
  - Runs in a read-only database session.
  - Restricted to `SELECT` statements.
  - Uses MCP to isolate database tools from the LLM logic.
- **Docker Ready**: Fully containerized setup for easy deployment.

## 🛠 Architecture

The project consists of three main components:

1.  **Bot Service (`mattermost.py`)**: A Flask application that handles Mattermost outgoing webhooks. It processes incoming requests and delegates them to the AI handler.
2.  **AI Logic (`ai_handler.py`)**: Uses Ollama to interpret user intents and calls MCP tools.
3.  **MCP Server (`server.py`)**: A dedicated tool server that executes database queries securely (`read-only` mode).
4.  **Command Logic (`slash_commands.py`)**: Defines specific prompts based on the token used (e.g., general query vs. specific ID lookup).

They communicate via the Model Context Protocol (MCP) over SSE (Server-Sent Events).

## 📋 Prerequisites

- **Docker** and **Docker Compose** installed.
- **Ollama** running (locally or on a network server) with a model pulled (e.g., `llama3.1`).
- **PostgreSQL** database.
- **Mattermost** server (admin access required to set up webhooks).

## ⚙️ Configuration

### 1. Clone the repository

```bash
git clone <repository-url>
cd mattermost-bot
```

### 2. Create a `.env` file

Create a file named `.env` in the root directory. You can use `.env.example` as a template.

**Important**: This bot supports multiple command tokens for different functionalities.

```ini
# --- Mattermost Settings ---
# Token for General SQL Queries (e.g., !db)
SQL_TOKEN=your_mattermost_token_for_sql
# Token for Client ID Lookup (e.g., !client)
ID_TOKEN=your_mattermost_token_for_id_lookup
# Token for PPPoE Status (e.g., !pppoe)
PPPOE_TOKEN=your_mattermost_token_for_pppoe

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

You need to set up **Outgoing Webhooks** in Mattermost for each command you want to use.

1.  Go to **Main Menu > Integrations > Outgoing Webhooks**.
2.  Click **Add Outgoing Webhook**.
3.  **Common Settings**:
    - **Content Type**: `application/x-www-form-urlencoded`
    - **Callback URLs**: `http://<YOUR_BOT_SERVER_IP>:5000/`

4.  **Create Webhook for SQL Queries**:
    - **Trigger Words**: `!db`, `!ask`
    - Copy the **Token** -> Paste into `.env` as `SQL_TOKEN`.

5.  **Create Webhook for Client ID Lookup**:
    - **Trigger Words**: `!client`, `!id`
    - Copy the **Token** -> Paste into `.env` as `ID_TOKEN`.

6.  **(Optional) Create Webhook for PPPoE**:
    - **Trigger Words**: `!pppoe`
    - Copy the **Token** -> Paste into `.env` as `PPPOE_TOKEN`.

7.  **Restart the bot container** if you updated the `.env` file:
    ```bash
    docker-compose restart bot
    ```

## 🧪 Usage

### General SQL Query (`SQL_TOKEN`)
*Use this for natural language questions on your data.*

> **User**: !db Show me the last 5 users who registered.
>
> **Bot**: 🧠 Thinking...
>
> **Bot**: Here are the last 5 users: ...

### Client ID Lookup (`ID_TOKEN`)
*Use this to fetch specific client details from the `clients` table by ID.*

> **User**: !client 12345
>
> **Bot**: 🧠 Thinking...
>
> **Bot**: Client 12345 details: {name: "John Doe", status: "Active"...}

## 🛡 Security Notes

- The MCP server enforces a **Read-Only** session on the PostgreSQL connection.
- Only `SELECT` statements are allowed by the `query_database` tool.
- Ensure your database user (`DB_USER`) has appropriate permissions (least privilege).

## ❓ Troubleshooting

| Issue | Possible Cause | Solution |
| :--- | :--- | :--- |
| **Bot doesn't respond** | Webhook URL is unreachable from Mattermost. | checking firewall rules and ensuring the bot container is running and exposing port 5000. |
| **"Invalid token"** | The token used in `.env` doesn't match Mattermost. | Verify `SQL_TOKEN`, `ID_TOKEN`, etc. in `.env`. |
| **Ollama connection error** | `OLLAMA_HOST` is incorrect. | Use `http://host.docker.internal:11434` if running locally, or the correct IP address. |
| **Database error** | Credentials or Schema incorrect. | Check `DB_HOST`, `DB_USER`, `DB_PASS`, and `DB_SCHEMA` variables. |

---

Made with ❤️ by the Data Team.
