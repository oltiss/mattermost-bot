# Mattermost Database Query Bot

A Python Flask application that acts as a custom integration for Mattermost. This bot allows users to query specific customer details and PPPoE/IP assignments directly from a PostgreSQL database using Mattermost Slash Commands.

## Features

This bot exposes two main endpoints for Mattermost slash commands:

* **`/id <client_id>`**: Queries customer details. It fetches data from the `clients` table and returns formatted JSON containing information such as name, status, description, IBAN, email, phone number, NIP, and address.
* **`/pppoe <client_id>`**: Queries hardware IP configurations. It fetches data from the `hardware_ips` table and returns associated IP details.

## Prerequisites

* Python 3.7+
* PostgreSQL database
* Mattermost server with the ability to create Custom Slash Commands

## Installation

1. **Clone or download the project** to your desired directory.

2. **Set up a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**:
   Make sure you have `pip` installed, then run:
   ```bash
   pip install Flask python-dotenv requests psycopg2-binary asyncio
   ```
   *(Note: You can also save these into a `requirements.txt` file for easier deployment)*

## Configuration

The bot requires a `.env` file to securely load database credentials and Mattermost validation tokens. Create a file named `.env` in the root folder of the project (`c:\Users\michm\Desktop\vscode\mattermost-bot\`) and add the following:

```env
# Database Configuration
DB_HOST=localhost
DB_NAME=postgres
DB_USER=postgres
DB_PASS=your_db_password
DB_SCHEMA=public

# Mattermost Slash Command Tokens (Used to verify requests come from Mattermost)
ID_TOKEN=your_mattermost_id_token
PPPOE_TOKEN=your_mattermost_pppoe_token

# App Configuration
FLASK_PORT=5000
```

## Running the Bot

To start the bot, simply run the Python script:

```bash
python mattermost.py
```

The application will run on `http://0.0.0.0:5000/` by default (or the port defined in `FLASK_PORT`).

## Mattermost Setup

To connect Mattermost to your bot, go to **Integrations > Slash Commands** in your Mattermost interface and create two commands:

### 1. The `/id` Command
* **Command:** `id`
* **Request URL:** `http://<your-server-ip>:5000/query/id`
* **Request Method:** POST
* *After saving, Mattermost will give you a Token. Paste this into your `.env` file as `ID_TOKEN`.*

### 2. The `/pppoe` Command
* **Command:** `pppoe`
* **Request URL:** `http://<your-server-ip>:5000/query/pppoe`
* **Request Method:** POST
* *After saving, Mattermost will give you a Token. Paste this into your `.env` file as `PPPOE_TOKEN`.*
