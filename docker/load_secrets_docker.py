#!/usr/bin/env python3
"""
Docker Secrets Loader for NBA MCP Synthesis

Loads secrets using the unified secrets manager with hierarchical loading.
Supports both Docker secrets and the new hierarchical structure.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    project = os.getenv('PROJECT_NAME', 'nba-mcp-synthesis')
    sport = os.getenv('SPORT_NAME', 'NBA')
    context = os.getenv('NBA_MCP_CONTEXT', 'WORKFLOW')

    logger.info(f"Loading secrets for project={project}, sport={sport}, context={context}")

    # Load secrets using unified secrets manager
    success = load_secrets_hierarchical(project, sport, context)

    if success:
        logger.info("✅ Secrets loaded successfully")

        # Verify critical secrets are loaded
        critical_secrets = [
            'GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
            'ANTHROPIC_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW',
            'DEEPSEEK_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW'
        ]

        missing_secrets = []
        for secret_name in critical_secrets:
            if not os.getenv(secret_name):
                missing_secrets.append(secret_name)

        if missing_secrets:
            logger.warning(f"⚠️  Some critical secrets are missing: {missing_secrets}")
        else:
            logger.info("✅ All critical secrets are present")

    else:
        logger.error("❌ Failed to load secrets")
        sys.exit(1)

if __name__ == '__main__':
    main()
