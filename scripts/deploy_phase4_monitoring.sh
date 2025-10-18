#!/bin/bash

# NBA MCP Synthesis - Phase 4: Monitoring Setup
# This script sets up the monitoring stack with Prometheus, Grafana, and Alertmanager

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
HELM_DIR="$PROJECT_ROOT/infrastructure/helm"
LOG_FILE="/tmp/nba-mcp-phase4-monitoring.log"

# Default values
DRY_RUN=false
VERBOSE=false
NAMESPACE="monitoring"
GRAFANA_PASSWORD=""
PAGERDUTY_KEY=""
SLACK_WEBHOOK=""

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
NBA MCP Synthesis - Phase 4: Monitoring Setup

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -d, --dry-run          Show what would be done without executing
    -v, --verbose          Enable verbose output
    -n, --namespace NS     Kubernetes namespace (default: monitoring)
    -p, --grafana-password PASSWORD  Grafana admin password
    --pagerduty-key KEY    PagerDuty service key
    --slack-webhook URL    Slack webhook URL
    -h, --help            Show this help message

EXAMPLES:
    $0                                    # Standard setup
    $0 --dry-run                          # Preview setup
    $0 --grafana-password "secure123"      # Set Grafana password
    $0 --pagerduty-key "key123" --slack-webhook "https://hooks.slack.com/..."  # Configure alerting

DESCRIPTION:
    This script sets up the monitoring stack:
    1. Installs Prometheus stack (Prometheus, Grafana, Alertmanager)
    2. Configures NBA MCP Synthesis dashboards
    3. Sets up alerting rules
    4. Configures PagerDuty and Slack integrations
    5. Verifies monitoring stack health

REQUIREMENTS:
    - EKS cluster running (from Phase 1)
    - Application deployed (from Phase 3)
    - Helm installed and configured

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
            -p|--grafana-password)
                GRAFANA_PASSWORD="$2"
                shift 2
                ;;
            --pagerduty-key)
                PAGERDUTY_KEY="$2"
                shift 2
                ;;
            --slack-webhook)
                SLACK_WEBHOOK="$2"
                shift 2
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
        exit 1
    fi

    log_success "kubectl access verified"

    # Check Helm
    if ! command -v helm >/dev/null 2>&1; then
        log_error "Helm not installed"
        log "Please install Helm and try again"
        exit 1
    fi

    log_success "Helm is installed"

    # Check application is deployed
    if ! kubectl get deployment nba-mcp-synthesis -n nba-mcp-synthesis >/dev/null 2>&1; then
        log_error "NBA MCP Synthesis application not found"
        log "Please run Phase 3 first: ./scripts/deploy_phase3_application.sh"
        exit 1
    fi

    log_success "Application deployment verified"

    # Check Helm values file
    if [[ ! -f "$HELM_DIR/prometheus-values.yaml" ]]; then
        log_error "Prometheus values file not found: $HELM_DIR/prometheus-values.yaml"
        exit 1
    fi

    log_success "Helm configuration validated"
}

# Configuration functions
configure_values() {
    log "Configuring Helm values..."

    local values_file="$HELM_DIR/prometheus-values.yaml"
    local temp_values="/tmp/prometheus-values.yaml"

    # Copy original values file
    cp "$values_file" "$temp_values"

    # Update Grafana password if provided
    if [[ -n "$GRAFANA_PASSWORD" ]]; then
        log "Setting Grafana admin password..."
        sed -i.bak "s/admin123/$GRAFANA_PASSWORD/g" "$temp_values"
    fi

    # Update PagerDuty key if provided
    if [[ -n "$PAGERDUTY_KEY" ]]; then
        log "Setting PagerDuty service key..."
        sed -i.bak "s/YOUR_PAGERDUTY_SERVICE_KEY/$PAGERDUTY_KEY/g" "$temp_values"
    fi

    # Update Slack webhook if provided
    if [[ -n "$SLACK_WEBHOOK" ]]; then
        log "Setting Slack webhook URL..."
        sed -i.bak "s|YOUR_SLACK_WEBHOOK_URL|$SLACK_WEBHOOK|g" "$temp_values"
    fi

    log_success "Helm values configured"
}

# Helm functions
add_helm_repositories() {
    log "Adding Helm repositories..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would add Helm repositories"
        return 0
    fi

    # Add Prometheus community repository
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

    # Update repositories
    helm repo update

    log_success "Helm repositories added and updated"
}

install_prometheus_stack() {
    log "Installing Prometheus stack..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would install Prometheus stack"
        return 0
    fi

    local temp_values="/tmp/prometheus-values.yaml"

    # Install Prometheus stack
    helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
        -n "$NAMESPACE" --create-namespace \
        -f "$temp_values" \
        --wait --timeout=600s

    log_success "Prometheus stack installed"

    # Clean up temporary values file
    rm -f "$temp_values" "$temp_values.bak"
}

# Verification functions
verify_monitoring_stack() {
    log "Verifying monitoring stack..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would verify monitoring stack"
        return 0
    fi

    # Check Prometheus
    if kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=prometheus | grep -q "Running"; then
        log_success "Prometheus is running"
    else
        log_warning "Prometheus may not be ready yet"
    fi

    # Check Grafana
    if kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=grafana | grep -q "Running"; then
        log_success "Grafana is running"
    else
        log_warning "Grafana may not be ready yet"
    fi

    # Check Alertmanager
    if kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=alertmanager | grep -q "Running"; then
        log_success "Alertmanager is running"
    else
        log_warning "Alertmanager may not be ready yet"
    fi

    # Check ServiceMonitor
    if kubectl get servicemonitor -n nba-mcp-synthesis | grep -q "nba-mcp-synthesis"; then
        log_success "ServiceMonitor is configured"
    else
        log_warning "ServiceMonitor may not be ready yet"
    fi
}

test_monitoring_endpoints() {
    log "Testing monitoring endpoints..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would test monitoring endpoints"
        return 0
    fi

    # Test Prometheus
    log "Testing Prometheus endpoint..."
    kubectl port-forward service/kube-prometheus-stack-prometheus 9090:9090 -n "$NAMESPACE" &
    local prom_pf_pid=$!
    sleep 3

    if curl -f http://localhost:9090/api/v1/query?query=up >/dev/null 2>&1; then
        log_success "Prometheus endpoint is responding"
    else
        log_warning "Prometheus endpoint may not be ready yet"
    fi

    kill $prom_pf_pid 2>/dev/null || true

    # Test Grafana
    log "Testing Grafana endpoint..."
    kubectl port-forward service/kube-prometheus-stack-grafana 3000:80 -n "$NAMESPACE" &
    local graf_pf_pid=$!
    sleep 3

    if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
        log_success "Grafana endpoint is responding"
    else
        log_warning "Grafana endpoint may not be ready yet"
    fi

    kill $graf_pf_pid 2>/dev/null || true

    log_success "Monitoring endpoint testing completed"
}

# Dashboard functions
verify_dashboards() {
    log "Verifying NBA MCP Synthesis dashboards..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would verify dashboards"
        return 0
    fi

    # Check if NBA MCP dashboard is configured
    if kubectl get configmap -n "$NAMESPACE" | grep -q "nba-mcp-synthesis"; then
        log_success "NBA MCP Synthesis dashboard configuration found"
    else
        log_warning "NBA MCP Synthesis dashboard may not be configured yet"
    fi
}

# Alerting functions
test_alerting() {
    log "Testing alerting configuration..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would test alerting"
        return 0
    fi

    # Check alerting rules
    kubectl port-forward service/kube-prometheus-stack-prometheus 9090:9090 -n "$NAMESPACE" &
    local prom_pf_pid=$!
    sleep 3

    if curl -f "http://localhost:9090/api/v1/rules" | grep -q "nba-mcp-synthesis"; then
        log_success "NBA MCP Synthesis alerting rules are active"
    else
        log_warning "NBA MCP Synthesis alerting rules may not be active yet"
    fi

    kill $prom_pf_pid 2>/dev/null || true

    log_success "Alerting configuration testing completed"
}

# Main execution
main() {
    log "Starting NBA MCP Synthesis Phase 4: Monitoring Setup..."
    log "Configuration:"
    log "  Namespace: $NAMESPACE"
    log "  Dry Run: $DRY_RUN"
    log "  Verbose: $VERBOSE"
    log "  Grafana Password: ${GRAFANA_PASSWORD:+[SET]}"
    log "  PagerDuty Key: ${PAGERDUTY_KEY:+[SET]}"
    log "  Slack Webhook: ${SLACK_WEBHOOK:+[SET]}"

    # Validation phase
    log "Starting validation phase..."
    validate_prerequisites
    log_success "Validation phase completed"

    # Configuration phase
    log "Starting configuration phase..."
    configure_values
    log_success "Configuration phase completed"

    # Installation phase
    log "Starting installation phase..."
    add_helm_repositories
    install_prometheus_stack
    log_success "Installation phase completed"

    # Verification phase
    log "Starting verification phase..."
    verify_monitoring_stack
    test_monitoring_endpoints
    verify_dashboards
    test_alerting
    log_success "Verification phase completed"

    log_success "Phase 4: Monitoring setup completed successfully!"

    if [[ "$DRY_RUN" == "false" ]]; then
        log "Next steps:"
        log "1. Access Grafana: kubectl port-forward service/kube-prometheus-stack-grafana 3000:80 -n $NAMESPACE"
        log "2. Access Prometheus: kubectl port-forward service/kube-prometheus-stack-prometheus 9090:9090 -n $NAMESPACE"
        log "3. Run validation: python3 scripts/validate_deployment.py"
        log "4. Test alerting: Check PagerDuty and Slack integrations"
    fi
}

# Error handling
trap 'log_error "Script failed at line $LINENO"' ERR

# Parse arguments and run main function
parse_args "$@"
main


