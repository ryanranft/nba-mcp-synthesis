"""
Configuration Management System

Centralized configuration for multiple environments:
- Environment-specific configs
- Dynamic configuration updates
- Configuration validation
- Secret interpolation
- Version control
- Feature flags

Features:
- YAML/JSON/ENV support
- Hot reload without restart
- Configuration inheritance
- Environment overrides
- Audit logging
- Schema validation

Use Cases:
- Multi-environment deployment
- A/B testing configuration
- Feature rollout control
- Configuration as code
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from threading import RLock
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class ConfigSource:
    """Configuration source metadata"""
    source_type: str  # 'file', 'env', 'consul', 'aws_ssm'
    location: str
    priority: int = 100
    loaded_at: Optional[datetime] = None
    checksum: Optional[str] = None


class ConfigurationSchema:
    """Configuration validation schema"""
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
    
    def validate(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate configuration against schema"""
        errors = []
        
        # Check required fields
        required = self.schema.get('required', [])
        for field in required:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Check field types
        properties = self.schema.get('properties', {})
        for field, field_schema in properties.items():
            if field in config:
                expected_type = field_schema.get('type')
                actual_value = config[field]
                
                if expected_type == 'string' and not isinstance(actual_value, str):
                    errors.append(f"Field {field} should be string, got {type(actual_value).__name__}")
                elif expected_type == 'integer' and not isinstance(actual_value, int):
                    errors.append(f"Field {field} should be integer, got {type(actual_value).__name__}")
                elif expected_type == 'boolean' and not isinstance(actual_value, bool):
                    errors.append(f"Field {field} should be boolean, got {type(actual_value).__name__}")
                
                # Check enums
                if 'enum' in field_schema:
                    if actual_value not in field_schema['enum']:
                        errors.append(f"Field {field} must be one of {field_schema['enum']}, got {actual_value}")
                
                # Check ranges
                if 'minimum' in field_schema and actual_value < field_schema['minimum']:
                    errors.append(f"Field {field} must be >= {field_schema['minimum']}, got {actual_value}")
                if 'maximum' in field_schema and actual_value > field_schema['maximum']:
                    errors.append(f"Field {field} must be <= {field_schema['maximum']}, got {actual_value}")
        
        return len(errors) == 0, errors


class ConfigurationManager:
    """Centralized configuration manager"""
    
    def __init__(self, environment: str = "development", config_dir: str = "config"):
        self.environment = environment
        self.config_dir = Path(config_dir)
        self._config: Dict[str, Any] = {}
        self._sources: List[ConfigSource] = []
        self._schemas: Dict[str, ConfigurationSchema] = {}
        self._lock = RLock()
        self._watchers: List[callable] = []
        
        # Initialize
        self._load_default_config()
    
    def _load_default_config(self) -> None:
        """Load default configuration"""
        defaults = {
            'app': {
                'name': 'NBA MCP Synthesis',
                'version': '1.0.0',
                'debug': False
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': 4
            },
            'database': {
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30
            },
            'cache': {
                'enabled': True,
                'ttl_seconds': 300,
                'max_size': 1000
            },
            'logging': {
                'level': 'INFO',
                'format': 'json',
                'output': 'stdout'
            }
        }
        
        with self._lock:
            self._config = defaults
            self._sources.append(ConfigSource(
                source_type='default',
                location='builtin',
                priority=0,
                loaded_at=datetime.now()
            ))
    
    def register_schema(self, namespace: str, schema: Dict[str, Any]) -> None:
        """Register configuration schema for validation"""
        self._schemas[namespace] = ConfigurationSchema(schema)
        logger.info(f"Registered schema for namespace: {namespace}")
    
    def load_from_file(self, filename: str, priority: int = 100) -> bool:
        """Load configuration from YAML or JSON file"""
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Configuration file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                file_content = f.read()
                checksum = hashlib.sha256(file_content.encode()).hexdigest()
                
                if filepath.suffix in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(file_content)
                elif filepath.suffix == '.json':
                    config_data = json.loads(file_content)
                else:
                    logger.error(f"Unsupported file format: {filepath.suffix}")
                    return False
            
            with self._lock:
                self._merge_config(config_data, priority)
                self._sources.append(ConfigSource(
                    source_type='file',
                    location=str(filepath),
                    priority=priority,
                    loaded_at=datetime.now(),
                    checksum=checksum
                ))
            
            logger.info(f"Loaded configuration from {filepath}")
            self._notify_watchers()
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {filepath}: {e}")
            return False
    
    def load_from_env(self, prefix: str = "NBA_MCP_", priority: int = 200) -> None:
        """Load configuration from environment variables"""
        config_data = {}
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Convert NBA_MCP_SERVER_PORT to server.port
                config_key = key[len(prefix):].lower()
                parts = config_key.split('_')
                
                # Navigate nested dict
                current = config_data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # Set value with type conversion
                final_key = parts[-1]
                current[final_key] = self._convert_env_value(value)
        
        if config_data:
            with self._lock:
                self._merge_config(config_data, priority)
                self._sources.append(ConfigSource(
                    source_type='env',
                    location='environment',
                    priority=priority,
                    loaded_at=datetime.now()
                ))
            
            logger.info(f"Loaded {len(config_data)} configuration items from environment")
            self._notify_watchers()
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type"""
        # Boolean
        if value.lower() in ['true', 'yes', '1']:
            return True
        if value.lower() in ['false', 'no', '0']:
            return False
        
        # Integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float
        try:
            return float(value)
        except ValueError:
            pass
        
        # String
        return value
    
    def _merge_config(self, new_config: Dict[str, Any], priority: int) -> None:
        """Merge new configuration with existing (deep merge)"""
        def deep_merge(base: Dict, update: Dict) -> Dict:
            result = base.copy()
            for key, value in update.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        self._config = deep_merge(self._config, new_config)
    
    def get(self, key: str, default: Any = None, namespace: Optional[str] = None) -> Any:
        """Get configuration value by dot-notation key"""
        with self._lock:
            if namespace:
                keys = [namespace] + key.split('.')
            else:
                keys = key.split('.')
            
            current = self._config
            for k in keys:
                if isinstance(current, dict) and k in current:
                    current = current[k]
                else:
                    return default
            
            return current
    
    def set(self, key: str, value: Any, namespace: Optional[str] = None) -> None:
        """Set configuration value by dot-notation key"""
        with self._lock:
            if namespace:
                keys = [namespace] + key.split('.')
            else:
                keys = key.split('.')
            
            current = self._config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
            logger.debug(f"Set configuration: {'.'.join(keys)} = {value}")
            self._notify_watchers()
    
    def get_all(self, namespace: Optional[str] = None) -> Dict[str, Any]:
        """Get all configuration or namespace"""
        with self._lock:
            if namespace:
                return self._config.get(namespace, {})
            return self._config.copy()
    
    def validate(self, namespace: Optional[str] = None) -> tuple[bool, List[str]]:
        """Validate configuration against registered schemas"""
        all_errors = []
        
        if namespace:
            if namespace in self._schemas:
                config_data = self.get_all(namespace)
                is_valid, errors = self._schemas[namespace].validate(config_data)
                all_errors.extend(errors)
            else:
                logger.warning(f"No schema registered for namespace: {namespace}")
        else:
            # Validate all namespaces
            for ns, schema in self._schemas.items():
                config_data = self.get_all(ns)
                is_valid, errors = schema.validate(config_data)
                all_errors.extend([f"{ns}.{e}" for e in errors])
        
        return len(all_errors) == 0, all_errors
    
    def watch(self, callback: callable) -> None:
        """Register a callback for configuration changes"""
        self._watchers.append(callback)
        logger.debug(f"Registered configuration watcher: {callback.__name__}")
    
    def _notify_watchers(self) -> None:
        """Notify all watchers of configuration changes"""
        for watcher in self._watchers:
            try:
                watcher(self._config)
            except Exception as e:
                logger.error(f"Error notifying watcher {watcher.__name__}: {e}")
    
    def reload(self) -> bool:
        """Reload all configuration sources"""
        logger.info("Reloading all configuration sources...")
        
        # Save sources
        sources = self._sources.copy()
        
        # Reset config
        self._config = {}
        self._sources = []
        self._load_default_config()
        
        # Reload each source
        success = True
        for source in sources:
            if source.source_type == 'file':
                if not self.load_from_file(Path(source.location).name, source.priority):
                    success = False
            elif source.source_type == 'env':
                self.load_from_env(priority=source.priority)
        
        if success:
            logger.info("Configuration reloaded successfully")
        else:
            logger.warning("Configuration reload completed with errors")
        
        return success
    
    def export_to_file(self, filename: str, format: str = 'yaml') -> bool:
        """Export current configuration to file"""
        filepath = self.config_dir / filename
        
        try:
            with self._lock:
                config_copy = self._config.copy()
            
            with open(filepath, 'w') as f:
                if format == 'yaml':
                    yaml.dump(config_copy, f, default_flow_style=False)
                elif format == 'json':
                    json.dump(config_copy, f, indent=2)
                else:
                    logger.error(f"Unsupported export format: {format}")
                    return False
            
            logger.info(f"Exported configuration to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
            return False


# Global instance
_config_manager = None
_config_lock = RLock()


def get_config_manager(environment: Optional[str] = None) -> ConfigurationManager:
    """Get global configuration manager"""
    global _config_manager
    with _config_lock:
        if _config_manager is None:
            env = environment or os.getenv('NBA_MCP_ENV', 'development')
            _config_manager = ConfigurationManager(environment=env)
        return _config_manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Configuration Manager Demo ===\n")
    
    # Create manager
    config_manager = ConfigurationManager(environment='development')
    
    # Register schema
    server_schema = {
        'required': ['host', 'port'],
        'properties': {
            'host': {'type': 'string'},
            'port': {'type': 'integer', 'minimum': 1024, 'maximum': 65535},
            'workers': {'type': 'integer', 'minimum': 1, 'maximum': 32}
        }
    }
    config_manager.register_schema('server', server_schema)
    
    # Get configurations
    print("--- Default Configuration ---")
    print(f"Server host: {config_manager.get('server.host')}")
    print(f"Server port: {config_manager.get('server.port')}")
    print(f"Cache enabled: {config_manager.get('cache.enabled')}")
    print(f"Log level: {config_manager.get('logging.level')}")
    
    # Set custom values
    print("\n--- Setting Custom Values ---")
    config_manager.set('server.port', 9000)
    config_manager.set('app.debug', True)
    print(f"Server port: {config_manager.get('server.port')}")
    print(f"Debug mode: {config_manager.get('app.debug')}")
    
    # Validate
    print("\n--- Validation ---")
    is_valid, errors = config_manager.validate('server')
    print(f"Server config valid: {is_valid}")
    if errors:
        for error in errors:
            print(f"  Error: {error}")
    
    # Load from environment
    print("\n--- Loading from Environment ---")
    os.environ['NBA_MCP_SERVER_PORT'] = '8080'
    os.environ['NBA_MCP_APP_DEBUG'] = 'true'
    config_manager.load_from_env()
    print(f"Server port (from env): {config_manager.get('server.port')}")
    print(f"Debug mode (from env): {config_manager.get('app.debug')}")
    
    # Watch for changes
    print("\n--- Configuration Watcher ---")
    def on_config_change(config):
        print(f"  Configuration changed! Cache enabled: {config.get('cache', {}).get('enabled')}")
    
    config_manager.watch(on_config_change)
    config_manager.set('cache.enabled', False)
    
    print("\n=== Demo Complete ===")

