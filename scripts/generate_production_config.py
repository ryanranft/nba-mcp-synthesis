#!/usr/bin/env python3

"""
NBA MCP Synthesis - Production Configuration Generator

This script generates customized Kubernetes manifests and Terraform configurations
for production deployment by prompting for required values and validating input.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import yaml

# Color codes for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

@dataclass
class ProductionConfig:
    """Production configuration data structure"""
    # AWS Configuration
    aws_account_id: str
    aws_region: str
    cluster_name: str

    # Domain Configuration
    domain_name: str
    certificate_arn: str

    # Database Configuration
    db_instance_class: str
    db_engine: str
    db_name: str
    db_backup_retention: int
    db_multi_az: bool

    # Monitoring Configuration
    grafana_admin_password: str
    pagerduty_service_key: str
    slack_webhook_url: str

    # Application Configuration
    namespace: str
    deployment_name: str
    service_name: str
    image_repository: str

    # Network Configuration
    vpc_cidr: str
    availability_zones: List[str]

    # Security Configuration
    enable_network_policies: bool
    enable_pod_security_standards: bool

class ConfigGenerator:
    """Main configuration generator class"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.config: Optional[ProductionConfig] = None
        self.project_root = Path(__file__).parent.parent
        self.templates_dir = self.project_root / "templates"
        self.output_dir = self.project_root / "generated-config"

    def log(self, message: str, color: str = Colors.BLUE):
        """Log message with color"""
        print(f"{color}[{self.__class__.__name__}]{Colors.NC} {message}")

    def log_success(self, message: str):
        """Log success message"""
        self.log(f"✓ {message}", Colors.GREEN)

    def log_warning(self, message: str):
        """Log warning message"""
        self.log(f"⚠ {message}", Colors.YELLOW)

    def log_error(self, message: str):
        """Log error message"""
        self.log(f"✗ {message}", Colors.RED)

    def validate_aws_account_id(self, account_id: str) -> bool:
        """Validate AWS account ID format"""
        return bool(re.match(r'^\d{12}$', account_id))

    def validate_domain_name(self, domain: str) -> bool:
        """Validate domain name format"""
        pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(pattern, domain))

    def validate_certificate_arn(self, arn: str) -> bool:
        """Validate AWS Certificate Manager ARN format"""
        pattern = r'^arn:aws:acm:[a-z0-9-]+:\d{12}:certificate/[a-f0-9-]+$'
        return bool(re.match(pattern, arn))

    def validate_url(self, url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))

    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'\d', password):
            return False
        return True

    def prompt_with_validation(self, prompt: str, validator_func, error_msg: str,
                              required: bool = True, default: Optional[str] = None) -> str:
        """Prompt user for input with validation"""
        while True:
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    user_input = default
            else:
                user_input = input(f"{prompt}: ").strip()

            if not user_input and required:
                self.log_error("This field is required")
                continue

            if not user_input and not required:
                return ""

            if validator_func(user_input):
                return user_input
            else:
                self.log_error(error_msg)

    def collect_configuration(self) -> ProductionConfig:
        """Collect configuration from user input"""
        self.log("Collecting production configuration...")

        # AWS Configuration
        self.log("\n=== AWS Configuration ===", Colors.CYAN)
        aws_account_id = self.prompt_with_validation(
            "AWS Account ID (12 digits)",
            self.validate_aws_account_id,
            "AWS Account ID must be exactly 12 digits"
        )

        aws_region = self.prompt_with_validation(
            "AWS Region",
            lambda x: x in ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'],
            "Please enter a valid AWS region",
            default="us-east-1"
        )

        cluster_name = self.prompt_with_validation(
            "EKS Cluster Name",
            lambda x: len(x) > 0 and re.match(r'^[a-zA-Z0-9-]+$', x),
            "Cluster name must contain only alphanumeric characters and hyphens",
            default="nba-mcp-synthesis-prod"
        )

        # Domain Configuration
        self.log("\n=== Domain Configuration ===", Colors.CYAN)
        domain_name = self.prompt_with_validation(
            "Domain Name (e.g., nba-mcp-synthesis.example.com)",
            self.validate_domain_name,
            "Please enter a valid domain name"
        )

        certificate_arn = self.prompt_with_validation(
            "AWS Certificate Manager ARN",
            self.validate_certificate_arn,
            "Please enter a valid ACM certificate ARN"
        )

        # Database Configuration
        self.log("\n=== Database Configuration ===", Colors.CYAN)
        db_instance_class = self.prompt_with_validation(
            "RDS Instance Class",
            lambda x: x.startswith('db.'),
            "Instance class must start with 'db.'",
            default="db.t3.medium"
        )

        db_engine = self.prompt_with_validation(
            "Database Engine",
            lambda x: x in ['postgres', 'mysql'],
            "Please enter 'postgres' or 'mysql'",
            default="postgres"
        )

        db_name = self.prompt_with_validation(
            "Database Name",
            lambda x: len(x) > 0 and re.match(r'^[a-zA-Z0-9_]+$', x),
            "Database name must contain only alphanumeric characters and underscores",
            default="nba_simulator"
        )

        db_backup_retention = int(self.prompt_with_validation(
            "Backup Retention (days)",
            lambda x: x.isdigit() and 1 <= int(x) <= 35,
            "Backup retention must be between 1 and 35 days",
            default="7"
        ))

        db_multi_az = self.prompt_with_validation(
            "Enable Multi-AZ deployment (y/n)",
            lambda x: x.lower() in ['y', 'n', 'yes', 'no'],
            "Please enter 'y' or 'n'",
            default="y"
        ).lower() in ['y', 'yes']

        # Monitoring Configuration
        self.log("\n=== Monitoring Configuration ===", Colors.CYAN)
        grafana_admin_password = self.prompt_with_validation(
            "Grafana Admin Password",
            self.validate_password,
            "Password must be at least 8 characters with uppercase, lowercase, and numbers"
        )

        pagerduty_service_key = self.prompt_with_validation(
            "PagerDuty Service Key",
            lambda x: len(x) > 0,
            "PagerDuty service key is required"
        )

        slack_webhook_url = self.prompt_with_validation(
            "Slack Webhook URL",
            self.validate_url,
            "Please enter a valid HTTPS URL"
        )

        # Application Configuration
        self.log("\n=== Application Configuration ===", Colors.CYAN)
        namespace = self.prompt_with_validation(
            "Kubernetes Namespace",
            lambda x: len(x) > 0 and re.match(r'^[a-z0-9-]+$', x),
            "Namespace must contain only lowercase letters, numbers, and hyphens",
            default="nba-mcp-synthesis"
        )

        deployment_name = self.prompt_with_validation(
            "Deployment Name",
            lambda x: len(x) > 0 and re.match(r'^[a-z0-9-]+$', x),
            "Deployment name must contain only lowercase letters, numbers, and hyphens",
            default="nba-mcp-synthesis"
        )

        service_name = self.prompt_with_validation(
            "Service Name",
            lambda x: len(x) > 0 and re.match(r'^[a-z0-9-]+$', x),
            "Service name must contain only lowercase letters, numbers, and hyphens",
            default="nba-mcp-synthesis-service"
        )

        image_repository = self.prompt_with_validation(
            "ECR Repository Name",
            lambda x: len(x) > 0 and re.match(r'^[a-z0-9-]+$', x),
            "Repository name must contain only lowercase letters, numbers, and hyphens",
            default="nba-mcp-synthesis"
        )

        # Network Configuration
        self.log("\n=== Network Configuration ===", Colors.CYAN)
        vpc_cidr = self.prompt_with_validation(
            "VPC CIDR Block",
            lambda x: re.match(r'^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$', x),
            "Please enter a valid CIDR block (e.g., 10.0.0.0/16)",
            default="10.0.0.0/16"
        )

        availability_zones_input = self.prompt_with_validation(
            "Availability Zones (comma-separated)",
            lambda x: len(x.split(',')) >= 2,
            "Please enter at least 2 availability zones",
            default=f"{aws_region}a,{aws_region}b,{aws_region}c"
        )
        availability_zones = [az.strip() for az in availability_zones_input.split(',')]

        # Security Configuration
        self.log("\n=== Security Configuration ===", Colors.CYAN)
        enable_network_policies = self.prompt_with_validation(
            "Enable Network Policies (y/n)",
            lambda x: x.lower() in ['y', 'n', 'yes', 'no'],
            "Please enter 'y' or 'n'",
            default="y"
        ).lower() in ['y', 'yes']

        enable_pod_security_standards = self.prompt_with_validation(
            "Enable Pod Security Standards (y/n)",
            lambda x: x.lower() in ['y', 'n', 'yes', 'no'],
            "Please enter 'y' or 'n'",
            default="y"
        ).lower() in ['y', 'yes']

        return ProductionConfig(
            aws_account_id=aws_account_id,
            aws_region=aws_region,
            cluster_name=cluster_name,
            domain_name=domain_name,
            certificate_arn=certificate_arn,
            db_instance_class=db_instance_class,
            db_engine=db_engine,
            db_name=db_name,
            db_backup_retention=db_backup_retention,
            db_multi_az=db_multi_az,
            grafana_admin_password=grafana_admin_password,
            pagerduty_service_key=pagerduty_service_key,
            slack_webhook_url=slack_webhook_url,
            namespace=namespace,
            deployment_name=deployment_name,
            service_name=service_name,
            image_repository=image_repository,
            vpc_cidr=vpc_cidr,
            availability_zones=availability_zones,
            enable_network_policies=enable_network_policies,
            enable_pod_security_standards=enable_pod_security_standards
        )

    def generate_terraform_vars(self) -> str:
        """Generate Terraform variables file"""
        tf_vars = f"""# NBA MCP Synthesis - Terraform Variables
# Generated by production configuration generator

# AWS Configuration
aws_account_id = "{self.config.aws_account_id}"
aws_region = "{self.config.aws_region}"
cluster_name = "{self.config.cluster_name}"

# Domain Configuration
domain_name = "{self.config.domain_name}"
certificate_arn = "{self.config.certificate_arn}"

# Database Configuration
db_instance_class = "{self.config.db_instance_class}"
db_engine = "{self.config.db_engine}"
db_name = "{self.config.db_name}"
db_backup_retention = {self.config.db_backup_retention}
db_multi_az = {str(self.config.db_multi_az).lower()}

# Network Configuration
vpc_cidr = "{self.config.vpc_cidr}"
availability_zones = {json.dumps(self.config.availability_zones)}

# Security Configuration
enable_network_policies = {str(self.config.enable_network_policies).lower()}
enable_pod_security_standards = {str(self.config.enable_pod_security_standards).lower()}

# Monitoring Configuration
grafana_admin_password = "{self.config.grafana_admin_password}"
pagerduty_service_key = "{self.config.pagerduty_service_key}"
slack_webhook_url = "{self.config.slack_webhook_url}"
"""
        return tf_vars

    def generate_kubernetes_manifests(self) -> Dict[str, str]:
        """Generate Kubernetes manifests with placeholders replaced"""
        manifests = {}

        # Deployment manifest
        deployment_manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {self.config.deployment_name}
  namespace: {self.config.namespace}
  labels:
    app: {self.config.deployment_name}
    environment: production
    project: nba-mcp-synthesis
    sport: nba
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: {self.config.deployment_name}
  template:
    metadata:
      labels:
        app: {self.config.deployment_name}
        environment: production
        project: nba-mcp-synthesis
        sport: nba
    spec:
      # Init container to load secrets
      initContainers:
        - name: secrets-loader
          image: {self.config.aws_account_id}.dkr.ecr.{self.config.aws_region}.amazonaws.com/{self.config.image_repository}:latest
          command: ["/app/entrypoint.sh"]
          env:
            - name: PROJECT_NAME
              value: "nba-mcp-synthesis"
            - name: SPORT_NAME
              value: "NBA"
            - name: NBA_MCP_CONTEXT
              value: "production"
          envFrom:
            - secretRef:
                name: nba-mcp-synthesis-secrets
          volumeMounts:
            - name: shared-secrets
              mountPath: /shared
            - name: init-config
              mountPath: /app
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"

      # Main application container
      containers:
        - name: {self.config.deployment_name}
          image: {self.config.aws_account_id}.dkr.ecr.{self.config.aws_region}.amazonaws.com/{self.config.image_repository}:latest
          ports:
            - containerPort: 8000
              name: http
            - containerPort: 9090
              name: metrics
          env:
            - name: PROJECT_NAME
              value: "nba-mcp-synthesis"
            - name: SPORT_NAME
              value: "NBA"
            - name: NBA_MCP_CONTEXT
              value: "production"
            - name: PYTHONUNBUFFERED
              value: "1"
          envFrom:
            - secretRef:
                name: nba-mcp-synthesis-secrets
          volumeMounts:
            - name: shared-secrets
              mountPath: /shared
            - name: app-config
              mountPath: /app/config
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1000m"

      # Volumes
      volumes:
        - name: shared-secrets
          emptyDir: {{}}
"""
        manifests['deployment.yaml'] = deployment_manifest

        # Service manifest
        service_manifest = f"""apiVersion: v1
kind: Service
metadata:
  name: {self.config.service_name}
  namespace: {self.config.namespace}
  labels:
    app: {self.config.deployment_name}
    environment: production
    project: nba-mcp-synthesis
    sport: nba
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 8000
      protocol: TCP
      name: http
    - port: 9090
      targetPort: 9090
      protocol: TCP
      name: metrics
  selector:
    app: {self.config.deployment_name}
"""
        manifests['service.yaml'] = service_manifest

        # Ingress manifest
        ingress_manifest = f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {self.config.deployment_name}-ingress
  namespace: {self.config.namespace}
  labels:
    app: {self.config.deployment_name}
    environment: production
    project: nba-mcp-synthesis
    sport: nba
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/certificate-arn: {self.config.certificate_arn}
    alb.ingress.kubernetes.io/ssl-policy: ELBSecurityPolicy-TLS-1-2-2017-01
    alb.ingress.kubernetes.io/listen-ports: '[{{"HTTP": 80}}, {{"HTTPS": 443}}]'
    alb.ingress.kubernetes.io/load-balancer-attributes: routing.http2.enabled=true
    alb.ingress.kubernetes.io/target-group-attributes: stickiness.enabled=true,stickiness.lb_cookie.duration_seconds=3600
spec:
  tls:
    - hosts:
        - {self.config.domain_name}
      secretName: {self.config.deployment_name}-tls
  rules:
    - host: {self.config.domain_name}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {self.config.service_name}
                port:
                  number: 80
          - path: /metrics
            pathType: Prefix
            backend:
              service:
                name: {self.config.service_name}
                port:
                  number: 9090
"""
        manifests['ingress.yaml'] = ingress_manifest

        return manifests

    def save_configuration(self):
        """Save generated configuration files"""
        self.log("Saving generated configuration...")

        # Create output directory
        self.output_dir.mkdir(exist_ok=True)

        # Save Terraform variables
        tf_vars_path = self.output_dir / "secrets.tfvars"
        with open(tf_vars_path, 'w') as f:
            f.write(self.generate_terraform_vars())
        self.log_success(f"Saved Terraform variables to {tf_vars_path}")

        # Save Kubernetes manifests
        manifests = self.generate_kubernetes_manifests()
        for filename, content in manifests.items():
            manifest_path = self.output_dir / filename
            with open(manifest_path, 'w') as f:
                f.write(content)
            self.log_success(f"Saved Kubernetes manifest to {manifest_path}")

        # Save configuration summary
        config_path = self.output_dir / "configuration.json"
        with open(config_path, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)
        self.log_success(f"Saved configuration summary to {config_path}")

    def display_summary(self):
        """Display configuration summary"""
        self.log("\n=== Configuration Summary ===", Colors.PURPLE)
        self.log(f"AWS Account ID: {self.config.aws_account_id}")
        self.log(f"AWS Region: {self.config.aws_region}")
        self.log(f"Cluster Name: {self.config.cluster_name}")
        self.log(f"Domain Name: {self.config.domain_name}")
        self.log(f"Namespace: {self.config.namespace}")
        self.log(f"Database: {self.config.db_engine} ({self.config.db_instance_class})")
        self.log(f"Network Policies: {'Enabled' if self.config.enable_network_policies else 'Disabled'}")
        self.log(f"Pod Security Standards: {'Enabled' if self.config.enable_pod_security_standards else 'Disabled'}")

        self.log("\n=== Generated Files ===", Colors.PURPLE)
        self.log(f"Terraform Variables: {self.output_dir}/secrets.tfvars")
        self.log(f"Kubernetes Manifests: {self.output_dir}/*.yaml")
        self.log(f"Configuration Summary: {self.output_dir}/configuration.json")

        self.log("\n=== Next Steps ===", Colors.PURPLE)
        self.log("1. Copy secrets.tfvars to infrastructure/terraform/")
        self.log("2. Copy Kubernetes manifests to k8s/")
        self.log("3. Run infrastructure setup: ./scripts/setup_infrastructure.sh")
        self.log("4. Deploy application: kubectl apply -f k8s/")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Generate production configuration for NBA MCP Synthesis')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-o', '--output-dir', help='Output directory for generated files')

    args = parser.parse_args()

    generator = ConfigGenerator(verbose=args.verbose)

    try:
        # Collect configuration
        generator.config = generator.collect_configuration()

        # Set custom output directory if provided
        if args.output_dir:
            generator.output_dir = Path(args.output_dir)

        # Save configuration
        generator.save_configuration()

        # Display summary
        generator.display_summary()

        generator.log_success("Configuration generation completed successfully!")

    except KeyboardInterrupt:
        generator.log_warning("Configuration generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        generator.log_error(f"Configuration generation failed: {e}")
        if generator.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

