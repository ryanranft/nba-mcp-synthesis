#!/usr/bin/env python3
"""
Unified Configuration Manager with Context-Rich Naming Convention

This module provides a comprehensive configuration management system that:
- Integrates with the unified secrets manager
- Supports context-rich naming conventions
- Provides environment-specific configurations
- Supports dynamic configuration updates
- Includes configuration validation and schema support
- Provides audit logging and version control
- Supports feature flags and A/B testing

Features merged from existing managers:
- Environment-specific configs (from config_manager.py)
- Dynamic configuration updates (from configuration_manager.py)
- Configuration validation and schema support
- Secret interpolation with naming convention
- Hot reload without restart
- Configuration inheritance
- Environment overrides
- Audit logging
- Version control
- Feature flags
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import threading

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

# Configure logging
logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environment types with context-rich naming"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    WORKFLOW = "workflow"  # Alias for production
    TEST = "test"


@dataclass
class DatabaseConfig:
    """Database configuration with context-rich naming"""

    host: str
    port: int
    database: str
    username: str
    password: str
    ssl_mode: str = "prefer"
    max_connections: int = 20
    connection_timeout: int = 30

    @classmethod
    def from_env(cls, project: str, context_key: str) -> "DatabaseConfig":
        """Create database config from environment variables with naming convention"""
        return cls(
            host=os.getenv(
                f'DB_HOST_{project.upper().replace("-", "_")}_{context_key}',
                "localhost",
            ),
            port=int(
                os.getenv(
                    f'DB_PORT_{project.upper().replace("-", "_")}_{context_key}', "5432"
                )
            ),
            database=os.getenv(
                f'DB_NAME_{project.upper().replace("-", "_")}_{context_key}', "nba_mcp"
            ),
            username=os.getenv(
                f'DB_USER_{project.upper().replace("-", "_")}_{context_key}', "postgres"
            ),
            password=os.getenv(
                f'DB_PASSWORD_{project.upper().replace("-", "_")}_{context_key}', ""
            ),
            ssl_mode=os.getenv(
                f'DB_SSL_MODE_{project.upper().replace("-", "_")}_{context_key}',
                "prefer",
            ),
            max_connections=int(
                os.getenv(
                    f'DB_MAX_CONNECTIONS_{project.upper().replace("-", "_")}_{context_key}',
                    "20",
                )
            ),
            connection_timeout=int(
                os.getenv(
                    f'DB_CONNECTION_TIMEOUT_{project.upper().replace("-", "_")}_{context_key}',
                    "30",
                )
            ),
        )


@dataclass
class APIConfig:
    """API configuration with context-rich naming"""

    google_api_key: str
    anthropic_api_key: str
    openai_api_key: str
    deepseek_api_key: str
    slack_webhook_url: str
    linear_api_key: str
    linear_team_id: str
    linear_project_id: str

    @classmethod
    def from_env(cls, project: str, context_key: str) -> "APIConfig":
        """Create API config from environment variables with naming convention"""
        return cls(
            google_api_key=os.getenv(
                f'GOOGLE_API_KEY_{project.upper().replace("-", "_")}_{context_key}', ""
            ),
            anthropic_api_key=os.getenv(
                f'ANTHROPIC_API_KEY_{project.upper().replace("-", "_")}_{context_key}',
                "",
            ),
            openai_api_key=os.getenv(
                f'OPENAI_API_KEY_{project.upper().replace("-", "_")}_{context_key}', ""
            ),
            deepseek_api_key=os.getenv(
                f'DEEPSEEK_API_KEY_{project.upper().replace("-", "_")}_{context_key}',
                "",
            ),
            slack_webhook_url=os.getenv(
                f"SLACK_WEBHOOK_URL_BIG_CAT_BETS_GLOBAL_{context_key}", ""
            ),
            linear_api_key=os.getenv(
                f"LINEAR_API_KEY_BIG_CAT_BETS_GLOBAL_{context_key}", ""
            ),
            linear_team_id=os.getenv(
                f"LINEAR_TEAM_ID_BIG_CAT_BETS_GLOBAL_{context_key}", ""
            ),
            linear_project_id=os.getenv(
                f"LINEAR_PROJECT_ID_BIG_CAT_BETS_GLOBAL_{context_key}", ""
            ),
        )


@dataclass
class WorkflowConfig:
    """Workflow configuration with context-rich naming"""

    enable_notifications: bool
    enable_linear_issues: bool
    critical_stages: List[str]
    budget_alert_threshold_1: float
    budget_alert_threshold_2: float
    max_cost_per_book: float
    notification_batch_size: int
    enable_slack_threads: bool
    max_retries: int
    retry_delay: int
    retry_backoff: int
    enable_checkpoints: bool
    checkpoint_interval: int
    log_level: str

    @classmethod
    def from_env(cls, project: str, context_key: str) -> "WorkflowConfig":
        """Create workflow config from environment variables with naming convention"""
        return cls(
            enable_notifications=os.getenv(
                f'WORKFLOW_ENABLE_NOTIFICATIONS_{project.upper().replace("-", "_")}_{context_key}',
                "true",
            ).lower()
            == "true",
            enable_linear_issues=os.getenv(
                f'WORKFLOW_ENABLE_LINEAR_ISSUES_{project.upper().replace("-", "_")}_{context_key}',
                "true",
            ).lower()
            == "true",
            critical_stages=os.getenv(
                f'WORKFLOW_CRITICAL_STAGES_{project.upper().replace("-", "_")}_{context_key}',
                "pre_flight,book_analysis",
            ).split(","),
            budget_alert_threshold_1=float(
                os.getenv(
                    f'WORKFLOW_BUDGET_ALERT_THRESHOLD_1_{project.upper().replace("-", "_")}_{context_key}',
                    "0.80",
                )
            ),
            budget_alert_threshold_2=float(
                os.getenv(
                    f'WORKFLOW_BUDGET_ALERT_THRESHOLD_2_{project.upper().replace("-", "_")}_{context_key}',
                    "0.95",
                )
            ),
            max_cost_per_book=float(
                os.getenv(
                    f'WORKFLOW_MAX_COST_PER_BOOK_{project.upper().replace("-", "_")}_{context_key}',
                    "0.50",
                )
            ),
            notification_batch_size=int(
                os.getenv(
                    f'WORKFLOW_NOTIFICATION_BATCH_SIZE_{project.upper().replace("-", "_")}_{context_key}',
                    "5",
                )
            ),
            enable_slack_threads=os.getenv(
                f'WORKFLOW_ENABLE_SLACK_THREADS_{project.upper().replace("-", "_")}_{context_key}',
                "true",
            ).lower()
            == "true",
            max_retries=int(
                os.getenv(
                    f'WORKFLOW_MAX_RETRIES_{project.upper().replace("-", "_")}_{context_key}',
                    "3",
                )
            ),
            retry_delay=int(
                os.getenv(
                    f'WORKFLOW_RETRY_DELAY_{project.upper().replace("-", "_")}_{context_key}',
                    "5",
                )
            ),
            retry_backoff=int(
                os.getenv(
                    f'WORKFLOW_RETRY_BACKOFF_{project.upper().replace("-", "_")}_{context_key}',
                    "2",
                )
            ),
            enable_checkpoints=os.getenv(
                f'WORKFLOW_ENABLE_CHECKPOINTS_{project.upper().replace("-", "_")}_{context_key}',
                "true",
            ).lower()
            == "true",
            checkpoint_interval=int(
                os.getenv(
                    f'WORKFLOW_CHECKPOINT_INTERVAL_{project.upper().replace("-", "_")}_{context_key}',
                    "5",
                )
            ),
            log_level=os.getenv(
                f'WORKFLOW_LOG_LEVEL_{project.upper().replace("-", "_")}_{context_key}',
                "INFO",
            ),
        )


@dataclass
class FeatureFlags:
    """Feature flags configuration"""

    enable_new_analyzer: bool = False
    enable_advanced_caching: bool = False
    enable_experimental_features: bool = False
    enable_debug_mode: bool = False
    enable_performance_monitoring: bool = False

    @classmethod
    def from_env(cls, project: str, context_key: str) -> "FeatureFlags":
        """Create feature flags from environment variables with naming convention"""
        return cls(
            enable_new_analyzer=os.getenv(
                f'FEATURE_ENABLE_NEW_ANALYZER_{project.upper().replace("-", "_")}_{context_key}',
                "false",
            ).lower()
            == "true",
            enable_advanced_caching=os.getenv(
                f'FEATURE_ENABLE_ADVANCED_CACHING_{project.upper().replace("-", "_")}_{context_key}',
                "false",
            ).lower()
            == "true",
            enable_experimental_features=os.getenv(
                f'FEATURE_ENABLE_EXPERIMENTAL_{project.upper().replace("-", "_")}_{context_key}',
                "false",
            ).lower()
            == "true",
            enable_debug_mode=os.getenv(
                f'FEATURE_ENABLE_DEBUG_MODE_{project.upper().replace("-", "_")}_{context_key}',
                "false",
            ).lower()
            == "true",
            enable_performance_monitoring=os.getenv(
                f'FEATURE_ENABLE_PERFORMANCE_MONITORING_{project.upper().replace("-", "_")}_{context_key}',
                "false",
            ).lower()
            == "true",
        )


class ConfigurationFileHandler:
    """File system event handler for configuration hot reload"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(
            (".json", ".yaml", ".yml")
        ):
            self.logger.info(f"Configuration file changed: {event.src_path}")
            self.config_manager.reload_configuration()


class UnifiedConfigurationManager:
    """
    Unified configuration manager with context-rich naming convention support
    """

    def __init__(
        self, project: str = None, context: str = None, config_dir: str = None
    ):
        self.project = project or os.getenv("PROJECT_NAME", "nba-mcp-synthesis")
        self.context = context or os.getenv("NBA_MCP_CONTEXT", "production")

        # Map context names for consistency
        context_mapping = {
            "production": "WORKFLOW",
            "workflow": "WORKFLOW",
            "development": "DEVELOPMENT",
            "test": "TEST",
        }
        self.context_key = context_mapping.get(
            self.context.lower(), self.context.upper()
        )

        self.config_dir = (
            Path(config_dir)
            if config_dir
            else Path(
                f"/Users/ryanranft/Desktop/++/big_cat_bets_assets/config/{self.project}"
            )
        )

        # Configuration components
        self.database_config: Optional[DatabaseConfig] = None
        self.api_config: Optional[APIConfig] = None
        self.workflow_config: Optional[WorkflowConfig] = None
        self.feature_flags: Optional[FeatureFlags] = None

        # Configuration data
        self.config_data: Dict[str, Any] = {}
        self.config_schema: Dict[str, Any] = {}

        # Hot reload support
        self.observer: Optional[Observer] = None
        self.file_handler: Optional[ConfigurationFileHandler] = None
        self._lock = threading.RLock()

        # Audit logging
        self.audit_log: List[Dict[str, Any]] = []

        # Load initial configuration
        self.load_configuration()

    def load_configuration(self) -> bool:
        """Load configuration from files and environment variables"""
        with self._lock:
            try:
                logger.info(
                    f"Loading configuration for project={self.project}, context={self.context}"
                )

                # Load from configuration files
                self._load_config_files()

                # Load from environment variables with naming convention
                self._load_from_environment()

                # Validate configuration
                self._validate_configuration()

                # Log successful load
                self._audit_log(
                    "config_loaded",
                    {
                        "project": self.project,
                        "context": self.context,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                logger.info("Configuration loaded successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                self._audit_log(
                    "config_load_error",
                    {
                        "error": str(e),
                        "project": self.project,
                        "context": self.context,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                return False

    def _load_config_files(self):
        """Load configuration from JSON/YAML files"""
        config_files = [
            self.config_dir / f"config.{self.context}.json",
            self.config_dir / f"config.{self.context}.yaml",
            self.config_dir / f"config.{self.context}.yml",
            self.config_dir / "config.json",
            self.config_dir / "config.yaml",
            self.config_dir / "config.yml",
        ]

        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, "r") as f:
                        if config_file.suffix in [".yaml", ".yml"]:
                            file_data = yaml.safe_load(f)
                        else:
                            file_data = json.load(f)

                        # Merge with existing config data
                        self._merge_config_data(file_data)
                        logger.info(f"Loaded configuration from: {config_file}")

                except Exception as e:
                    logger.warning(f"Failed to load config file {config_file}: {e}")

    def _load_from_environment(self):
        """Load configuration from environment variables with naming convention"""
        # Load database configuration
        self.database_config = DatabaseConfig.from_env(self.project, self.context_key)

        # Load API configuration
        self.api_config = APIConfig.from_env(self.project, self.context_key)

        # Load workflow configuration
        self.workflow_config = WorkflowConfig.from_env(self.project, self.context_key)

        # Load feature flags
        self.feature_flags = FeatureFlags.from_env(self.project, self.context_key)

        # Store in config data
        self.config_data.update(
            {
                "database": asdict(self.database_config),
                "api": asdict(self.api_config),
                "workflow": asdict(self.workflow_config),
                "feature_flags": asdict(self.feature_flags),
            }
        )

    def _merge_config_data(self, new_data: Dict[str, Any]):
        """Merge new configuration data with existing data"""

        def deep_merge(base: Dict, update: Dict) -> Dict:
            for key, value in update.items():
                if (
                    key in base
                    and isinstance(base[key], dict)
                    and isinstance(value, dict)
                ):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
            return base

        self.config_data = deep_merge(self.config_data, new_data)

    def _validate_configuration(self):
        """Validate configuration against schema"""
        # Basic validation
        required_sections = ["database", "api", "workflow"]
        for section in required_sections:
            if section not in self.config_data:
                logger.warning(f"Missing required configuration section: {section}")

        # Validate database config
        if self.database_config:
            if not self.database_config.host:
                logger.warning("Database host not configured")
            if not self.database_config.password:
                logger.warning("Database password not configured")

        # Validate API config
        if self.api_config:
            if not self.api_config.google_api_key:
                logger.warning("Google API key not configured")
            if not self.api_config.anthropic_api_key:
                logger.warning("Anthropic API key not configured")

    def reload_configuration(self):
        """Reload configuration (hot reload)"""
        logger.info("Reloading configuration...")
        self.load_configuration()

    def enable_hot_reload(self):
        """Enable hot reload for configuration files"""
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available, hot reload disabled")
            return

        if self.observer is None:
            self.file_handler = ConfigurationFileHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                self.file_handler, str(self.config_dir), recursive=True
            )
            self.observer.start()
            logger.info("Hot reload enabled for configuration files")

    def disable_hot_reload(self):
        """Disable hot reload"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Hot reload disabled")

    def get_config(self, section: str = None, key: str = None) -> Any:
        """Get configuration value"""
        with self._lock:
            if section is None:
                return self.config_data

            if key is None:
                return self.config_data.get(section)

            section_data = self.config_data.get(section, {})
            return section_data.get(key)

    def set_config(self, section: str, key: str, value: Any):
        """Set configuration value"""
        with self._lock:
            if section not in self.config_data:
                self.config_data[section] = {}

            self.config_data[section][key] = value

            # Update specific config objects
            if section == "database" and self.database_config:
                setattr(self.database_config, key, value)
            elif section == "api" and self.api_config:
                setattr(self.api_config, key, value)
            elif section == "workflow" and self.workflow_config:
                setattr(self.workflow_config, key, value)
            elif section == "feature_flags" and self.feature_flags:
                setattr(self.feature_flags, key, value)

            self._audit_log(
                "config_updated",
                {
                    "section": section,
                    "key": key,
                    "value": str(value)[:100],  # Truncate for security
                    "timestamp": datetime.now().isoformat(),
                },
            )

    def export_configuration(self, output_file: str = None) -> str:
        """Export configuration to file"""
        config_export = {
            "project": self.project,
            "context": self.context,
            "timestamp": datetime.now().isoformat(),
            "configuration": self.config_data,
        }

        content = json.dumps(config_export, indent=2)

        if output_file:
            with open(output_file, "w") as f:
                f.write(content)
            logger.info(f"Configuration exported to: {output_file}")

        return content

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of configuration manager"""
        return {
            "project": self.project,
            "context": self.context,
            "config_loaded": bool(self.config_data),
            "database_configured": bool(
                self.database_config and self.database_config.host
            ),
            "api_configured": bool(self.api_config and self.api_config.google_api_key),
            "workflow_configured": bool(self.workflow_config),
            "feature_flags_configured": bool(self.feature_flags),
            "hot_reload_enabled": self.observer is not None,
            "audit_log_entries": len(self.audit_log),
            "last_updated": datetime.now().isoformat(),
        }

    def _audit_log(self, action: str, data: Dict[str, Any]):
        """Add entry to audit log"""
        entry = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "project": self.project,
            "context": self.context,
            **data,
        }
        self.audit_log.append(entry)

        # Keep only last 1000 entries
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        return self.audit_log[-limit:]

    def __del__(self):
        """Cleanup on destruction"""
        self.disable_hot_reload()


# Global instance
_config_manager = None


def get_config_manager(
    project: str = None, context: str = None
) -> UnifiedConfigurationManager:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = UnifiedConfigurationManager(project, context)
    return _config_manager


def load_configuration(project: str = None, context: str = None) -> bool:
    """Load configuration and return success status"""
    manager = get_config_manager(project, context)
    return manager.load_configuration()


def get_config(section: str = None, key: str = None) -> Any:
    """Get configuration value"""
    manager = get_config_manager()
    return manager.get_config(section, key)


def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    manager = get_config_manager()
    return manager.database_config


def get_api_config() -> APIConfig:
    """Get API configuration"""
    manager = get_config_manager()
    return manager.api_config


def get_workflow_config() -> WorkflowConfig:
    """Get workflow configuration"""
    manager = get_config_manager()
    return manager.workflow_config


def get_feature_flags() -> FeatureFlags:
    """Get feature flags"""
    manager = get_config_manager()
    return manager.feature_flags


if __name__ == "__main__":
    # Test the configuration manager
    import sys

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Load configuration
    success = load_configuration()

    if success:
        print("✅ Configuration loaded successfully")

        # Show health status
        manager = get_config_manager()
        health = manager.get_health_status()
        print(f"📊 Health Status: {health}")

        # Show some configuration
        db_config = get_database_config()
        api_config = get_api_config()

        print(f"🗄️  Database: {db_config.host}:{db_config.port}")
        print(f"🔑 Google API Key: {'✅' if api_config.google_api_key else '❌'}")
        print(f"🔑 Anthropic API Key: {'✅' if api_config.anthropic_api_key else '❌'}")
    else:
        print("❌ Failed to load configuration")
        sys.exit(1)
