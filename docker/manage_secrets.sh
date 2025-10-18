#!/bin/bash
# Docker Secrets Management Script

set -e

# Configuration
SECRETS_DIR="./secrets"
COMPOSE_FILES=(
    "docker-compose.dev.yml"
    "docker-compose.prod.yml"
    "docker-compose.test.yml"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date -u +%Y-%m-%dT%H:%M:%SZ)]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ERROR:${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[$(date -u +%Y-%m-%dT%H:%M:%SZ)] WARNING:${NC} $1"
}

# Create secrets directory
create_secrets_dir() {
    log "Creating secrets directory..."
    mkdir -p "$SECRETS_DIR"
    log "Secrets directory created at $SECRETS_DIR"
}

# Generate mock secrets for testing
generate_mock_secrets() {
    log "Generating mock secrets for testing..."

    # Mock API keys
    echo "mock_google_api_key" > "$SECRETS_DIR/GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_TEST.env"
    echo "mock_anthropic_api_key" > "$SECRETS_DIR/ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_TEST.env"
    echo "mock_deepseek_api_key" > "$SECRETS_DIR/DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_TEST.env"
    echo "mock_openai_api_key" > "$SECRETS_DIR/OPENAI_API_KEY_NBA_MCP_SYNTHESIS_TEST.env"

    # Mock database credentials
    echo "mock_db_password" > "$SECRETS_DIR/DB_PASSWORD_NBA_MCP_SYNTHESIS_TEST.env"
    echo "postgres-test" > "$SECRETS_DIR/DB_HOST_NBA_MCP_SYNTHESIS_TEST.env"
    echo "5432" > "$SECRETS_DIR/DB_PORT_NBA_MCP_SYNTHESIS_TEST.env"

    # Mock integration credentials
    echo "mock_slack_webhook" > "$SECRETS_DIR/SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_TEST.env"
    echo "mock_linear_api_key" > "$SECRETS_DIR/LINEAR_API_KEY_BIG_CAT_BETS_GLOBAL_TEST.env"
    echo "mock_linear_team_id" > "$SECRETS_DIR/LINEAR_TEAM_ID_BIG_CAT_BETS_GLOBAL_TEST.env"
    echo "mock_linear_project_id" > "$SECRETS_DIR/LINEAR_PROJECT_ID_BIG_CAT_BETS_GLOBAL_TEST.env"

    log "Mock secrets generated"
}

# Validate secrets
validate_secrets() {
    log "Validating secrets..."

    local missing_secrets=()

    # Check for required secrets
    local required_secrets=(
        "GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "DB_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "DB_HOST_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "DB_PORT_NBA_MCP_SYNTHESIS_WORKFLOW.env"
        "SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_WORKFLOW.env"
        "LINEAR_API_KEY_BIG_CAT_BETS_GLOBAL_WORKFLOW.env"
        "LINEAR_TEAM_ID_BIG_CAT_BETS_GLOBAL_WORKFLOW.env"
        "LINEAR_PROJECT_ID_BIG_CAT_BETS_GLOBAL_WORKFLOW.env"
    )

    for secret in "${required_secrets[@]}"; do
        if [ ! -f "$SECRETS_DIR/$secret" ]; then
            missing_secrets+=("$secret")
        fi
    done

    if [ ${#missing_secrets[@]} -gt 0 ]; then
        log_error "Missing required secrets:"
        for secret in "${missing_secrets[@]}"; do
            log_error "  - $secret"
        done
        return 1
    fi

    log "All required secrets are present"
    return 0
}

# Set file permissions
set_permissions() {
    log "Setting file permissions..."

    # Set restrictive permissions on secrets
    chmod 600 "$SECRETS_DIR"/*.env

    # Set executable permissions on scripts
    chmod +x docker/entrypoint.sh
    chmod +x docker/load_secrets_docker.py

    log "File permissions set"
}

# Build Docker images
build_images() {
    log "Building Docker images..."

    docker build -t nba-mcp-synthesis:latest .

    log "Docker images built"
}

# Start services
start_services() {
    local env=$1
    local compose_file="docker-compose.$env.yml"

    if [ ! -f "$compose_file" ]; then
        log_error "Compose file $compose_file not found"
        return 1
    fi

    log "Starting services for $env environment..."

    docker-compose -f "$compose_file" up -d

    log "Services started for $env environment"
}

# Stop services
stop_services() {
    local env=$1
    local compose_file="docker-compose.$env.yml"

    if [ ! -f "$compose_file" ]; then
        log_error "Compose file $compose_file not found"
        return 1
    fi

    log "Stopping services for $env environment..."

    docker-compose -f "$compose_file" down

    log "Services stopped for $env environment"
}

# Show logs
show_logs() {
    local env=$1
    local compose_file="docker-compose.$env.yml"

    if [ ! -f "$compose_file" ]; then
        log_error "Compose file $compose_file not found"
        return 1
    fi

    docker-compose -f "$compose_file" logs -f
}

# Clean up
cleanup() {
    log "Cleaning up..."

    # Stop all services
    for compose_file in "${COMPOSE_FILES[@]}"; do
        if [ -f "$compose_file" ]; then
            docker-compose -f "$compose_file" down -v
        fi
    done

    # Remove images
    docker rmi nba-mcp-synthesis:latest 2>/dev/null || true

    # Remove volumes
    docker volume prune -f

    log "Cleanup completed"
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND] [ENVIRONMENT]"
    echo ""
    echo "Commands:"
    echo "  init              Initialize secrets directory and generate mock secrets"
    echo "  validate          Validate that all required secrets are present"
    echo "  build             Build Docker images"
    echo "  start [env]       Start services for specified environment (dev/prod/test)"
    echo "  stop [env]        Stop services for specified environment"
    echo "  logs [env]        Show logs for specified environment"
    echo "  cleanup           Clean up all Docker resources"
    echo "  help              Show this help message"
    echo ""
    echo "Environments:"
    echo "  dev               Development environment"
    echo "  prod              Production environment"
    echo "  test              Testing environment"
    echo ""
    echo "Examples:"
    echo "  $0 init"
    echo "  $0 validate"
    echo "  $0 build"
    echo "  $0 start dev"
    echo "  $0 stop prod"
    echo "  $0 logs test"
    echo "  $0 cleanup"
}

# Main function
main() {
    case "$1" in
        init)
            create_secrets_dir
            generate_mock_secrets
            set_permissions
            ;;
        validate)
            validate_secrets
            ;;
        build)
            build_images
            ;;
        start)
            if [ -z "$2" ]; then
                log_error "Environment not specified"
                show_help
                exit 1
            fi
            start_services "$2"
            ;;
        stop)
            if [ -z "$2" ]; then
                log_error "Environment not specified"
                show_help
                exit 1
            fi
            stop_services "$2"
            ;;
        logs)
            if [ -z "$2" ]; then
                log_error "Environment not specified"
                show_help
                exit 1
            fi
            show_logs "$2"
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"


