# 🚀 Deployment Guide: Mattermost Bot (LXC)

This guide assumes you are deploying the bot on a **Proxmox LXC Container** (Debian 12 or Ubuntu 24.04).

## 1. Prepare the LXC Container

Run these commands inside your LXC container's console as `root`.

### Update & Install System Dependencies
```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip git curl
```

### Create Service User
Create a dedicated user to run the application securely.
```bash
useradd -m -s /bin/bash mattermost
```

## 2. Application Setup

### Clone/Copy the Project
We will install the application to `/opt/mattermost-bot`.

```bash
# Create directory and set permissions
mkdir -p /opt/mattermost-bot
chown mattermost:mattermost /opt/mattermost-bot
```

*Now, copy your project files (via SCP, Git, or FileZilla) into `/opt/mattermost-bot` on the container.*

### Install Python Dependencies
Switch to the user and set up the environment.

```bash
su - mattermost
cd /opt/mattermost-bot

# Create Virtual Environment
python3 -m venv .venv
source .venv/bin/activate

# Install Requirements
pip install --upgrade pip
pip install -r requirements.txt

# Exit user session
exit
```

### Configure Environment Variables
Create/Edit the `.env` file with production secrets.

```bash
nano /opt/mattermost-bot/.env
```

**Paste your `.env` content:**
Ensure you point `OLLAMA_HOST` and `DB_HOST` to your external servers' IPs.

```bash
# Example
MATTERMOST_TOKEN=your_token_here
FLASK_PORT=5000
OLLAMA_HOST=http://192.168.1.50:11434  # External Ollama IP
DB_HOST=192.168.1.50                 # External DB IP
DB_NAME=postgres
DB_USER=postgres
DB_PASS=password
```

Set permissions so only the `mattermost` user can read it:
```bash
chown mattermost:mattermost /opt/mattermost-bot/.env
chmod 600 /opt/mattermost-bot/.env
```

## 3. Install Systemd Services

Copy the service files from the `deployment/` directory to the system directory.

```bash
cd /opt/mattermost-bot/deployment

cp mcp-server.service /etc/systemd/system/
cp mattermost-bot.service /etc/systemd/system/

# Reload Systemd to see new services
systemctl daemon-reload
```

### Enable and Start Services

```bash
# Enable auto-start on boot
systemctl enable mcp-server
systemctl enable mattermost-bot

# Start them now
systemctl start mcp-server
systemctl start mattermost-bot
```

### Check Status

```bash
systemctl status mcp-server
systemctl status mattermost-bot
```

## 4. Troubleshooting

**View Logs:**
```bash
journalctl -u mattermost-bot -f
journalctl -u mcp-server -f
```

**Common Issues:**
*   **Connection Refused**: Check if `OLLAMA_HOST` and `DB_HOST` are reachable from this container (Ping them). Check Proxmox Firewall.
*   **Permission Denied**: Ensure `/opt/mattermost-bot` is owned by `mattermost:mattermost`.
