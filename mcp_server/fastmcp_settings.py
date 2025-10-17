"""
FastMCP Settings for NBA MCP Server
Environment variable configuration with context-rich naming convention

Updated to use the new unified secrets and configuration management system.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal
import os


class NBAMCPSettings(BaseSettings):
    """
    Settings for NBA MCP Server using FastMCP.

    Updated to use context-rich naming convention:
    - GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW
    - DB_HOST_NBA_MCP_SYNTHESIS_WORKFLOW
    - etc.

    Can also be configured via .env file or unified configuration system.
    """

    model_config = SettingsConfigDict(
        env_prefix="NBA_MCP_",
        env_file=".env",
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        extra="ignore",
    )

    @classmethod
    def from_unified_config(
        cls, project: str = "nba-mcp-synthesis", context: str = "production"
    ):
        """Create settings from unified configuration system."""
        try:
            from .unified_configuration_manager import UnifiedConfigurationManager

            config = UnifiedConfigurationManager(project, context)

            # Map unified config to FastMCP settings
            return cls(
                debug=config.feature_flags.enable_debug_mode,
                log_level=config.workflow_config.log_level,
                # Add other mappings as needed
            )
        except Exception as e:
            print(f"Warning: Could not load unified config: {e}")
            return cls()

    # ==========================================================================
    # Server Settings
    # ==========================================================================

    debug: bool = False
    """Enable debug mode"""

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    """Logging level"""

    host: str = "127.0.0.1"
    """Server host (for HTTP transports)"""

    port: int = 8000
    """Server port (for HTTP transports)"""

    # ==========================================================================
    # Database Settings (RDS PostgreSQL)
    # ==========================================================================

    rds_host: str = (
        os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW")
        or os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        or os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_TEST")
        or os.getenv("RDS_HOST", "localhost")
    )  # Fallback to old name
    """RDS PostgreSQL host"""

    rds_port: int = int(os.getenv("RDS_PORT", "5432"))
    """RDS PostgreSQL port"""

    rds_database: str = (
        os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW")
        or os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        or os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_TEST")
        or os.getenv("RDS_DATABASE", "nba_simulator")
    )  # Fallback to old name
    """RDS database name"""

    rds_username: str = (
        os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW")
        or os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        or os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_TEST")
        or os.getenv("RDS_USERNAME", "postgres")
    )  # Fallback to old name
    """RDS username"""

    rds_password: str = (
        os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW")
        or os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        or os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_TEST")
        or os.getenv("RDS_PASSWORD", "")
    )  # Fallback to old name
    """RDS password"""

    db_pool_size: int = 5
    """Database connection pool size"""

    db_timeout: float = 30.0
    """Database query timeout (seconds)"""

    # ==========================================================================
    # S3 Settings
    # ==========================================================================

    s3_bucket: str = (
        os.getenv("S3_BUCKET_NBA_MCP_SYNTHESIS_WORKFLOW")
        or os.getenv("S3_BUCKET_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        or os.getenv("S3_BUCKET_NBA_MCP_SYNTHESIS_TEST")
        or os.getenv("S3_BUCKET", "nba-mcp-books-20251011")
    )  # Fallback to old name
    """S3 bucket name"""

    s3_region: str = (
        os.getenv("S3_REGION_NBA_MCP_SYNTHESIS_WORKFLOW")
        or os.getenv("S3_REGION_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        or os.getenv("S3_REGION_NBA_MCP_SYNTHESIS_TEST")
        or os.getenv("S3_REGION", "us-east-1")
    )  # Fallback to old name
    """S3 region"""

    # ==========================================================================
    # AWS Glue Settings
    # ==========================================================================

    glue_database: str = (
        os.getenv("GLUE_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW")
        or os.getenv("GLUE_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        or os.getenv("GLUE_DATABASE_NBA_MCP_SYNTHESIS_TEST")
        or os.getenv("GLUE_DATABASE", "nba_data_catalog")
    )  # Fallback to old name
    """Glue database name"""

    glue_region: str = (
        os.getenv("GLUE_REGION_NBA_MCP_SYNTHESIS_WORKFLOW")
        or os.getenv("GLUE_REGION_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        or os.getenv("GLUE_REGION_NBA_MCP_SYNTHESIS_TEST")
        or os.getenv("GLUE_REGION", "us-east-1")
    )  # Fallback to old name
    """Glue region"""

    # ==========================================================================
    # Security Settings
    # ==========================================================================

    max_concurrent_requests: int = 10
    """Maximum concurrent tool executions"""

    enable_sql_injection_protection: bool = True
    """Enable SQL injection protection"""

    enable_path_traversal_protection: bool = True
    """Enable path traversal protection"""

    rate_limit_per_minute: int = 60
    """Rate limit per client per minute"""

    # ==========================================================================
    # Slack Settings (Optional)
    # ==========================================================================

    slack_webhook_url: Optional[str] = (
        os.getenv("SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW")
        or os.getenv("SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_DEVELOPMENT")
        or os.getenv("SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_TEST")
        or os.getenv("SLACK_WEBHOOK_URL")
    )  # Fallback to old name
    """Slack webhook URL for notifications"""

    notify_on_success: bool = False
    """Send Slack notifications on successful tool executions"""

    notify_on_error: bool = True
    """Send Slack notifications on errors"""

    # ==========================================================================
    # Project Settings
    # ==========================================================================

    project_root: str = os.getenv("PROJECT_ROOT", "/Users/ryanranft/nba-mcp-synthesis")
    """Project root directory"""

    synthesis_output_dir: str = os.getenv(
        "SYNTHESIS_OUTPUT_DIR", "/Users/ryanranft/nba-mcp-synthesis/synthesis_outputs"
    )
    """Directory for synthesis outputs"""

    # ==========================================================================
    # FastMCP HTTP Settings (for non-stdio transports)
    # ==========================================================================

    mount_path: str = "/"
    """Mount path for HTTP server"""

    sse_path: str = "/sse"
    """SSE endpoint path"""

    message_path: str = "/messages/"
    """Message endpoint path"""

    streamable_http_path: str = "/mcp"
    """Streamable HTTP endpoint path"""

    json_response: bool = False
    """Use JSON response format"""

    stateless_http: bool = False
    """Run HTTP server in stateless mode"""

    # ==========================================================================
    # Tool Settings
    # ==========================================================================

    warn_on_duplicate_tools: bool = True
    """Warn when duplicate tools are registered"""

    warn_on_duplicate_resources: bool = True
    """Warn when duplicate resources are registered"""

    warn_on_duplicate_prompts: bool = True
    """Warn when duplicate prompts are registered"""

    # ==========================================================================
    # Feature Flags
    # ==========================================================================

    enable_database_tools: bool = True
    """Enable database query tools"""

    enable_s3_tools: bool = True
    """Enable S3 file access tools"""

    enable_glue_tools: bool = True
    """Enable Glue catalog tools"""

    enable_file_tools: bool = True
    """Enable local file tools"""

    enable_action_tools: bool = True
    """Enable action tools (save, log, notify)"""

    # ==========================================================================
    # Monitoring & Observability
    # ==========================================================================

    enable_performance_logging: bool = True
    """Enable performance logging"""

    enable_structured_logging: bool = True
    """Enable structured JSON logging"""

    log_dir: str = "logs"
    """Directory for log files"""

    # ==========================================================================
    # Helper Methods
    # ==========================================================================

    @property
    def database_url(self) -> str:
        """Construct database connection URL"""
        return f"postgresql://{self.rds_username}:{self.rds_password}@{self.rds_host}:{self.rds_port}/{self.rds_database}"

    @property
    def s3_url(self) -> str:
        """Construct S3 bucket URL"""
        return f"s3://{self.s3_bucket}"

    def __repr__(self) -> str:
        """String representation (hiding sensitive data)"""
        return (
            f"NBAMCPSettings("
            f"debug={self.debug}, "
            f"rds_host={self.rds_host}, "
            f"s3_bucket={self.s3_bucket}, "
            f"glue_database={self.glue_database})"
        )


# Example usage in FastMCP server:
#
# from mcp.server.fastmcp import FastMCP
# from .fastmcp_settings import NBAMCPSettings
#
# settings = NBAMCPSettings()
# mcp = FastMCP(
#     "nba-mcp",
#     debug=settings.debug,
#     log_level=settings.log_level,
#     host=settings.host,
#     port=settings.port
# )
