# Mattermost Ollama Bot with PostgreSQL 🐍🤖🐘

A powerful integration bridge that connects **Mattermost**, **Ollama (Local AI)**, and **PostgreSQL**.

This bot allows proper conversations via Mattermost and can autonomously query your database to answer questions about your data (Text-to-SQL).

## Features ✨

*   **💬 Natural Chat**: Talk to local LLMs (Llama 3, Mistral, etc.) running via Ollama.
*   **🗄️ Text-to-SQL**: Ask questions like "How many users signed up today?" and the bot will:
    1.  Detect you are asking about data.
    2.  Read your DB schema.
    3.  Generate a SQL query.
    4.  Execute it (Read-Only).
    5.  Summarize the answer in plain language.
*   **⚡ Async & Feedback**: Immediate feedback ("Generuję odpowiedź...") so you know it's working.
*   **🔒 Secure**: Configuration via `.env` file. No hardcoded secrets.

## Prerequisites 🛠️

*   Python 3.8+
*   [Ollama](https://ollama.com/) running locally (`ollama serve`).
*   PostgreSQL Database.
*   Mattermost Server (with permissions to create Slash Commands).

## Installation 📥

1.  **Clone the intent:**
    ```bash
    git clone https://github.com/your-repo/mattermost-ollama-bot.git
    cd mattermost-ollama-bot
    ```

2.  **Install dependencies:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
    *(Note: minimal requirements are `flask`, `requests`, `psycopg2-binary`, `python-dotenv`)*

3.  **Configure Environment:**
    Create a `.env` file (copy from below) and fill in your details:
    ```ini
    # Mattermost
    MATTERMOST_TOKEN=your_slash_command_token
    FLASK_PORT=5000

    # Ollama
    OLLAMA_API_URL=http://localhost:11434/api/generate
    OLLAMA_MODEL=llama3.1

    # Database
    DB_HOST=localhost
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASS=password
    ```

## Usage 🚀

1.  **Start the Bot:**
    ```bash
    python mattermost.py
    ```

2.  **Mattermost Setup:**
    *   Create a Slash Command (e.g., `/bot`).
    *   Set **Request URL** to `http://YOUR_IP:5000/`.
    *   Set **Request Method** to `POST`.

## Examples 💡

*   **Chat Mode:**
    > **/bot** Tell me a joke about Python.
    >
    > **TRYB CZAT**
    > Why did the programmer quit his job? Because he didn't get arrays.

*   **SQL Mode:**
    > **/bot** List the top 5 most expensive products.
    >
    > **TRYB SQL**
    > *Query:* `SELECT name, price FROM products ORDER BY price DESC LIMIT 5`
    >
    > Here are the top 5 products...

## Security Note ⚠️

Ensure the database user provided in `.env` has **READ-ONLY (SELECT)** permissions. Do not use a user that can DROP or DELETE tables.
