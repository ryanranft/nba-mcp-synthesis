"""
Environment-Specific Configuration Manager
Manages configuration for dev, staging, and production environments.

⚠️  DEPRECATION NOTICE ⚠️
This module is deprecated and will be removed in a future version.
Please migrate to the new unified configuration system:

1. Use mcp_server.unified_configuration_manager.UnifiedConfigurationManager
2. Use mcp_server.unified_secrets_manager.UnifiedSecretsManager
3. Use /Users/ryanranft/load_env_hierarchical.py for loading secrets

Migration Guide:
- Replace ConfigManager with UnifiedConfigurationManager
- Use context-rich naming convention (e.g., GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW)
- Load secrets using the hierarchical loader before initializing config

For more details, see:
- /centralized-secrets-management.plan.md
- mcp_server/unified_configuration_manager.py
- mcp_server/unified_secrets_manager.py

This file will be removed in version 2.0.0
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environment types"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


@dataclass
class DatabaseConfig:
    """Database configuration"""

    host: str
    port: int
    database: str
    user: str
    password: str
    max_connections: int = 10
    ssl_mode: str = "require"

    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class CacheConfig:
    """Cache configuration"""

    enabled: bool = True
    backend: str = "redis"  # redis, memcached, or local
    host: Optional[str] = "localhost"
    port: int = 6379
    ttl_seconds: int = 3600
    max_size_mb: int = 100


@dataclass
class LoggingConfig:
    """Logging configuration"""

    level: str = "INFO"
    format: str = "json"  # json or text
    output: str = "stdout"  # stdout, file, or cloudwatch
    file_path: Optional[str] = None
    cloudwatch_group: Optional[str] = None
    cloudwatch_stream: Optional[str] = None


@dataclass
class SecurityConfig:
    """Security configuration"""

    jwt_secret_key: str
    jwt_expiry_minutes: int = 30
    api_rate_limit: int = 100  # requests per minute
    enable_cors: bool = False
    allowed_origins: list = None

    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = []


@dataclass
class MLConfig:
    """ML/Model configuration"""

    model_registry_path: str
    mlflow_tracking_uri: str
    experiment_name: str = "nba_mcp"
    enable_drift_detection: bool = True
    drift_threshold: float = 0.05
    enable_ab_testing: bool = False


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""

    enable_metrics: bool = True
    prometheus_port: int = 9090
    grafana_port: int = 3000
    enable_tracing: bool = True
    jaeger_endpoint: str = "http://localhost:14268/api/traces"
    enable_profiling: bool = False


class ConfigManager:
    """Manages environment-specific configurations"""

    def __init__(self, env: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            env: Environment name (development, staging, production)
                 If None, uses NBA_MCP_ENV environment variable
        """
        # Deprecation warning
        import warnings

        warnings.warn(
            "ConfigManager is deprecated. Use UnifiedConfigurationManager instead. "
            "See mcp_server/unified_configuration_manager.py for migration guide.",
            DeprecationWarning,
            stacklevel=2,
        )

        env_str = env or os.getenv("NBA_MCP_ENV", "development")
        self.environment = Environment(env_str.lower())
        self.config_dir = Path(__file__).parent.parent / "config"
        self.config: Dict[str, Any] = {}

        self._load_config()
        logger.warning(
            f"⚠️  DEPRECATED: ConfigManager loaded for environment: {self.environment.value}"
        )
        logger.warning("⚠️  Please migrate to UnifiedConfigurationManager")

    def _load_config(self):
        """Load configuration from files and environment variables"""
        # Load base config
        base_config_path = self.config_dir / "base.json"
        if base_config_path.exists():
            with open(base_config_path) as f:
                self.config = json.load(f)

        # Load environment-specific config
        env_config_path = self.config_dir / f"{self.environment.value}.json"
        if env_config_path.exists():
            with open(env_config_path) as f:
                env_config = json.load(f)
                # Merge with base config (env config overrides base)
                self._deep_merge(self.config, env_config)

        # Override with environment variables
        self._load_env_variables()

    def _deep_merge(self, base: Dict, override: Dict):
        """Deep merge two dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _load_env_variables(self):
        """Load configuration from environment variables"""
        # Database
        if os.getenv("DB_HOST"):
            self.config.setdefault("database", {})
            self.config["database"]["host"] = os.getenv("DB_HOST")
        if os.getenv("DB_PORT"):
            self.config["database"]["port"] = int(os.getenv("DB_PORT"))
        if os.getenv("DB_NAME"):
            self.config["database"]["database"] = os.getenv("DB_NAME")
        if os.getenv("DB_USER"):
            self.config["database"]["user"] = os.getenv("DB_USER")
        if os.getenv("DB_PASSWORD"):
            self.config["database"]["password"] = os.getenv("DB_PASSWORD")

        # Cache
        if os.getenv("REDIS_HOST"):
            self.config.setdefault("cache", {})
            self.config["cache"]["host"] = os.getenv("REDIS_HOST")
        if os.getenv("REDIS_PORT"):
            self.config["cache"]["port"] = int(os.getenv("REDIS_PORT"))

        # Security
        if os.getenv("JWT_SECRET"):
            self.config.setdefault("security", {})
            self.config["security"]["jwt_secret_key"] = os.getenv("JWT_SECRET")

        # ML
        if os.getenv("MLFLOW_TRACKING_URI"):
            self.config.setdefault("ml", {})
            self.config["ml"]["mlflow_tracking_uri"] = os.getenv("MLFLOW_TRACKING_URI")

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        db_config = self.config.get("database", {})
        return DatabaseConfig(**db_config)

    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        cache_config = self.config.get("cache", {})
        return CacheConfig(**cache_config)

    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        log_config = self.config.get("logging", {})
        return LoggingConfig(**log_config)

    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        security_config = self.config.get("security", {})
        return SecurityConfig(**security_config)

    def get_ml_config(self) -> MLConfig:
        """Get ML configuration"""
        ml_config = self.config.get("ml", {})
        return MLConfig(**ml_config)

    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        monitoring_config = self.config.get("monitoring", {})
        return MonitoringConfig(**monitoring_config)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT

    def is_staging(self) -> bool:
        """Check if running in staging environment"""
        return self.environment == Environment.STAGING

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION

    def is_test(self) -> bool:
        """Check if running in test environment"""
        return self.environment == Environment.TEST

    def export_config(self, path: str):
        """Export current configuration to file"""
        with open(path, "w") as f:
            json.dump(self.config, f, indent=2)
        logger.info(f"Configuration exported to {path}")

    def validate_config(self) -> bool:
        """Validate that all required configuration is present"""
        required_keys = [
            "database.host",
            "database.port",
            "database.database",
            "security.jwt_secret_key",
            "ml.model_registry_path",
        ]

        missing_keys = []
        for key in required_keys:
            if self.get(key) is None:
                missing_keys.append(key)

        if missing_keys:
            logger.error(f"Missing required configuration keys: {missing_keys}")
            return False

        logger.info("Configuration validation passed")
        return True


# Singleton instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager(env: Optional[str] = None) -> ConfigManager:
    """Get singleton ConfigManager instance"""
    global _config_manager
    if _config_manager is None or (env and env != _config_manager.environment.value):
        _config_manager = ConfigManager(env)
    return _config_manager


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("Environment-Specific Configuration Manager Demo")
    print("=" * 70)

    # Create config directory and sample configs
    config_dir = Path(__file__).parent.parent / "config"
    config_dir.mkdir(exist_ok=True)

    # Base configuration (shared across all environments)
    base_config = {
        "database": {"port": 5432, "max_connections": 10, "ssl_mode": "require"},
        "cache": {
            "enabled": True,
            "backend": "redis",
            "port": 6379,
            "ttl_seconds": 3600,
        },
        "logging": {"format": "json"},
        "ml": {"experiment_name": "nba_mcp", "drift_threshold": 0.05},
    }

    with open(config_dir / "base.json", "w") as f:
        json.dump(base_config, f, indent=2)

    # Development configuration
    dev_config = {
        "database": {
            "host": "localhost",
            "database": "nba_mcp_dev",
            "user": "dev_user",
            "password": "dev_password",
            "ssl_mode": "disable",
        },
        "cache": {"host": "localhost"},
        "logging": {"level": "DEBUG", "output": "stdout"},
        "security": {
            "jwt_secret_key": "dev-secret-key-change-in-production",
            "jwt_expiry_minutes": 60,
            "api_rate_limit": 1000,
            "enable_cors": True,
            "allowed_origins": ["http://localhost:3000", "http://localhost:8000"],
        },
        "ml": {
            "model_registry_path": "./models",
            "mlflow_tracking_uri": "http://localhost:5000",
            "enable_drift_detection": True,
            "enable_ab_testing": False,
        },
        "monitoring": {
            "enable_metrics": True,
            "enable_tracing": False,
            "enable_profiling": True,
        },
    }

    with open(config_dir / "development.json", "w") as f:
        json.dump(dev_config, f, indent=2)

    # Production configuration
    prod_config = {
        "database": {
            "host": "rds-prod-endpoint.us-east-1.rds.amazonaws.com",
            "database": "nba_mcp_prod",
            "user": "prod_user",
            "password": "${DB_PASSWORD}",  # Should come from Secrets Manager
            "max_connections": 50,
            "ssl_mode": "require",
        },
        "cache": {"host": "redis-prod.cache.amazonaws.com"},
        "logging": {
            "level": "INFO",
            "output": "cloudwatch",
            "cloudwatch_group": "/aws/nba-mcp/prod",
            "cloudwatch_stream": "application",
        },
        "security": {
            "jwt_secret_key": "${JWT_SECRET}",  # Should come from Secrets Manager
            "jwt_expiry_minutes": 30,
            "api_rate_limit": 100,
            "enable_cors": True,
            "allowed_origins": ["https://nba-mcp.com", "https://api.nba-mcp.com"],
        },
        "ml": {
            "model_registry_path": "s3://nba-mcp-models-prod/registry",
            "mlflow_tracking_uri": "https://mlflow-prod.nba-mcp.com",
            "enable_drift_detection": True,
            "enable_ab_testing": True,
        },
        "monitoring": {
            "enable_metrics": True,
            "prometheus_port": 9090,
            "enable_tracing": True,
            "jaeger_endpoint": "https://jaeger-prod.nba-mcp.com/api/traces",
            "enable_profiling": False,
        },
    }

    with open(config_dir / "production.json", "w") as f:
        json.dump(prod_config, f, indent=2)

    print("\n✅ Sample config files created in config/ directory\n")

    # Demo: Load configurations for different environments
    for env_name in ["development", "production"]:
        print(f"\n{'=' * 70}")
        print(f"Loading {env_name.upper()} configuration")
        print("=" * 70)

        config_mgr = ConfigManager(env=env_name)

        # Get typed configurations
        db_config = config_mgr.get_database_config()
        print(f"\n📦 Database Configuration:")
        print(f"  Host: {db_config.host}")
        print(f"  Port: {db_config.port}")
        print(f"  Database: {db_config.database}")
        print(f"  SSL Mode: {db_config.ssl_mode}")
        print(f"  Max Connections: {db_config.max_connections}")

        cache_config = config_mgr.get_cache_config()
        print(f"\n💾 Cache Configuration:")
        print(f"  Enabled: {cache_config.enabled}")
        print(f"  Backend: {cache_config.backend}")
        print(f"  Host: {cache_config.host}")
        print(f"  TTL: {cache_config.ttl_seconds}s")

        security_config = config_mgr.get_security_config()
        print(f"\n🔒 Security Configuration:")
        print(f"  JWT Expiry: {security_config.jwt_expiry_minutes} minutes")
        print(f"  API Rate Limit: {security_config.api_rate_limit}/min")
        print(f"  CORS Enabled: {security_config.enable_cors}")
        print(f"  Allowed Origins: {security_config.allowed_origins}")

        ml_config = config_mgr.get_ml_config()
        print(f"\n🤖 ML Configuration:")
        print(f"  Model Registry: {ml_config.model_registry_path}")
        print(f"  MLflow URI: {ml_config.mlflow_tracking_uri}")
        print(f"  Drift Detection: {ml_config.enable_drift_detection}")
        print(f"  A/B Testing: {ml_config.enable_ab_testing}")

        monitoring_config = config_mgr.get_monitoring_config()
        print(f"\n📊 Monitoring Configuration:")
        print(f"  Metrics Enabled: {monitoring_config.enable_metrics}")
        print(f"  Tracing Enabled: {monitoring_config.enable_tracing}")
        print(f"  Profiling Enabled: {monitoring_config.enable_profiling}")

        # Validate configuration
        print(
            f"\n✓ Configuration Validation: {'PASSED' if config_mgr.validate_config() else 'FAILED'}"
        )

    print("\n" + "=" * 70)
    print("Configuration Manager Demo Complete!")
    print("=" * 70)
