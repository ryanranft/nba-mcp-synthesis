#!/bin/bash

# NBA MCP Synthesis - Phase 3: Application Deployment
# This script deploys the NBA MCP Synthesis application to Kubernetes

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$PROJECT_ROOT/k8s"
LOG_FILE="/tmp/nba-mcp-phase3-application.log"

# Default values
DRY_RUN=false
VERBOSE=false
NAMESPACE="nba-mcp-synthesis"
IMAGE_TAG="latest"
WAIT_FOR_READY=true

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
NBA MCP Synthesis - Phase 3: Application Deployment

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -d, --dry-run          Show what would be done without executing
    -v, --verbose          Enable verbose output
    -n, --namespace NS     Kubernetes namespace (default: nba-mcp-synthesis)
    -t, --image-tag TAG    Docker image tag (default: latest)
    --no-wait              Don't wait for pods to be ready
    -h, --help            Show this help message

EXAMPLES:
    $0                                    # Standard deployment
    $0 --dry-run                          # Preview deployment
    $0 --image-tag v1.2.3                 # Deploy specific version
    $0 --namespace custom-ns              # Deploy to custom namespace

DESCRIPTION:
    This script deploys the NBA MCP Synthesis application:
    1. Builds and pushes Docker image to ECR
    2. Deploys Kubernetes manifests
    3. Configures Horizontal Pod Autoscaler
    4. Sets up ingress and service
    5. Verifies application health

REQUIREMENTS:
    - EKS cluster running (from Phase 1)
    - Secrets migrated to AWS (from Phase 2)
    - Docker installed and running
    - kubectl configured

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -t|--image-tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --no-wait)
                WAIT_FOR_READY=false
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Validation functions
validate_prerequisites() {
    log "Validating prerequisites..."

    # Check kubectl access
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "kubectl not configured or cluster not accessible"
        log "Please ensure kubectl is configured and cluster is running"
        exit 1
    fi

    log_success "kubectl access verified"

    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        log_warning "Namespace '$NAMESPACE' not found, will create it"
    else
        log_success "Namespace '$NAMESPACE' exists"
    fi

    # Check Docker
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        log "Please start Docker and try again"
        exit 1
    fi

    log_success "Docker is running"

    # Check Kubernetes manifests exist
    if [[ ! -d "$K8S_DIR" ]]; then
        log_error "Kubernetes manifests directory not found: $K8S_DIR"
        exit 1
    fi

    local required_manifests=("namespace.yaml" "deployment.yaml" "service.yaml" "ingress.yaml" "hpa.yaml")
    for manifest in "${required_manifests[@]}"; do
        if [[ ! -f "$K8S_DIR/$manifest" ]]; then
            log_error "Required manifest not found: $K8S_DIR/$manifest"
            exit 1
        fi
    done

    log_success "Kubernetes manifests validated"
}

# Docker functions
build_and_push_image() {
    log "Building and pushing Docker image..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would build and push image with tag $IMAGE_TAG"
        return 0
    fi

    # Get AWS account ID and region
    local account_id
    account_id=$(aws sts get-caller-identity --query Account --output text)

    local region
    region=$(aws configure get region || echo "us-east-1")

    local ecr_repo="$account_id.dkr.ecr.$region.amazonaws.com/nba-mcp-synthesis"

    # Login to ECR
    log "Logging in to ECR..."
    aws ecr get-login-password --region "$region" | docker login --username AWS --password-stdin "$account_id.dkr.ecr.$region.amazonaws.com"

    # Build image
    log "Building Docker image..."
    docker build -t "nba-mcp-synthesis:$IMAGE_TAG" .

    # Tag for ECR
    docker tag "nba-mcp-synthesis:$IMAGE_TAG" "$ecr_repo:$IMAGE_TAG"

    # Push to ECR
    log "Pushing image to ECR..."
    docker push "$ecr_repo:$IMAGE_TAG"

    log_success "Docker image built and pushed successfully"
}

# Kubernetes deployment functions
deploy_namespace() {
    log "Deploying namespace..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would deploy namespace"
        return 0
    fi

    if kubectl apply -f "$K8S_DIR/namespace.yaml"; then
        log_success "Namespace deployed"
    else
        log_error "Failed to deploy namespace"
        exit 1
    fi
}

deploy_application() {
    log "Deploying application manifests..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would deploy application manifests"
        return 0
    fi

    # Update image tag in deployment if needed
    if [[ "$IMAGE_TAG" != "latest" ]]; then
        log "Updating image tag to $IMAGE_TAG"
        sed -i.bak "s|:latest|:$IMAGE_TAG|g" "$K8S_DIR/deployment.yaml"
    fi

    # Deploy manifests
    local manifests=("deployment.yaml" "service.yaml" "ingress.yaml" "hpa.yaml")

    for manifest in "${manifests[@]}"; do
        log "Deploying $manifest..."
        if kubectl apply -f "$K8S_DIR/$manifest"; then
            log_success "$manifest deployed"
        else
            log_error "Failed to deploy $manifest"
            exit 1
        fi
    done

    # Restore original deployment.yaml if modified
    if [[ "$IMAGE_TAG" != "latest" && -f "$K8S_DIR/deployment.yaml.bak" ]]; then
        mv "$K8S_DIR/deployment.yaml.bak" "$K8S_DIR/deployment.yaml"
    fi

    log_success "Application manifests deployed"
}

wait_for_deployment() {
    log "Waiting for deployment to be ready..."

    if [[ "$DRY_RUN" == "true" || "$WAIT_FOR_READY" == "false" ]]; then
        log "DRY RUN: Would wait for deployment to be ready"
        return 0
    fi

    # Wait for deployment rollout
    if kubectl rollout status deployment/nba-mcp-synthesis -n "$NAMESPACE" --timeout=600s; then
        log_success "Deployment rollout completed"
    else
        log_error "Deployment rollout failed or timed out"
        exit 1
    fi

    # Wait for pods to be ready
    if kubectl wait --for=condition=ready pod -l app=nba-mcp-synthesis -n "$NAMESPACE" --timeout=300s; then
        log_success "Pods are ready"
    else
        log_error "Pods failed to become ready"
        exit 1
    fi
}

# Health check functions
verify_deployment() {
    log "Verifying deployment..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would verify deployment"
        return 0
    fi

    # Check deployment status
    local replicas
    replicas=$(kubectl get deployment nba-mcp-synthesis -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' || echo "0")

    if [[ "$replicas" -gt 0 ]]; then
        log_success "Deployment has $replicas ready replicas"
    else
        log_error "No ready replicas found"
        exit 1
    fi

    # Check pod status
    local running_pods
    running_pods=$(kubectl get pods -n "$NAMESPACE" -l app=nba-mcp-synthesis --no-headers | grep -c "Running" || echo "0")

    if [[ "$running_pods" -gt 0 ]]; then
        log_success "Found $running_pods running pods"
    else
        log_error "No running pods found"
        exit 1
    fi

    # Check service
    if kubectl get service nba-mcp-synthesis-service -n "$NAMESPACE" >/dev/null 2>&1; then
        log_success "Service is available"
    else
        log_error "Service not found"
        exit 1
    fi

    # Check ingress
    if kubectl get ingress -n "$NAMESPACE" | grep -q "nba-mcp-synthesis"; then
        log_success "Ingress is configured"
    else
        log_warning "Ingress may not be ready yet"
    fi

    # Check HPA
    if kubectl get hpa nba-mcp-synthesis-hpa -n "$NAMESPACE" >/dev/null 2>&1; then
        log_success "HPA is configured"
    else
        log_warning "HPA may not be ready yet"
    fi
}

test_health_endpoints() {
    log "Testing health endpoints..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would test health endpoints"
        return 0
    fi

    # Port forward to test endpoints
    log "Setting up port forward for testing..."
    kubectl port-forward service/nba-mcp-synthesis-service 8080:80 -n "$NAMESPACE" &
    local pf_pid=$!

    # Wait for port forward to establish
    sleep 5

    # Test health endpoint
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        log_success "Health endpoint is responding"
    else
        log_warning "Health endpoint may not be ready yet"
    fi

    # Test metrics endpoint
    if curl -f http://localhost:8080/metrics >/dev/null 2>&1; then
        log_success "Metrics endpoint is responding"
    else
        log_warning "Metrics endpoint may not be ready yet"
    fi

    # Clean up port forward
    kill $pf_pid 2>/dev/null || true

    log_success "Health endpoint testing completed"
}

# Main execution
main() {
    log "Starting NBA MCP Synthesis Phase 3: Application Deployment..."
    log "Configuration:"
    log "  Namespace: $NAMESPACE"
    log "  Image Tag: $IMAGE_TAG"
    log "  Dry Run: $DRY_RUN"
    log "  Verbose: $VERBOSE"
    log "  Wait for Ready: $WAIT_FOR_READY"

    # Validation phase
    log "Starting validation phase..."
    validate_prerequisites
    log_success "Validation phase completed"

    # Build phase
    log "Starting build phase..."
    build_and_push_image
    log_success "Build phase completed"

    # Deployment phase
    log "Starting deployment phase..."
    deploy_namespace
    deploy_application
    log_success "Deployment phase completed"

    # Wait phase
    if [[ "$WAIT_FOR_READY" == "true" ]]; then
        log "Starting wait phase..."
        wait_for_deployment
        log_success "Wait phase completed"
    fi

    # Verification phase
    log "Starting verification phase..."
    verify_deployment
    test_health_endpoints
    log_success "Verification phase completed"

    log_success "Phase 3: Application deployment completed successfully!"

    if [[ "$DRY_RUN" == "false" ]]; then
        log "Next steps:"
        log "1. Run Phase 4: ./scripts/deploy_phase4_monitoring.sh"
        log "2. Or run monitoring setup: helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack"
        log "3. Run validation: python3 scripts/validate_deployment.py"
    fi
}

# Error handling
trap 'log_error "Script failed at line $LINENO"' ERR

# Parse arguments and run main function
parse_args "$@"
main

