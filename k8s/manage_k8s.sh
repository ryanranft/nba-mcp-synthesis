#!/bin/bash
# Kubernetes Secrets Management Script

set -e

# Configuration
K8S_DIR="./k8s"
SECRETS_DIR="./secrets"
NAMESPACES=(
    "nba-mcp-synthesis"
    "nba-mcp-synthesis-dev"
    "nba-mcp-synthesis-test"
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

# Check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    log "kubectl is available and connected to cluster"
}

# Create namespaces
create_namespaces() {
    log "Creating namespaces..."

    for namespace in "${NAMESPACES[@]}"; do
        if kubectl get namespace "$namespace" &> /dev/null; then
            log_warning "Namespace $namespace already exists"
        else
            kubectl create namespace "$namespace"
            log "Created namespace: $namespace"
        fi
    done
}

# Create secrets from files
create_secrets_from_files() {
    local namespace=$1
    local environment=$2

    log "Creating secrets for namespace: $namespace (environment: $environment)"

    # Create main application secrets
    local secret_name="nba-mcp-synthesis-secrets"
    local secret_file="$SECRETS_DIR/secrets-$environment.yaml"

    if [ -f "$secret_file" ]; then
        kubectl apply -f "$secret_file" -n "$namespace"
        log "Applied secrets from $secret_file"
    else
        log_warning "Secret file $secret_file not found"
    fi

    # Create database secrets
    local db_secret_name="nba-mcp-synthesis-db-secrets"
    local db_secret_file="$SECRETS_DIR/secrets-$environment.yaml"

    if [ -f "$db_secret_file" ]; then
        kubectl apply -f "$db_secret_file" -n "$namespace"
        log "Applied database secrets from $db_secret_file"
    else
        log_warning "Database secret file $db_secret_file not found"
    fi

    # Create Redis secrets
    local redis_secret_name="nba-mcp-synthesis-redis-secrets"
    local redis_secret_file="$SECRETS_DIR/secrets-$environment.yaml"

    if [ -f "$redis_secret_file" ]; then
        kubectl apply -f "$redis_secret_file" -n "$namespace"
        log "Applied Redis secrets from $redis_secret_file"
    else
        log_warning "Redis secret file $redis_secret_file not found"
    fi
}

# Deploy application
deploy_application() {
    local namespace=$1
    local environment=$2

    log "Deploying application to namespace: $namespace (environment: $environment)"

    # Apply init container config
    if [ -f "$K8S_DIR/init-container.yaml" ]; then
        kubectl apply -f "$K8S_DIR/init-container.yaml" -n "$namespace"
        log "Applied init container configuration"
    fi

    # Apply deployment
    if [ -f "$K8S_DIR/deployment.yaml" ]; then
        kubectl apply -f "$K8S_DIR/deployment.yaml" -n "$namespace"
        log "Applied deployment configuration"
    fi

    # Apply database
    if [ -f "$K8S_DIR/database.yaml" ]; then
        kubectl apply -f "$K8S_DIR/database.yaml" -n "$namespace"
        log "Applied database configuration"
    fi

    # Apply ingress
    if [ -f "$K8S_DIR/ingress.yaml" ]; then
        kubectl apply -f "$K8S_DIR/ingress.yaml" -n "$namespace"
        log "Applied ingress configuration"
    fi
}

# Check deployment status
check_deployment_status() {
    local namespace=$1

    log "Checking deployment status for namespace: $namespace"

    # Check pods
    kubectl get pods -n "$namespace"

    # Check services
    kubectl get services -n "$namespace"

    # Check ingress
    kubectl get ingress -n "$namespace"

    # Check secrets
    kubectl get secrets -n "$namespace"
}

# Show logs
show_logs() {
    local namespace=$1
    local pod_name=$2

    if [ -z "$pod_name" ]; then
        log "Showing logs for all pods in namespace: $namespace"
        kubectl logs -f -l app=nba-mcp-synthesis -n "$namespace"
    else
        log "Showing logs for pod: $pod_name in namespace: $namespace"
        kubectl logs -f "$pod_name" -n "$namespace"
    fi
}

# Scale deployment
scale_deployment() {
    local namespace=$1
    local replicas=$2

    log "Scaling deployment to $replicas replicas in namespace: $namespace"

    kubectl scale deployment nba-mcp-synthesis --replicas="$replicas" -n "$namespace"

    log "Deployment scaled to $replicas replicas"
}

# Delete deployment
delete_deployment() {
    local namespace=$1

    log "Deleting deployment from namespace: $namespace"

    # Delete ingress
    kubectl delete ingress nba-mcp-synthesis-ingress -n "$namespace" --ignore-not-found=true

    # Delete services
    kubectl delete service nba-mcp-synthesis-service -n "$namespace" --ignore-not-found=true
    kubectl delete service nba-mcp-synthesis-headless -n "$namespace" --ignore-not-found=true

    # Delete deployment
    kubectl delete deployment nba-mcp-synthesis -n "$namespace" --ignore-not-found=true

    # Delete StatefulSet
    kubectl delete statefulset nba-mcp-postgres -n "$namespace" --ignore-not-found=true
    kubectl delete deployment nba-mcp-redis -n "$namespace" --ignore-not-found=true

    # Delete PVCs
    kubectl delete pvc postgres-pvc -n "$namespace" --ignore-not-found=true
    kubectl delete pvc redis-pvc -n "$namespace" --ignore-not-found=true

    log "Deployment deleted from namespace: $namespace"
}

# Clean up
cleanup() {
    log "Cleaning up Kubernetes resources..."

    for namespace in "${NAMESPACES[@]}"; do
        delete_deployment "$namespace"
    done

    # Delete namespaces
    for namespace in "${NAMESPACES[@]}"; do
        kubectl delete namespace "$namespace" --ignore-not-found=true
        log "Deleted namespace: $namespace"
    done

    log "Cleanup completed"
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  init              Initialize Kubernetes resources"
    echo "  deploy [env]      Deploy application for specified environment (prod/dev/test)"
    echo "  status [env]      Check deployment status for specified environment"
    echo "  logs [env] [pod]  Show logs for specified environment and pod"
    echo "  scale [env] [n]   Scale deployment to n replicas"
    echo "  delete [env]      Delete deployment for specified environment"
    echo "  cleanup           Clean up all Kubernetes resources"
    echo "  help              Show this help message"
    echo ""
    echo "Environments:"
    echo "  prod              Production environment"
    echo "  dev               Development environment"
    echo "  test              Testing environment"
    echo ""
    echo "Examples:"
    echo "  $0 init"
    echo "  $0 deploy prod"
    echo "  $0 status dev"
    echo "  $0 logs test nba-mcp-synthesis-xxx"
    echo "  $0 scale prod 5"
    echo "  $0 delete dev"
    echo "  $0 cleanup"
}

# Main function
main() {
    case "$1" in
        init)
            check_kubectl
            create_namespaces
            ;;
        deploy)
            if [ -z "$2" ]; then
                log_error "Environment not specified"
                show_help
                exit 1
            fi
            check_kubectl
            create_namespaces
            create_secrets_from_files "nba-mcp-synthesis-$2" "$2"
            deploy_application "nba-mcp-synthesis-$2" "$2"
            ;;
        status)
            if [ -z "$2" ]; then
                log_error "Environment not specified"
                show_help
                exit 1
            fi
            check_deployment_status "nba-mcp-synthesis-$2"
            ;;
        logs)
            if [ -z "$2" ]; then
                log_error "Environment not specified"
                show_help
                exit 1
            fi
            show_logs "nba-mcp-synthesis-$2" "$3"
            ;;
        scale)
            if [ -z "$2" ] || [ -z "$3" ]; then
                log_error "Environment and replicas not specified"
                show_help
                exit 1
            fi
            scale_deployment "nba-mcp-synthesis-$2" "$3"
            ;;
        delete)
            if [ -z "$2" ]; then
                log_error "Environment not specified"
                show_help
                exit 1
            fi
            delete_deployment "nba-mcp-synthesis-$2"
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

