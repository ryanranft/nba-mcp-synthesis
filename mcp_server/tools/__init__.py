"""
MCP Server Tools
Provides tools for database, S3, file operations, and actions
"""

try:
    from mcp_server.tools.database_tools import DatabaseTools
    from mcp_server.tools.s3_tools import S3Tools
    from mcp_server.tools.file_tools import FileTools
    from mcp_server.tools.action_tools import ActionTools
    from mcp_server.tools.glue_tools import GlueTools

    # Sprint 7 & 8: ML Tools (imported as modules)
    from mcp_server.tools import (
        ml_clustering_helper,
        ml_classification_helper,
        ml_anomaly_helper,
        ml_feature_helper,
        ml_evaluation_helper,
        ml_validation_helper
    )
except ImportError:
    # Fallback for when running as standalone script
    from .database_tools import DatabaseTools
    from .s3_tools import S3Tools
    from .file_tools import FileTools
    from .action_tools import ActionTools
    from .glue_tools import GlueTools

    # Sprint 7 & 8: ML Tools (imported as modules)
    from . import (
        ml_clustering_helper,
        ml_classification_helper,
        ml_anomaly_helper,
        ml_feature_helper,
        ml_evaluation_helper,
        ml_validation_helper
    )

__all__ = [
    'DatabaseTools',
    'S3Tools',
    'FileTools',
    'ActionTools',
    'GlueTools',
    'ml_clustering_helper',
    'ml_classification_helper',
    'ml_anomaly_helper',
    'ml_feature_helper',
    'ml_evaluation_helper',
    'ml_validation_helper'
]
