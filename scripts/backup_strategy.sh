#!/bin/bash
# Automated Backup Strategy for NBA MCP
# CRITICAL 5: Automated Backup Strategy

set -e

echo "🔄 NBA MCP Backup Strategy"
echo "=" * 80

# Configuration
RDS_INSTANCE="nba-stats"
S3_BACKUP_BUCKET="nba-mcp-backups-$(date +%Y%m%d)"
REGION="us-east-1"
RETENTION_DAYS=30

# 1. Enable RDS Automated Backups
echo "📦 Configuring RDS automated backups..."
aws rds modify-db-instance \
    --db-instance-identifier ${RDS_INSTANCE} \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00" \
    --region ${REGION} \
    --apply-immediately

echo "✅ RDS backups configured (7-day retention)"

# 2. Create manual RDS snapshot
echo "📸 Creating manual RDS snapshot..."
aws rds create-db-snapshot \
    --db-instance-identifier ${RDS_INSTANCE} \
    --db-snapshot-identifier "${RDS_INSTANCE}-$(date +%Y%m%d-%H%M%S)" \
    --region ${REGION}

echo "✅ Manual snapshot created"

# 3. Enable S3 versioning
echo "📂 Enabling S3 versioning..."
aws s3api put-bucket-versioning \
    --bucket nba-mcp-books-20251011 \
    --versioning-configuration Status=Enabled \
    --region ${REGION}

echo "✅ S3 versioning enabled"

# 4. Configure S3 lifecycle policy
echo "🗓️  Configuring S3 lifecycle policy..."
cat > /tmp/lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 30
      }
    },
    {
      "Id": "MoveToGlacier",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
    --bucket nba-mcp-books-20251011 \
    --lifecycle-configuration file:///tmp/lifecycle.json \
    --region ${REGION}

echo "✅ S3 lifecycle policy configured"

# 5. Backup application code
echo "💾 Backing up application code..."
tar -czf "/tmp/nba-mcp-backup-$(date +%Y%m%d).tar.gz" \
    --exclude='venv' --exclude='__pycache__' --exclude='.git' \
    /Users/ryanranft/nba-mcp-synthesis

echo "✅ Code backup created"

# 6. Setup automated backup cron job
echo "⏰ Setting up automated backups..."
CRON_JOB="0 2 * * * /Users/ryanranft/nba-mcp-synthesis/scripts/backup_strategy.sh >> /var/log/nba-mcp-backup.log 2>&1"

# Add to crontab if not already present
(crontab -l 2>/dev/null | grep -v backup_strategy.sh; echo "$CRON_JOB") | crontab -

echo "✅ Daily backup cron job configured (2 AM)"

echo ""
echo "=" * 80
echo "🎉 Backup strategy complete!"
echo ""
echo "Configured:"
echo "  ✅ RDS automated backups (7-day retention)"
echo "  ✅ S3 versioning enabled"
echo "  ✅ S3 lifecycle policy (30-day versions, 90-day Glacier)"
echo "  ✅ Daily automated backups at 2 AM"
echo ""
echo "To restore:"
echo "  RDS: aws rds restore-db-instance-from-db-snapshot --db-snapshot-identifier SNAPSHOT_ID"
echo "  S3: aws s3api get-object --bucket BUCKET --key KEY --version-id VERSION_ID"

