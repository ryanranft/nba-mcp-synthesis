#!/bin/bash
# NBA MCP Synthesis - Docker Entrypoint Script

set -e

# Configure logging
log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1"
}

log_error() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ERROR: $1" >&2
}

log_success() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] SUCCESS: $1"
}

# Load secrets
load_secrets() {
    log "Loading secrets..."

    if [ -f "/app/load_secrets_docker.py" ]; then
        python3 /app/load_secrets_docker.py
        if [ $? -eq 0 ]; then
            log_success "Secrets loaded successfully"
        else
            log_error "Failed to load secrets"
            exit 1
        fi
    else
        log_error "Secrets loader not found"
        exit 1
    fi
}

# Wait for dependencies
wait_for_dependencies() {
    log "Waiting for dependencies..."

    # Wait for database if DB_HOST is set
    if [ -n "$DB_HOST_NBA_MCP_SYNTHESIS_WORKFLOW" ]; then
        log "Waiting for database at $DB_HOST_NBA_MCP_SYNTHESIS_WORKFLOW..."
        while ! nc -z "$DB_HOST_NBA_MCP_SYNTHESIS_WORKFLOW" "${DB_PORT_NBA_MCP_SYNTHESIS_WORKFLOW:-5432}"; do
            log "Database not ready, waiting..."
            sleep 2
        done
        log_success "Database is ready"
    fi

    # Wait for Redis if REDIS_HOST is set
    if [ -n "$REDIS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW" ]; then
        log "Waiting for Redis at $REDIS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW..."
        while ! nc -z "$REDIS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW" "${REDIS_PORT_NBA_MCP_SYNTHESIS_WORKFLOW:-6379}"; do
            log "Redis not ready, waiting..."
            sleep 2
        done
        log_success "Redis is ready"
    fi
}

# Run health check
run_health_check() {
    log "Running health check..."

    # Check if required environment variables are set
    required_vars=(
        "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"
        "ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"
        "DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"
    )

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done

    log_success "Health check passed"
}

# Main execution
main() {
    log "Starting NBA MCP Synthesis container..."

    # Load secrets
    load_secrets

    # Wait for dependencies
    wait_for_dependencies

    # Run health check
    run_health_check

    # Execute the main command
    log "Executing: $@"
    exec "$@"
}

# Run main function with all arguments
main "$@"

