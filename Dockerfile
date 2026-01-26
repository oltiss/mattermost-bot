# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Copy project files
COPY . /app/

# Expose ports (5000 for Bot, 8000 for MCP)
EXPOSE 5000 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "mattermost.py"]
