#!/bin/bash
#
# NBA MCP Synthesis - Rollback Script
#

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${PROJECT_DIR}/deploy/backups"

echo "========================================="
echo "NBA MCP Synthesis - Rollback"
echo "========================================="
echo ""

# List available backups
if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR)" ]; then
    echo "❌ No backups found in $BACKUP_DIR"
    exit 1
fi

echo "Available backups:"
ls -1t "$BACKUP_DIR"
echo ""

echo "Enter backup filename to restore (or 'cancel' to abort):"
read -r BACKUP_FILE

if [ "$BACKUP_FILE" = "cancel" ]; then
    echo "Rollback cancelled"
    exit 0
fi

BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"

if [ ! -f "$BACKUP_PATH" ]; then
    echo "❌ Backup file not found: $BACKUP_PATH"
    exit 1
fi

# Restore backup
echo "Restoring $BACKUP_FILE..."
cp "$BACKUP_PATH" "$PROJECT_DIR/.env"

echo "✅ Rollback complete"
echo ""
echo "Please restart the MCP server for changes to take effect."

exit 0
