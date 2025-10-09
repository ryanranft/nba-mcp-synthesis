#!/bin/bash

# Script to copy planning documents to project directory
# Created: 2025-10-09

PROJECT_DIR="/Users/ryanranft/nba-mcp-synthesis"
DOCS_DIR="$PROJECT_DIR/docs/planning"

# Create docs/planning directory if it doesn't exist
mkdir -p "$DOCS_DIR"

echo "Copying planning documents to $DOCS_DIR..."

# Copy the three documents
cp "/Users/ryanranft/Downloads/MCP_MULTI_MODEL_PROJECT_PLAN.md" "$DOCS_DIR/" && \
  echo "✅ Copied MCP_MULTI_MODEL_PROJECT_PLAN.md"

cp "/Users/ryanranft/Downloads/CONNECTOR_INTEGRATION_PLANS.md" "$DOCS_DIR/" && \
  echo "✅ Copied CONNECTOR_INTEGRATION_PLANS.md"

cp "/Users/ryanranft/Downloads/Progressive_Fidelity_NBA_Simulator_Complete_Guide_CORRECTED.md" "$DOCS_DIR/" && \
  echo "✅ Copied Progressive_Fidelity_NBA_Simulator_Complete_Guide_CORRECTED.md"

echo ""
echo "All documents copied successfully to docs/planning/"
echo ""
echo "Files:"
ls -lh "$DOCS_DIR"