#!/usr/bin/env python3
"""
Advanced Alerting System with Slack Integration
"""

import os
import json
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    metric: str
    threshold: float
    comparison: str  # >, <, >=, <=, ==
    severity: str  # critical, warning, info
    cooldown_minutes: int = 30


class AlertManager:
    """Manages alerts and Slack notifications"""
    
    def __init__(self, slack_webhook_url: Optional[str] = None):
        self.slack_webhook_url = slack_webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        self.alert_history: Dict[str, datetime] = {}
        
        # Default alert rules
        self.rules = [
            AlertRule("high_error_rate", "error_rate", 10.0, ">", "critical", 30),
            AlertRule("slow_response", "p95_response_time", 45.0, ">", "warning", 60),
            AlertRule("high_cost", "cost_per_hour", 10.0, ">", "critical", 60),
            AlertRule("disk_full", "disk_usage_percent", 90.0, ">", "critical", 120),
            AlertRule("server_down", "server_status", 0, "==", "critical", 5),
        ]
    
    def check_alert(self, rule: AlertRule, value: float) -> bool:
        """Check if alert should fire"""
        if rule.comparison == ">":
            return value > rule.threshold
        elif rule.comparison == "<":
            return value < rule.threshold
        elif rule.comparison == ">=":
            return value >= rule.threshold
        elif rule.comparison == "<=":
            return value <= rule.threshold
        elif rule.comparison == "==":
            return value == rule.threshold
        return False
    
    def should_send_alert(self, rule_name: str, cooldown_minutes: int) -> bool:
        """Check if alert is in cooldown period"""
        if rule_name not in self.alert_history:
            return True
        
        last_alert = self.alert_history[rule_name]
        cooldown = timedelta(minutes=cooldown_minutes)
        
        return datetime.now() - last_alert > cooldown
    
    def send_slack_alert(
        self,
        rule: AlertRule,
        value: float,
        context: Optional[Dict] = None
    ) -> bool:
        """Send alert to Slack"""
        if not self.slack_webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        # Check cooldown
        if not self.should_send_alert(rule.name, rule.cooldown_minutes):
            logger.debug(f"Alert '{rule.name}' in cooldown period")
            return False
        
        # Build message
        emoji = "🚨" if rule.severity == "critical" else "⚠️" if rule.severity == "warning" else "ℹ️"
        color = "#FF0000" if rule.severity == "critical" else "#FFA500" if rule.severity == "warning" else "#0000FF"
        
        message = {
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} {rule.name.replace('_', ' ').title()}",
                    "fields": [
                        {
                            "title": "Metric",
                            "value": rule.metric,
                            "short": True
                        },
                        {
                            "title": "Current Value",
                            "value": f"{value:.2f}",
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": f"{rule.comparison} {rule.threshold}",
                            "short": True
                        },
                        {
                            "title": "Severity",
                            "value": rule.severity.upper(),
                            "short": True
                        }
                    ],
                    "footer": "NBA MCP Synthesis System",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        # Add context if provided
        if context:
            message["attachments"][0]["fields"].append({
                "title": "Additional Info",
                "value": json.dumps(context, indent=2),
                "short": False
            })
        
        try:
            response = requests.post(
                self.slack_webhook_url,
                json=message,
                timeout=10
            )
            
            if response.status_code == 200:
                self.alert_history[rule.name] = datetime.now()
                logger.info(f"✅ Slack alert sent: {rule.name}")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
            return False
    
    def check_metrics(self, metrics: Dict[str, float]) -> List[AlertRule]:
        """Check all metrics against rules and send alerts"""
        triggered_alerts = []
        
        for rule in self.rules:
            if rule.metric in metrics:
                value = metrics[rule.metric]
                
                if self.check_alert(rule, value):
                    triggered_alerts.append(rule)
                    self.send_slack_alert(rule, value)
        
        return triggered_alerts
    
    def send_test_alert(self) -> bool:
        """Send a test alert to verify Slack integration"""
        test_message = {
            "text": "✅ NBA MCP Synthesis - Slack Integration Test",
            "attachments": [
                {
                    "color": "#36a64f",
                    "title": "Test Alert",
                    "text": "If you see this message, Slack alerting is configured correctly!",
                    "footer": "NBA MCP Synthesis System",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        try:
            response = requests.post(
                self.slack_webhook_url,
                json=test_message,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Test alert failed: {e}")
            return False


# CLI for testing
if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("NBA MCP Synthesis - Alert System Test")
    print("="*60)
    print()
    
    # Create alert manager
    manager = AlertManager()
    
    if not manager.slack_webhook_url:
        print("❌ SLACK_WEBHOOK_URL not set in environment")
        print()
        print("To configure:")
        print("1. Create a Slack webhook at https://api.slack.com/messaging/webhooks")
        print("2. Set environment variable: export SLACK_WEBHOOK_URL='your-webhook-url'")
        sys.exit(1)
    
    print(f"📡 Slack webhook configured")
    print(f"🔔 Testing {len(manager.rules)} alert rules")
    print()
    
    # Send test alert
    print("Sending test alert to Slack...")
    success = manager.send_test_alert()
    
    if success:
        print("✅ Test alert sent successfully!")
        print()
        print("Check your Slack channel for the test message.")
    else:
        print("❌ Failed to send test alert")
        print("Check your webhook URL and network connection")
    
    print()
    print("="*60)
    
    sys.exit(0 if success else 1)
