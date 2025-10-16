#!/bin/bash

# NBA MCP Synthesis - Infrastructure Setup Script
# This script automates the infrastructure deployment for NBA MCP Synthesis

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
TERRAFORM_DIR="$PROJECT_ROOT/infrastructure/terraform"
LOG_FILE="/tmp/nba-mcp-infrastructure-setup.log"

# Default values
DRY_RUN=false
VERBOSE=false
SKIP_VALIDATION=false
AWS_REGION="us-east-1"
CLUSTER_NAME="nba-mcp-synthesis-prod"

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
NBA MCP Synthesis - Infrastructure Setup Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -d, --dry-run          Show what would be done without executing
    -v, --verbose          Enable verbose output
    -s, --skip-validation  Skip prerequisite validation
    -r, --region REGION   AWS region (default: us-east-1)
    -c, --cluster NAME    EKS cluster name (default: nba-mcp-synthesis-prod)
    -h, --help            Show this help message

EXAMPLES:
    $0                                    # Standard deployment
    $0 --dry-run                          # Preview changes
    $0 --verbose --region us-west-2        # Verbose output, different region
    $0 --skip-validation                  # Skip validation checks

DESCRIPTION:
    This script automates the infrastructure deployment for NBA MCP Synthesis:
    1. Validates AWS credentials and required tools
    2. Deploys Terraform infrastructure
    3. Configures kubectl access to EKS
    4. Installs required Helm charts
    5. Verifies infrastructure deployment

REQUIREMENTS:
    - AWS CLI configured with appropriate permissions
    - kubectl, helm, terraform installed
    - Docker installed and running
    - secrets.tfvars file configured

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
            -s|--skip-validation)
                SKIP_VALIDATION=true
                shift
                ;;
            -r|--region)
                AWS_REGION="$2"
                shift 2
                ;;
            -c|--cluster)
                CLUSTER_NAME="$2"
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
validate_aws_credentials() {
    log "Validating AWS credentials..."

    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured or invalid"
        log "Please run: aws configure"
        exit 1
    fi

    local account_id
    account_id=$(aws sts get-caller-identity --query Account --output text)
    log_success "AWS credentials valid (Account: $account_id)"
}

validate_required_tools() {
    log "Validating required tools..."

    local tools=("kubectl" "helm" "terraform" "docker" "aws")
    local missing_tools=()

    for tool in "${tools[@]}"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done

    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log "Please install missing tools and try again"
        exit 1
    fi

    log_success "All required tools are installed"
}

validate_terraform_config() {
    log "Validating Terraform configuration..."

    if [[ ! -f "$TERRAFORM_DIR/secrets.tfvars" ]]; then
        log_error "secrets.tfvars file not found in $TERRAFORM_DIR"
        log "Please create secrets.tfvars from secrets.tfvars.example"
        exit 1
    fi

    log_success "Terraform configuration validated"
}

validate_docker() {
    log "Validating Docker..."

    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running"
        log "Please start Docker and try again"
        exit 1
    fi

    log_success "Docker is running"
}

# Infrastructure deployment functions
deploy_terraform() {
    log "Deploying Terraform infrastructure..."

    cd "$TERRAFORM_DIR"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would execute terraform plan"
        terraform plan -var-file="secrets.tfvars" -var="aws_region=$AWS_REGION" -var="cluster_name=$CLUSTER_NAME"
        return 0
    fi

    # Initialize Terraform
    log "Initializing Terraform..."
    terraform init

    # Plan deployment
    log "Planning Terraform deployment..."
    terraform plan -var-file="secrets.tfvars" -var="aws_region=$AWS_REGION" -var="cluster_name=$CLUSTER_NAME"

    # Apply deployment
    log "Applying Terraform deployment..."
    terraform apply -var-file="secrets.tfvars" -var="aws_region=$AWS_REGION" -var="cluster_name=$CLUSTER_NAME" -auto-approve

    log_success "Terraform infrastructure deployed"
}

configure_kubectl() {
    log "Configuring kubectl access to EKS cluster..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would configure kubectl for cluster $CLUSTER_NAME"
        return 0
    fi

    aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME"

    # Verify cluster access
    if kubectl get nodes >/dev/null 2>&1; then
        log_success "kubectl configured and cluster accessible"
    else
        log_error "Failed to access EKS cluster"
        exit 1
    fi
}

install_helm_charts() {
    log "Installing required Helm charts..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would install Helm charts"
        return 0
    fi

    # Add Helm repositories
    log "Adding Helm repositories..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo add external-secrets https://charts.external-secrets.io
    helm repo update

    # Install External Secrets Operator
    log "Installing External Secrets Operator..."
    helm install external-secrets external-secrets/external-secrets \
        -n external-secrets-system --create-namespace \
        --wait --timeout=300s

    log_success "Helm charts installed"
}

verify_infrastructure() {
    log "Verifying infrastructure deployment..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: Would verify infrastructure"
        return 0
    fi

    # Check EKS cluster
    log "Checking EKS cluster status..."
    local cluster_status
    cluster_status=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$AWS_REGION" --query cluster.status --output text)

    if [[ "$cluster_status" == "ACTIVE" ]]; then
        log_success "EKS cluster is active"
    else
        log_error "EKS cluster is not active (Status: $cluster_status)"
        exit 1
    fi

    # Check nodes
    log "Checking node status..."
    local ready_nodes
    ready_nodes=$(kubectl get nodes --no-headers | grep -c "Ready" || echo "0")

    if [[ "$ready_nodes" -gt 0 ]]; then
        log_success "Found $ready_nodes ready nodes"
    else
        log_error "No ready nodes found"
        exit 1
    fi

    # Check External Secrets Operator
    log "Checking External Secrets Operator..."
    if kubectl get pods -n external-secrets-system | grep -q "Running"; then
        log_success "External Secrets Operator is running"
    else
        log_warning "External Secrets Operator may not be ready yet"
    fi

    log_success "Infrastructure verification completed"
}

# Main execution
main() {
    log "Starting NBA MCP Synthesis infrastructure setup..."
    log "Configuration:"
    log "  AWS Region: $AWS_REGION"
    log "  Cluster Name: $CLUSTER_NAME"
    log "  Dry Run: $DRY_RUN"
    log "  Verbose: $VERBOSE"
    log "  Skip Validation: $SKIP_VALIDATION"

    # Validation phase
    if [[ "$SKIP_VALIDATION" == "false" ]]; then
        log "Starting validation phase..."
        validate_aws_credentials
        validate_required_tools
        validate_terraform_config
        validate_docker
        log_success "Validation phase completed"
    else
        log_warning "Skipping validation phase"
    fi

    # Deployment phase
    log "Starting deployment phase..."
    deploy_terraform
    configure_kubectl
    install_helm_charts

    # Verification phase
    log "Starting verification phase..."
    verify_infrastructure

    log_success "Infrastructure setup completed successfully!"

    if [[ "$DRY_RUN" == "false" ]]; then
        log "Next steps:"
        log "1. Run secrets migration: python3 scripts/migrate_secrets_to_aws.py"
        log "2. Deploy application: kubectl apply -f k8s/"
        log "3. Set up monitoring: helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack"
        log "4. Run validation: python3 scripts/validate_deployment.py"
    fi
}

# Error handling
trap 'log_error "Script failed at line $LINENO"' ERR

# Parse arguments and run main function
parse_args "$@"
main

