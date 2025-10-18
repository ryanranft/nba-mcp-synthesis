#!/usr/bin/env python3
"""
Configuration Loader for NBA MCP Synthesis Workflows

Loads and validates workflow_config.yaml for use across all scripts.

Tier 0 Features:
- Load YAML configuration
- Provide typed access to config values
- Fallback to defaults if config missing
- Environment variable overrides

Usage:
    from config_loader import ConfigLoader

    config = ConfigLoader()

    # Access values
    cost_limit = config.get_cost_limit('phase_2_analysis')
    model_name = config.get_model_config('gemini', 'model_name')

    # Check features
    if config.is_feature_enabled('intelligent_plan_editor'):
        # Use advanced feature
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Loads and provides access to workflow configuration.

    Features:
    - YAML config loading
    - Environment variable overrides
    - Type-safe accessors
    - Default fallbacks
    """

    # Default configuration (fallback if file missing)
    DEFAULT_CONFIG = {
        'workflow': {
            'mode': 'B',
            'auto_implement': False,
            'prediction_enhancements': False,
            'test_book_limit': 1,
            'default_dry_run': False
        },
        'cost_limits': {
            'phase_2_analysis': 30.00,
            'phase_3_synthesis': 20.00,
            'phase_3_5_modifications': 15.00,
            'phase_5_predictions': 10.00,
            'total_workflow': 75.00,
            'approval_threshold': 10.00
        },
        'models': {
            'gemini': {
                'model_name': 'gemini-2.0-flash-exp',
                'temperature': 0.3,
                'max_tokens': 250000,
                'timeout_seconds': 180
            },
            'claude': {
                'model_name': 'claude-sonnet-4',
                'temperature': 0.3,
                'max_tokens': 200000,
                'timeout_seconds': 180
            },
            'gpt4': {
                'model_name': 'gpt-4-turbo',
                'temperature': 0.3,
                'max_tokens': 128000,
                'timeout_seconds': 180
            }
        },
        'phases': {
            'phase_2': {
                'use_high_context': True,
                'max_chars_per_book': 1000000,
                'max_tokens_per_book': 250000,
                'min_recommendations': 10,
                'max_recommendations': 60,
                'convergence_threshold': 0.85,
                'max_iterations': 3
            },
            'phase_3': {
                'similarity_threshold': 0.80,
                'min_confidence': 0.70,
                'synthesis_models': 'claude,gpt4'
            },
            'phase_4': {
                'output_dir': 'implementation_plans',
                'generate_tests': True,
                'generate_sql': True,
                'tier_1_file_count': 6,
                'tier_2_file_count': 3
            },
            'phase_8_5': {
                'syntax_check': True,
                'test_discovery': True,
                'import_check': True,
                'sql_validation': True,
                'run_tests': False,
                'fail_on_error': False
            }
        },
        'safety': {
            'rollback': {
                'enabled': True,
                'backup_before_phase': True,
                'backup_retention_days': 7
            },
            'error_recovery': {
                'enabled': True,
                'max_retries': 3,
                'api_timeout_backoff': 2,
                'rate_limit_backoff': 60,
                'network_error_backoff': 5
            },
            'cost_tracking': {
                'enabled': True,
                'save_reports': True,
                'report_dir': 'cost_tracker'
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file_logging': True,
            'log_dir': 'logs',
            'separate_phase_logs': True
        },
        'paths': {
            'mcp_synthesis': '/Users/ryanranft/nba-mcp-synthesis',
            'simulator_aws': '/Users/ryanranft/nba-simulator-aws',
            'analysis_results': 'analysis_results',
            'implementation_plans': 'implementation_plans',
            'books_s3_bucket': 'nba-mcp-books',
            'books_s3_prefix': 'books/',
            'backups_dir': 'backups'
        },
        'features': {
            'intelligent_plan_editor': False,
            'smart_integrator': False,
            'prediction_analyzer': False,
            'status_tracking': False,
            'conflict_resolution': False
        }
    }

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config loader.

        Args:
            config_path: Path to workflow_config.yaml (defaults to config/workflow_config.yaml)
        """
        if config_path is None:
            # Default: look in config/ directory relative to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "workflow_config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

        logger.debug(f"Configuration loaded from {self.config_path}")

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file with fallback to defaults.

        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found at {self.config_path}, using defaults")
            return self.DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            if not config:
                logger.warning("Config file is empty, using defaults")
                return self.DEFAULT_CONFIG.copy()

            # Merge with defaults (config overrides defaults)
            merged = self._deep_merge(self.DEFAULT_CONFIG.copy(), config)

            logger.info(f"✅ Configuration loaded from {self.config_path}")
            return merged

        except Exception as e:
            logger.error(f"Error loading config from {self.config_path}: {e}")
            logger.warning("Using default configuration")
            return self.DEFAULT_CONFIG.copy()

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """
        Deep merge two dictionaries (override takes precedence).

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get nested configuration value.

        Args:
            *keys: Nested keys (e.g., 'cost_limits', 'phase_2_analysis')
            default: Default value if key not found

        Returns:
            Configuration value or default

        Examples:
            >>> config.get('cost_limits', 'phase_2_analysis')
            30.00
            >>> config.get('models', 'gemini', 'model_name')
            'gemini-2.0-flash-exp'
        """
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        # Check for environment variable override
        env_var = '_'.join(['NBA_MCP'] + [k.upper() for k in keys])
        env_value = os.getenv(env_var)

        if env_value is not None:
            # Try to convert to appropriate type
            if isinstance(value, bool):
                return env_value.lower() in ('true', '1', 'yes')
            elif isinstance(value, int):
                try:
                    return int(env_value)
                except ValueError:
                    pass
            elif isinstance(value, float):
                try:
                    return float(env_value)
                except ValueError:
                    pass
            return env_value

        return value

    def get_cost_limit(self, phase: str) -> float:
        """
        Get cost limit for a specific phase.

        Args:
            phase: Phase name (e.g., 'phase_2_analysis', 'total_workflow')

        Returns:
            Cost limit in USD
        """
        return self.get('cost_limits', phase, default=0.0)

    def get_model_config(self, model: str, key: str) -> Any:
        """
        Get model configuration value.

        Args:
            model: Model name ('gemini', 'claude', 'gpt4')
            key: Configuration key

        Returns:
            Configuration value
        """
        return self.get('models', model, key)

    def get_phase_config(self, phase: str, key: str) -> Any:
        """
        Get phase configuration value.

        Args:
            phase: Phase name (e.g., 'phase_2', 'phase_3')
            key: Configuration key

        Returns:
            Configuration value
        """
        return self.get('phases', phase, key)

    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature: Feature name

        Returns:
            True if enabled
        """
        return self.get('features', feature, default=False)

    def get_workflow_mode(self) -> str:
        """
        Get workflow mode (A, B, or dual).

        Returns:
            Workflow mode
        """
        return self.get('workflow', 'mode', default='B')

    def is_dry_run_default(self) -> bool:
        """
        Check if dry-run mode is enabled by default.

        Returns:
            True if dry-run is default
        """
        return self.get('workflow', 'default_dry_run', default=False)

    def get_safety_config(self, category: str, key: str) -> Any:
        """
        Get safety configuration value.

        Args:
            category: Safety category ('rollback', 'error_recovery', 'cost_tracking')
            key: Configuration key

        Returns:
            Configuration value
        """
        return self.get('safety', category, key)

    def get_path(self, path_key: str) -> Path:
        """
        Get configured path.

        Args:
            path_key: Path key (e.g., 'mcp_synthesis', 'implementation_plans')

        Returns:
            Path object
        """
        path_str = self.get('paths', path_key, default='.')
        return Path(path_str)


# Global config instance (singleton pattern)
_global_config: Optional[ConfigLoader] = None


def get_config() -> ConfigLoader:
    """
    Get global configuration instance.

    Returns:
        ConfigLoader instance
    """
    global _global_config

    if _global_config is None:
        _global_config = ConfigLoader()

    return _global_config


# Convenience functions
def get_cost_limit(phase: str) -> float:
    """Get cost limit for phase."""
    return get_config().get_cost_limit(phase)


def get_model_config(model: str, key: str) -> Any:
    """Get model configuration."""
    return get_config().get_model_config(model, key)


def get_phase_config(phase: str, key: str) -> Any:
    """Get phase configuration."""
    return get_config().get_phase_config(phase, key)


def is_feature_enabled(feature: str) -> bool:
    """Check if feature is enabled."""
    return get_config().is_feature_enabled(feature)


if __name__ == "__main__":
    # Test configuration loading
    logging.basicConfig(level=logging.INFO)

    logger.info("--- Testing ConfigLoader ---\n")

    config = ConfigLoader()

    # Test basic access
    logger.info(f"Workflow mode: {config.get_workflow_mode()}")
    logger.info(f"Phase 2 cost limit: ${config.get_cost_limit('phase_2_analysis'):.2f}")
    logger.info(f"Total workflow limit: ${config.get_cost_limit('total_workflow'):.2f}")

    # Test model config
    logger.info(f"\nGemini model: {config.get_model_config('gemini', 'model_name')}")
    logger.info(f"Gemini max tokens: {config.get_model_config('gemini', 'max_tokens'):,}")

    # Test phase config
    logger.info(f"\nPhase 2 high context: {config.get_phase_config('phase_2', 'use_high_context')}")
    logger.info(f"Phase 2 max chars: {config.get_phase_config('phase_2', 'max_chars_per_book'):,}")

    # Test feature flags
    logger.info(f"\nIntelligent plan editor: {config.is_feature_enabled('intelligent_plan_editor')}")
    logger.info(f"Smart integrator: {config.is_feature_enabled('smart_integrator')}")

    # Test safety config
    logger.info(f"\nRollback enabled: {config.get_safety_config('rollback', 'enabled')}")
    logger.info(f"Max retries: {config.get_safety_config('error_recovery', 'max_retries')}")

    # Test paths
    logger.info(f"\nProject root: {config.get_path('mcp_synthesis')}")
    logger.info(f"Implementation plans: {config.get_path('implementation_plans')}")

    # Test environment variable override
    os.environ['NBA_MCP_WORKFLOW_MODE'] = 'A'
    logger.info(f"\n(With env override) Workflow mode: {config.get_workflow_mode()}")

    logger.info("\n--- ConfigLoader testing complete ---")

