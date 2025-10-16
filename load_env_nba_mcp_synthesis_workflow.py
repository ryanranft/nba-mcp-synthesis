#!/usr/bin/env python3
"""
NBA MCP Synthesis - Workflow Environment Loader
Loads all secrets from centralized location into environment variables
Enhanced with validation, health checks, and Slack integration
"""
import os
import sys
import time
import json
import hashlib
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/nba_mcp_synthesis_workflow.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecretsValidator:
    """Validates secret formats and values"""

    @staticmethod
    def validate_api_key(key: str, service: str) -> bool:
        """Validate API key format based on service"""
        if not key or len(key.strip()) == 0:
            return False

        key = key.strip()

        if service.upper() == 'GOOGLE':
            return key.startswith('AIza') and len(key) >= 30
        elif service.upper() == 'OPENAI':
            return key.startswith('sk-') and len(key) >= 40
        elif service.upper() == 'ANTHROPIC':
            return key.startswith('sk-ant-') and len(key) >= 40
        elif service.upper() == 'DEEPSEEK':
            return key.startswith('sk-') and len(key) >= 30
        elif service.upper() == 'LINEAR':
            return key.startswith('lin_api_') and len(key) >= 20

        return len(key) >= 8  # Generic validation

    @staticmethod
    def validate_webhook_url(url: str) -> bool:
        """Validate webhook URL format"""
        if not url:
            return False
        return url.startswith('https://hooks.slack.com/') or url.startswith('https://discord.com/api/webhooks/')

    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format"""
        if not uuid_str:
            return False
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, uuid_str.lower()))

class HealthChecker:
    """Performs health checks on loaded secrets"""

    def __init__(self, secrets: Dict[str, str]):
        self.secrets = secrets
        self.health_status = {}

    def check_api_connectivity(self) -> Dict[str, bool]:
        """Check API connectivity for loaded keys"""
        results = {}

        # Google API check
        if 'GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW' in self.secrets:
            try:
                # Simple validation request
                response = requests.get(
                    'https://generativelanguage.googleapis.com/v1beta/models',
                    params={'key': self.secrets['GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW']},
                    timeout=5
                )
                results['google_api'] = response.status_code == 200
            except:
                results['google_api'] = False

        # OpenAI API check
        if 'OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW' in self.secrets:
            try:
                response = requests.get(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {self.secrets["OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW"]}'},
                    timeout=5
                )
                results['openai_api'] = response.status_code == 200
            except:
                results['openai_api'] = False

        # Slack webhook check
        if 'SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW' in self.secrets:
            try:
                response = requests.post(
                    self.secrets['SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW'],
                    json={'text': 'Health check test'},
                    timeout=5
                )
                results['slack_webhook'] = response.status_code == 200
            except:
                results['slack_webhook'] = False

        return results

    def check_secret_strength(self) -> Dict[str, bool]:
        """Check secret strength and format"""
        results = {}

        for var_name, value in self.secrets.items():
            if 'API_KEY' in var_name:
                service = var_name.split('_')[0]
                results[var_name] = SecretsValidator.validate_api_key(value, service)
            elif 'WEBHOOK_URL' in var_name:
                results[var_name] = SecretsValidator.validate_webhook_url(value)
            elif 'TEAM_ID' in var_name or 'PROJECT_ID' in var_name:
                results[var_name] = SecretsValidator.validate_uuid(value)
            else:
                results[var_name] = len(value) >= 8

        return results

    def get_health_summary(self) -> Dict[str, Any]:
        """Get comprehensive health summary"""
        connectivity = self.check_api_connectivity()
        strength = self.check_secret_strength()

        return {
            'timestamp': datetime.now().isoformat(),
            'total_secrets': len(self.secrets),
            'connectivity_checks': connectivity,
            'strength_checks': strength,
            'overall_health': all(connectivity.values()) and all(strength.values()),
            'issues': [
                f"{service}: {'OK' if status else 'FAILED'}"
                for service, status in {**connectivity, **strength}.items()
            ]
        }

class SlackNotifier:
    """Handles Slack notifications for secrets loading"""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW')
        self.enabled = bool(self.webhook_url)

    def send_notification(self, message: str, level: str = 'info') -> bool:
        """Send notification to Slack"""
        if not self.enabled:
            return False

        try:
            color_map = {
                'success': '#36a64f',
                'warning': '#ff9500',
                'error': '#ff0000',
                'info': '#36a64f'
            }

            payload = {
                'attachments': [{
                    'color': color_map.get(level, '#36a64f'),
                    'title': f'NBA MCP Synthesis - Secrets Loader',
                    'text': message,
                    'timestamp': int(time.time()),
                    'footer': 'NBA MCP Synthesis Workflow',
                    'footer_icon': 'https://platform.slack-edge.com/img/default_application_icon.png'
                }]
            }

            response = requests.post(self.webhook_url, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def notify_secrets_loaded(self, count: int, health_summary: Dict[str, Any]) -> bool:
        """Notify about successful secrets loading"""
        message = f"✅ Successfully loaded {count} secrets\n"
        message += f"Health Status: {'🟢 Healthy' if health_summary['overall_health'] else '🟡 Issues detected'}\n"

        if not health_summary['overall_health']:
            issues = [issue for issue in health_summary['issues'] if 'FAILED' in issue]
            message += f"Issues: {', '.join(issues[:3])}"  # Show first 3 issues

        return self.send_notification(message, 'success' if health_summary['overall_health'] else 'warning')

    def notify_secrets_error(self, error: str) -> bool:
        """Notify about secrets loading error"""
        message = f"❌ Secrets loading failed: {error}"
        return self.send_notification(message, 'error')

def load_workflow_secrets() -> Dict[str, str]:
    """
    Load all secrets from centralized workflow directory with enhanced validation

    Returns:
        Dictionary of loaded environment variables
    """
    # Path to centralized secrets
    secrets_dir = Path("/Users/ryanranft/Desktop/++/big_cat_bets_assets/sports_assets/big_cat_bets_simulators/NBA/nba-mcp-synthesis/.env.nba_mcp_synthesis.production")

    if not secrets_dir.exists():
        logger.error(f"Secrets directory not found: {secrets_dir}")
        print(f"❌ Secrets directory not found: {secrets_dir}")
        print("Please ensure the centralized secrets structure is set up")
        return {}

    loaded_vars = {}
    validation_errors = []

    # Load each .env file with validation
    for env_file in secrets_dir.glob("*.env"):
        try:
            with open(env_file, 'r') as f:
                value = f.read().strip()
                var_name = env_file.stem  # filename without .env extension

                # Validate secret format
                if 'API_KEY' in var_name:
                    service = var_name.split('_')[0]
                    if not SecretsValidator.validate_api_key(value, service):
                        validation_errors.append(f"Invalid {service} API key format: {var_name}")
                        logger.warning(f"Invalid API key format for {var_name}")
                elif 'WEBHOOK_URL' in var_name:
                    if not SecretsValidator.validate_webhook_url(value):
                        validation_errors.append(f"Invalid webhook URL format: {var_name}")
                        logger.warning(f"Invalid webhook URL format for {var_name}")
                elif 'TEAM_ID' in var_name or 'PROJECT_ID' in var_name:
                    if not SecretsValidator.validate_uuid(value):
                        validation_errors.append(f"Invalid UUID format: {var_name}")
                        logger.warning(f"Invalid UUID format for {var_name}")

                # Set environment variable
                os.environ[var_name] = value
                loaded_vars[var_name] = value

                logger.info(f"Loaded secret: {var_name}")
                print(f"✅ Loaded: {var_name}")

        except Exception as e:
            error_msg = f"Error loading {env_file}: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            validation_errors.append(error_msg)

    # Log validation errors
    if validation_errors:
        logger.warning(f"Validation errors found: {validation_errors}")
        print(f"\n⚠️  Validation warnings:")
        for error in validation_errors:
            print(f"   - {error}")

    logger.info(f"Successfully loaded {len(loaded_vars)} environment variables")
    print(f"\n🎉 Loaded {len(loaded_vars)} environment variables")
    return loaded_vars

def verify_critical_vars() -> bool:
    """Verify that critical variables are loaded with enhanced validation"""
    critical_vars = [
        'GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
        'DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
        'ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
        'OPENAI_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
        'SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW',
        'LINEAR_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW'
    ]

    missing = []
    invalid = []

    for var in critical_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            continue

        # Additional validation for critical vars
        if 'API_KEY' in var:
            service = var.split('_')[0]
            if not SecretsValidator.validate_api_key(value, service):
                invalid.append(f"{var} (invalid format)")
        elif 'WEBHOOK_URL' in var:
            if not SecretsValidator.validate_webhook_url(value):
                invalid.append(f"{var} (invalid URL format)")

    if missing:
        logger.error(f"Missing critical variables: {missing}")
        print(f"❌ Missing critical variables: {missing}")
        return False

    if invalid:
        logger.warning(f"Invalid critical variables: {invalid}")
        print(f"⚠️  Invalid critical variables: {invalid}")

    logger.info("All critical variables loaded and validated")
    print("✅ All critical variables loaded and validated")
    return True

def perform_health_checks(secrets: Dict[str, str]) -> Dict[str, Any]:
    """Perform comprehensive health checks on loaded secrets"""
    print("\n🔍 Performing health checks...")

    health_checker = HealthChecker(secrets)
    health_summary = health_checker.get_health_summary()

    # Display health check results
    print(f"📊 Health Summary:")
    print(f"   Total Secrets: {health_summary['total_secrets']}")
    print(f"   Overall Health: {'🟢 Healthy' if health_summary['overall_health'] else '🟡 Issues detected'}")

    if health_summary['connectivity_checks']:
        print(f"   Connectivity Checks:")
        for service, status in health_summary['connectivity_checks'].items():
            print(f"     {service}: {'✅' if status else '❌'}")

    if health_summary['strength_checks']:
        print(f"   Strength Checks:")
        for var, status in health_summary['strength_checks'].items():
            print(f"     {var}: {'✅' if status else '❌'}")

    return health_summary

def send_slack_notifications(secrets: Dict[str, str], health_summary: Dict[str, Any], error: Optional[str] = None):
    """Send Slack notifications about secrets loading status"""
    slack_notifier = SlackNotifier()

    if error:
        slack_notifier.notify_secrets_error(error)
    else:
        slack_notifier.notify_secrets_loaded(len(secrets), health_summary)

if __name__ == "__main__":
    print("🔐 NBA MCP Synthesis - Loading Workflow Secrets (Enhanced)")
    print("=" * 70)

    start_time = time.time()

    try:
        # Load secrets
        loaded = load_workflow_secrets()

        if not loaded:
            error_msg = "No secrets loaded"
            logger.error(error_msg)
            print(f"❌ {error_msg}. Exiting.")
            send_slack_notifications({}, {}, error_msg)
            sys.exit(1)

        # Verify critical variables
        if not verify_critical_vars():
            error_msg = "Critical variables missing or invalid"
            logger.error(error_msg)
            print(f"❌ {error_msg}. Exiting.")
            send_slack_notifications(loaded, {}, error_msg)
            sys.exit(1)

        # Perform health checks
        health_summary = perform_health_checks(loaded)

        # Send Slack notifications
        send_slack_notifications(loaded, health_summary)

        # Calculate and display execution time
        execution_time = time.time() - start_time
        logger.info(f"Secrets loading completed in {execution_time:.2f} seconds")
        print(f"\n⏱️  Execution time: {execution_time:.2f} seconds")

        print("\n🚀 Ready to run NBA MCP Synthesis workflow!")
        print("Environment variables are now available globally.")

    except Exception as e:
        error_msg = f"Unexpected error during secrets loading: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        send_slack_notifications({}, {}, error_msg)
        sys.exit(1)
