#!/bin/bash
# NBA MCP Synthesis - Production Health Check Script
# Comprehensive production health check for all services

set -e

# Configuration
NAMESPACE="nba-mcp-synthesis"
DEPLOYMENT_NAME="nba-mcp-synthesis"
SERVICE_NAME="nba-mcp-synthesis-service"
TIMEOUT=300

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

# Check EKS cluster health
check_eks_cluster() {
    log_info "Checking EKS cluster health..."

    if ! kubectl cluster-info > /dev/null 2>&1; then
        log_error "EKS cluster is not accessible"
        return 1
    fi

    # Check node status
    NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
    READY_NODES=$(kubectl get nodes --no-headers | grep "Ready" | wc -l)

    if [ "$NODE_COUNT" -eq "$READY_NODES" ] && [ "$NODE_COUNT" -gt 0 ]; then
        log_success "All $NODE_COUNT nodes are ready"
    else
        log_error "Not all nodes are ready ($READY_NODES/$NODE_COUNT)"
        return 1
    fi

    # Check node resources
    kubectl top nodes
}

# Check pod status
check_pod_status() {
    log_info "Checking pod status..."

    POD_COUNT=$(kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE --no-headers | wc -l)
    READY_PODS=$(kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE --no-headers | grep "Running" | wc -l)

    if [ "$POD_COUNT" -eq "$READY_PODS" ] && [ "$POD_COUNT" -gt 0 ]; then
        log_success "All $POD_COUNT pods are running and ready"
    else
        log_error "Not all pods are ready ($READY_PODS/$POD_COUNT)"
        kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE
        return 1
    fi

    # Show pod details
    kubectl get pods -l app=$DEPLOYMENT_NAME -n $NAMESPACE -o wide
}

# Check database connectivity
check_database_connectivity() {
    log_info "Checking database connectivity..."

    # Create a temporary pod to test database connectivity
    kubectl run db-test --image=postgres:13 --rm -it --restart=Never -n $NAMESPACE -- \
        psql -h nba-simulator-db.cluster-xyz.us-east-1.rds.amazonaws.com -U username -d nba_simulator -c "SELECT 1;" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        log_success "Database connectivity OK"
    else
        log_error "Database connectivity failed"
        return 1
    fi
}

# Check S3 access
check_s3_access() {
    log_info "Checking S3 access..."

    # Test S3 bucket access
    if aws s3 ls s3://nba-sim-raw-data-lake/ --max-items 1 > /dev/null 2>&1; then
        log_success "S3 access OK"
    else
        log_error "S3 access failed"
        return 1
    fi

    # Test books bucket access
    if aws s3 ls s3://nba-mcp-books/ --max-items 1 > /dev/null 2>&1; then
        log_success "S3 books bucket access OK"
    else
        log_error "S3 books bucket access failed"
        return 1
    fi
}

# Check secret validation
check_secret_validation() {
    log_info "Running secret validation..."

    # Run the secrets health monitor
    if python3 -m mcp_server.secrets_health_monitor --check > /dev/null 2>&1; then
        log_success "Secret validation OK"
    else
        log_error "Secret validation failed"
        return 1
    fi
}

# Check application health endpoints
check_application_health() {
    log_info "Checking application health endpoints..."

    # Set up port forward
    kubectl port-forward service/$SERVICE_NAME 8080:80 -n $NAMESPACE &
    PORT_FORWARD_PID=$!
    sleep 5

    # Test health endpoint
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log_success "Health endpoint OK"
    else
        log_error "Health endpoint failed"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        return 1
    fi

    # Test metrics endpoint
    if curl -f http://localhost:8080/metrics > /dev/null 2>&1; then
        log_success "Metrics endpoint OK"
    else
        log_error "Metrics endpoint failed"
        kill $PORT_FORWARD_PID 2>/dev/null || true
        return 1
    fi

    kill $PORT_FORWARD_PID 2>/dev/null || true
}

# Check HPA status
check_hpa_status() {
    log_info "Checking HPA status..."

    if kubectl get hpa nba-mcp-synthesis-hpa -n $NAMESPACE > /dev/null 2>&1; then
        kubectl get hpa nba-mcp-synthesis-hpa -n $NAMESPACE
        log_success "HPA status OK"
    else
        log_warning "HPA not found or not configured"
    fi
}

# Check recent events
check_recent_events() {
    log_info "Checking recent events..."

    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' --field-selector type!=Normal | tail -10
}

# Check resource usage
check_resource_usage() {
    log_info "Checking resource usage..."

    echo "Pod resource usage:"
    kubectl top pods -n $NAMESPACE

    echo ""
    echo "Node resource usage:"
    kubectl top nodes
}

# Check monitoring stack
check_monitoring_stack() {
    log_info "Checking monitoring stack..."

    # Check Prometheus
    if kubectl get pods -n monitoring -l app.kubernetes.io/name=prometheus --no-headers | grep "Running" > /dev/null 2>&1; then
        log_success "Prometheus is running"
    else
        log_warning "Prometheus is not running or not found"
    fi

    # Check Grafana
    if kubectl get pods -n monitoring -l app.kubernetes.io/name=grafana --no-headers | grep "Running" > /dev/null 2>&1; then
        log_success "Grafana is running"
    else
        log_warning "Grafana is not running or not found"
    fi

    # Check Alertmanager
    if kubectl get pods -n monitoring -l app.kubernetes.io/name=alertmanager --no-headers | grep "Running" > /dev/null 2>&1; then
        log_success "Alertmanager is running"
    else
        log_warning "Alertmanager is not running or not found"
    fi
}

# Main health check function
main() {
    log_info "Starting NBA MCP Synthesis production health check..."
    echo "=============================================="

    local failed_checks=0

    # Run all health checks
    check_eks_cluster || ((failed_checks++))
    echo ""

    check_pod_status || ((failed_checks++))
    echo ""

    check_database_connectivity || ((failed_checks++))
    echo ""

    check_s3_access || ((failed_checks++))
    echo ""

    check_secret_validation || ((failed_checks++))
    echo ""

    check_application_health || ((failed_checks++))
    echo ""

    check_hpa_status
    echo ""

    check_recent_events
    echo ""

    check_resource_usage
    echo ""

    check_monitoring_stack
    echo ""

    # Summary
    echo "=============================================="
    if [ $failed_checks -eq 0 ]; then
        log_success "All health checks passed! System is healthy."
        exit 0
    else
        log_error "$failed_checks health check(s) failed. System needs attention."
        exit 1
    fi
}

# Run main function
main "$@"


