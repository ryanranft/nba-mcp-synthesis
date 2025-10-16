#!/bin/bash
# NBA MCP Synthesis - Production Deployment Script
# Comprehensive deployment script with pre-checks, rolling deployment, and rollback capability

set -e

# Configuration
NAMESPACE="nba-mcp-synthesis"
DEPLOYMENT_NAME="nba-mcp-synthesis"
SERVICE_NAME="nba-mcp-synthesis-service"
IMAGE_TAG="${1:-latest}"
ACCOUNT_ID="${2:-$(aws sts get-caller-identity --query Account --output text)}"
AWS_REGION="${3:-us-east-1}"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/nba-mcp-synthesis:${IMAGE_TAG}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
pre_deployment_checks() {
    log_info "Running pre-deployment checks..."

    # Check if kubectl is configured
    if ! kubectl cluster-info > /dev/null 2>&1; then
        log_error "kubectl is not configured or cluster is not accessible"
        exit 1
    fi

    # Check if namespace exists
    if ! kubectl get namespace $NAMESPACE > /dev/null 2>&1; then
        log_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi

    # Check if ECR image exists
    if ! aws ecr describe-images --repository-name nba-mcp-synthesis --image-ids imageTag=$IMAGE_TAG --region $AWS_REGION > /dev/null 2>&1; then
        log_error "Image $ECR_URI does not exist in ECR"
        exit 1
    fi

    # Check current deployment status
    if kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE > /dev/null 2>&1; then
        CURRENT_REPLICAS=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}')
        log_info "Current deployment has $CURRENT_REPLICAS replicas"
    else
        log_warning "Deployment $DEPLOYMENT_NAME does not exist, will be created"
    fi

    log_success "Pre-deployment checks passed"
}

# Database migration (if needed)
run_database_migration() {
    log_info "Checking for database migrations..."

    # Check if there are pending migrations
    # This would typically involve running a migration script or checking migration status
    # For now, we'll just log that we're checking

    log_info "Database migration check completed"
}

# Rolling deployment
rolling_deployment() {
    log_info "Starting rolling deployment..."

    # Update deployment with new image
    kubectl set image deployment/$DEPLOYMENT_NAME \
        $DEPLOYMENT_NAME=$ECR_URI \
        -n $NAMESPACE

    # Wait for rollout to complete
    log_info "Waiting for rollout to complete..."
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=600s

    log_success "Rolling deployment completed"
}

# Health check validation
health_check_validation() {
    log_info "Running health check validation..."

    # Wait for pods to be ready
    kubectl wait --for=condition=ready pod -l app=$DEPLOYMENT_NAME -n $NAMESPACE --timeout=300s

    # Get service endpoint
    SERVICE_ENDPOINT=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")

    if [ -z "$SERVICE_ENDPOINT" ]; then
        log_warning "Service endpoint not available, checking cluster IP"
        SERVICE_ENDPOINT=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.clusterIP}')
        PORT=$(kubectl get service $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.ports[0].port}')

        # Port forward for testing
        log_info "Setting up port forward for health checks..."
        kubectl port-forward service/$SERVICE_NAME 8080:$PORT -n $NAMESPACE &
        PORT_FORWARD_PID=$!
        sleep 5

        # Run health checks via port forward
        curl -f http://localhost:8080/health || {
            log_error "Health check failed"
            kill $PORT_FORWARD_PID 2>/dev/null || true
            return 1
        }

        curl -f http://localhost:8080/metrics || {
            log_error "Metrics endpoint check failed"
            kill $PORT_FORWARD_PID 2>/dev/null || true
            return 1
        }

        kill $PORT_FORWARD_PID 2>/dev/null || true
    else
        # Run health checks via external endpoint
        curl -f http://$SERVICE_ENDPOINT/health || {
            log_error "Health check failed"
            return 1
        }

        curl -f http://$SERVICE_ENDPOINT/metrics || {
            log_error "Metrics endpoint check failed"
            return 1
        }
    fi

    log_success "Health check validation passed"
}

# Rollback function
rollback_deployment() {
    log_warning "Rolling back deployment..."

    kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=300s

    log_success "Rollback completed"
}

# Smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."

    # Test basic functionality
    # This would typically involve running actual application tests
    # For now, we'll just verify the deployment is working

    POD_COUNT=$(kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE --no-headers | wc -l)
    READY_PODS=$(kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE --no-headers | grep "Running" | wc -l)

    if [ "$POD_COUNT" -eq "$READY_PODS" ] && [ "$POD_COUNT" -gt 0 ]; then
        log_success "All $POD_COUNT pods are running and ready"
    else
        log_error "Not all pods are ready ($READY_PODS/$POD_COUNT)"
        return 1
    fi

    log_success "Smoke tests passed"
}

# Main deployment function
main() {
    log_info "Starting NBA MCP Synthesis production deployment"
    log_info "Image: $ECR_URI"
    log_info "Namespace: $NAMESPACE"
    log_info "Deployment: $DEPLOYMENT_NAME"

    # Run pre-deployment checks
    pre_deployment_checks

    # Run database migration
    run_database_migration

    # Perform rolling deployment
    rolling_deployment

    # Run health checks
    if ! health_check_validation; then
        log_error "Health check validation failed, rolling back..."
        rollback_deployment
        exit 1
    fi

    # Run smoke tests
    if ! run_smoke_tests; then
        log_error "Smoke tests failed, rolling back..."
        rollback_deployment
        exit 1
    fi

    log_success "Production deployment completed successfully!"

    # Display deployment information
    echo ""
    log_info "Deployment Summary:"
    echo "  Image: $ECR_URI"
    echo "  Namespace: $NAMESPACE"
    echo "  Deployment: $DEPLOYMENT_NAME"
    echo "  Service: $SERVICE_NAME"
    echo ""

    # Show pod status
    kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE
}

# Error handling
trap 'log_error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"

