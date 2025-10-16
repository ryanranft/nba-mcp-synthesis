"""
MCP Server Configuration
Handles all configuration settings for the NBA MCP Server
"""

import os
from typing import Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()


@dataclass
class MCPConfig:
    """Configuration for NBA MCP Server"""

    # Server settings
    host: str = "localhost"
    port: int = 3000

    # AWS RDS PostgreSQL
    rds_host: str = ""
    rds_port: int = 5432
    rds_database: str = "nba_simulator"
    rds_username: str = ""
    rds_password: str = ""

    # AWS S3
    s3_bucket: str = "nba-mcp-books-20251011"
    s3_region: str = "us-east-1"

    # AWS Glue
    glue_database: str = "nba_raw_data"
    glue_region: str = "us-east-1"

    # Project paths
    project_root: str = "/Users/ryanranft/nba-simulator-aws"
    synthesis_output_dir: str = ""

    # Slack (optional)
    slack_webhook_url: Optional[str] = None
    notify_on_success: bool = False

    # Safety limits
    max_query_rows: int = 1000
    max_file_size_bytes: int = 1048576  # 1MB
    query_timeout_seconds: int = 30
    max_context_tokens: int = 4000

    # Performance
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300

    # Security
    allowed_sql_keywords: List[str] = field(default_factory=lambda: [
        "SELECT", "EXPLAIN", "SHOW", "DESCRIBE", "WITH"
    ])
    forbidden_sql_keywords: List[str] = field(default_factory=lambda: [
        "DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE",
        "ALTER", "CREATE", "GRANT", "REVOKE"
    ])

    # Logging
    log_file: str = "logs/mcp_synthesis.log"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "MCPConfig":
        """Create configuration from environment variables"""

        # Get synthesis output dir
        synthesis_dir = os.getenv(
            "SYNTHESIS_OUTPUT_DIR",
            os.path.join(os.getenv("PROJECT_ROOT", ""), "synthesis_output")
        )

        return cls(
            # Server
            host=os.getenv("MCP_SERVER_HOST", "localhost"),
            port=int(os.getenv("MCP_SERVER_PORT", "3000")),

            # RDS - Try new naming convention first, then fallback to old
            rds_host=(os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_WORKFLOW") or
                     os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                     os.getenv("RDS_HOST_NBA_MCP_SYNTHESIS_TEST") or
                     os.getenv("RDS_HOST", "")),  # Fallback to old name

            rds_port=int(os.getenv("RDS_PORT", "5432")),

            rds_database=(os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW") or
                         os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                         os.getenv("RDS_DATABASE_NBA_MCP_SYNTHESIS_TEST") or
                         os.getenv("RDS_DATABASE", "nba_simulator")),  # Fallback to old name

            rds_username=(os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_WORKFLOW") or
                         os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                         os.getenv("RDS_USERNAME_NBA_MCP_SYNTHESIS_TEST") or
                         os.getenv("RDS_USERNAME", "")),  # Fallback to old name

            rds_password=(os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_WORKFLOW") or
                         os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                         os.getenv("RDS_PASSWORD_NBA_MCP_SYNTHESIS_TEST") or
                         os.getenv("RDS_PASSWORD", "")),  # Fallback to old name

            # S3 - Try new naming convention first, then fallback to old
            s3_bucket=(os.getenv("S3_BUCKET_NBA_MCP_SYNTHESIS_WORKFLOW") or
                      os.getenv("S3_BUCKET_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                      os.getenv("S3_BUCKET_NBA_MCP_SYNTHESIS_TEST") or
                      os.getenv("S3_BUCKET", "nba-mcp-books-20251011")),  # Fallback to old name

            s3_region=(os.getenv("S3_REGION_NBA_MCP_SYNTHESIS_WORKFLOW") or
                      os.getenv("S3_REGION_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                      os.getenv("S3_REGION_NBA_MCP_SYNTHESIS_TEST") or
                      os.getenv("S3_REGION", "us-east-1")),  # Fallback to old name

            # Glue - Try new naming convention first, then fallback to old
            glue_database=(os.getenv("GLUE_DATABASE_NBA_MCP_SYNTHESIS_WORKFLOW") or
                          os.getenv("GLUE_DATABASE_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                          os.getenv("GLUE_DATABASE_NBA_MCP_SYNTHESIS_TEST") or
                          os.getenv("GLUE_DATABASE", "nba_raw_data")),  # Fallback to old name

            glue_region=(os.getenv("GLUE_REGION_NBA_MCP_SYNTHESIS_WORKFLOW") or
                        os.getenv("GLUE_REGION_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                        os.getenv("GLUE_REGION_NBA_MCP_SYNTHESIS_TEST") or
                        os.getenv("GLUE_REGION", "us-east-1")),  # Fallback to old name

            # Paths
            project_root=os.getenv("PROJECT_ROOT", "/Users/ryanranft/nba-simulator-aws"),
            synthesis_output_dir=synthesis_dir,

            # Slack - Try new naming convention first, then fallback to old
            slack_webhook_url=(os.getenv("SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_WORKFLOW") or
                              os.getenv("SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                              os.getenv("SLACK_WEBHOOK_URL_NBA_MCP_SYNTHESIS_TEST") or
                              os.getenv("SLACK_WEBHOOK_URL")),  # Fallback to old name

            notify_on_success=os.getenv("SLACK_NOTIFY_SUCCESS", "false").lower() == "true",

            # Limits
            max_query_rows=int(os.getenv("MAX_QUERY_ROWS", "1000")),
            max_file_size_bytes=int(os.getenv("MAX_FILE_SIZE_MB", "1")) * 1024 * 1024,
            query_timeout_seconds=int(os.getenv("QUERY_TIMEOUT_SECONDS", "30")),
            max_context_tokens=int(os.getenv("MAX_CONTEXT_TOKENS", "4000")),

            # Performance
            cache_enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),

            # Logging
            log_file=os.getenv("LOG_FILE", "logs/mcp_synthesis.log"),
            log_level=os.getenv("MCP_LOG_LEVEL", "INFO")
        )

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Check required AWS credentials
        if not self.rds_host:
            errors.append("RDS_HOST is required")
        if not self.rds_username:
            errors.append("RDS_USERNAME is required")
        if not self.rds_password:
            errors.append("RDS_PASSWORD is required")

        # Check paths exist
        if self.project_root and not Path(self.project_root).exists():
            errors.append(f"PROJECT_ROOT does not exist: {self.project_root}")

        # Check AWS credentials - Try new naming convention first, then fallback to old
        aws_access_key = (os.getenv("AWS_ACCESS_KEY_ID_NBA_MCP_SYNTHESIS_WORKFLOW") or
                         os.getenv("AWS_ACCESS_KEY_ID_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                         os.getenv("AWS_ACCESS_KEY_ID_NBA_MCP_SYNTHESIS_TEST") or
                         os.getenv("AWS_ACCESS_KEY_ID"))  # Fallback to old name

        aws_secret_key = (os.getenv("AWS_SECRET_ACCESS_KEY_NBA_MCP_SYNTHESIS_WORKFLOW") or
                         os.getenv("AWS_SECRET_ACCESS_KEY_NBA_MCP_SYNTHESIS_DEVELOPMENT") or
                         os.getenv("AWS_SECRET_ACCESS_KEY_NBA_MCP_SYNTHESIS_TEST") or
                         os.getenv("AWS_SECRET_ACCESS_KEY"))  # Fallback to old name

        if not aws_access_key:
            errors.append("AWS_ACCESS_KEY_ID is required")
        if not aws_secret_key:
            errors.append("AWS_SECRET_ACCESS_KEY is required")

        return errors

    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            "server": {
                "host": self.host,
                "port": self.port
            },
            "rds": {
                "host": self.rds_host,
                "port": self.rds_port,
                "database": self.rds_database,
                "username": self.rds_username,
                "connected": bool(self.rds_host and self.rds_username)
            },
            "s3": {
                "bucket": self.s3_bucket,
                "region": self.s3_region
            },
            "glue": {
                "database": self.glue_database,
                "region": self.glue_region
            },
            "project": {
                "root": self.project_root,
                "output_dir": self.synthesis_output_dir
            },
            "limits": {
                "max_query_rows": self.max_query_rows,
                "max_file_size_mb": self.max_file_size_bytes / 1024 / 1024,
                "query_timeout": self.query_timeout_seconds,
                "max_context_tokens": self.max_context_tokens
            },
            "features": {
                "cache_enabled": self.cache_enabled,
                "slack_enabled": bool(self.slack_webhook_url)
            }
        }
