# NBA MCP Synthesis - Docker Image with Unified Secrets Management
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NBA_MCP_CONTEXT=production
ENV PROJECT_NAME=nba-mcp-synthesis
ENV SPORT_NAME=NBA

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create secrets directory structure
RUN mkdir -p /app/secrets/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production

# Copy secrets loader script
COPY docker/load_secrets_docker.py /app/load_secrets_docker.py
RUN chmod +x /app/load_secrets_docker.py

# Create entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["python", "-m", "mcp_server.fastmcp_server"]


