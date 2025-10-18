# Secrets Management Utilities

This document describes the comprehensive utilities for managing secrets, including file permissions, audit logging, and rotation.

## Overview

The secrets management utilities provide:
- File permission management and monitoring
- Comprehensive audit logging
- Automated secrets rotation
- Backup and restore capabilities
- Security monitoring and alerting

## Directory Structure

```
scripts/
├── manage_permissions.sh    # File permission management
├── manage_audit.sh         # Audit logging management
├── manage_rotation.sh      # Secrets rotation management
└── README.md               # This documentation

/var/log/
├── secrets_permissions.log # Permission change log
├── secrets_audit.log       # Audit event log
└── secrets_rotation.log    # Rotation activity log

/var/log/secrets_audit/
├── audit_2024-01-01.log    # Daily audit logs
├── audit_2024-01-02.log    # Daily audit logs
└── ...

/var/backups/secrets/
├── GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env_20240101_020000_pre_rotation
├── GOOGLE_API_KEY_NBA_MCP_SYNTHESIS_WORKFLOW.env_20240101_020500_post_rotation
└── ...

/etc/cron.d/
└── secrets_rotation        # Rotation schedule
```

## File Permission Management

### Overview

The `manage_permissions.sh` script provides comprehensive file permission management for secrets.

### Features

- Set file and directory permissions
- Recursive permission management
- Permission validation and checking
- Audit logging of permission changes
- Permission monitoring
- Automated permission fixing

### Usage

```bash
# Set file permissions
./scripts/manage_permissions.sh set /path/to/secret.env 600

# Set directory permissions
./scripts/manage_permissions.sh setdir /path/to/secrets 700

# Set recursive permissions
./scripts/manage_permissions.sh setrec /path/to/secrets 600 700

# Check file permissions
./scripts/manage_permissions.sh check /path/to/secret.env 600

# Check directory permissions
./scripts/manage_permissions.sh checkdir /path/to/secrets 700

# Fix permissions
./scripts/manage_permissions.sh fix /path/to/secrets

# Audit permissions
./scripts/manage_permissions.sh audit /path/to/secrets

# Generate permission report
./scripts/manage_permissions.sh report /path/to/secrets report.txt

# Monitor permission changes
./scripts/manage_permissions.sh monitor /path/to/secrets
```

### Security Considerations

1. **File Permissions**: Secrets are stored with 600 permissions (owner read/write only)
2. **Directory Permissions**: Secret directories have 700 permissions (owner only)
3. **Audit Logging**: All permission changes are logged
4. **Monitoring**: Real-time monitoring of permission changes
5. **Validation**: Regular validation of permission compliance

## Audit Logging

### Overview

The `manage_audit.sh` script provides comprehensive audit logging for secrets management.

### Features

- Event logging with timestamps
- User activity tracking
- Resource access monitoring
- Failed action detection
- Suspicious activity alerts
- Log search and filtering
- Report generation
- Log retention management

### Usage

```bash
# Initialize audit logging
./scripts/manage_audit.sh init

# Log audit event
./scripts/manage_audit.sh log SECRET_ACCESS /path/to/secret.env $USER READ SUCCESS

# Search audit logs
./scripts/manage_audit.sh search SECRET_ACCESS 2024-01-01 2024-01-31

# Generate audit report
./scripts/manage_audit.sh report report.txt 2024-01-01 2024-01-31

# Clean old audit logs
./scripts/manage_audit.sh clean

# Monitor audit logs
./scripts/manage_audit.sh monitor

# Export audit logs
./scripts/manage_audit.sh export export.txt 2024-01-01 2024-01-31
```

### Audit Events

The system logs the following events:

- **SECRET_ACCESS**: Access to secret files
- **SECRET_MODIFICATION**: Changes to secret files
- **PERMISSION_CHANGE**: Changes to file permissions
- **ROTATION_EVENT**: Secrets rotation activities
- **BACKUP_EVENT**: Backup and restore operations
- **FAILED_ACTION**: Failed operations
- **SUSPICIOUS_ACTIVITY**: Potentially malicious activities

### Log Format

Each audit log entry follows this format:
```
timestamp|event_type|resource|user|action|result|details
```

Example:
```
2024-01-01T02:00:00Z|SECRET_ACCESS|/path/to/secret.env|user1|READ|SUCCESS|API key accessed
```

## Secrets Rotation

### Overview

The `manage_rotation.sh` script provides automated secrets rotation capabilities.

### Features

- Automated API key rotation
- Scheduled rotation (daily, weekly, monthly)
- Backup before rotation
- Restore from backup
- Notification system
- Rotation status monitoring
- Cleanup of old backups

### Usage

```bash
# Initialize rotation system
./scripts/manage_rotation.sh init

# Rotate specific API key
./scripts/manage_rotation.sh rotate GOOGLE NBA_MCP_SYNTHESIS WORKFLOW

# Rotate all API keys
./scripts/manage_rotation.sh rotate-all NBA_MCP_SYNTHESIS DEVELOPMENT

# Run scheduled rotations
./scripts/manage_rotation.sh rotate-daily
./scripts/manage_rotation.sh rotate-weekly
./scripts/manage_rotation.sh rotate-monthly

# Backup secret
./scripts/manage_rotation.sh backup /path/to/secret.env pre_rotation

# Restore from backup
./scripts/manage_rotation.sh restore /path/to/secret.env /path/to/backup.env

# List available backups
./scripts/manage_rotation.sh list-backups GOOGLE_API_KEY

# Clean old backups
./scripts/manage_rotation.sh clean 30

# Show rotation status
./scripts/manage_rotation.sh status
```

### Rotation Schedule

The system supports three rotation schedules:

1. **Daily**: Development API keys (2 AM daily)
2. **Weekly**: Test API keys (Sunday 3 AM)
3. **Monthly**: Production API keys (1st of month 4 AM)

### Supported Services

- **GOOGLE**: Google Cloud API keys
- **ANTHROPIC**: Anthropic API keys
- **DEEPSEEK**: DeepSeek API keys
- **OPENAI**: OpenAI API keys

### Backup Strategy

- **Pre-rotation**: Backup before rotation
- **Post-rotation**: Backup after successful rotation
- **Retention**: Configurable retention period
- **Compression**: Automatic compression of old backups

## Security Considerations

### File Permissions

1. **Secrets**: 600 permissions (owner read/write only)
2. **Directories**: 700 permissions (owner only)
3. **Logs**: 600 permissions (owner read/write only)
4. **Backups**: 600 permissions (owner read/write only)

### Audit Logging

1. **Comprehensive Logging**: All operations are logged
2. **User Tracking**: User identity is recorded
3. **Resource Monitoring**: Resource access is tracked
4. **Failed Action Detection**: Failed operations are flagged
5. **Suspicious Activity Alerts**: Unusual patterns are detected

### Rotation Security

1. **Backup Before Rotation**: Always backup before rotation
2. **Notification System**: Alerts for rotation events
3. **Rollback Capability**: Ability to restore from backup
4. **Scheduled Rotation**: Automated rotation schedule
5. **Service Integration**: Integration with service APIs

## Best Practices

### File Permissions

1. **Regular Audits**: Regular permission audits
2. **Monitoring**: Continuous monitoring of permission changes
3. **Validation**: Regular validation of permission compliance
4. **Documentation**: Document permission requirements
5. **Training**: Train users on permission management

### Audit Logging

1. **Comprehensive Coverage**: Log all relevant events
2. **Regular Review**: Regular review of audit logs
3. **Retention Management**: Proper log retention
4. **Access Control**: Restrict access to audit logs
5. **Analysis**: Regular analysis of audit patterns

### Secrets Rotation

1. **Regular Rotation**: Regular rotation of secrets
2. **Backup Strategy**: Comprehensive backup strategy
3. **Testing**: Test rotation procedures
4. **Documentation**: Document rotation procedures
5. **Monitoring**: Monitor rotation success

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Check file permissions
   - Verify user ownership
   - Check directory permissions

2. **Audit Log Issues**
   - Check log file permissions
   - Verify log directory exists
   - Check disk space

3. **Rotation Failures**
   - Check API key validity
   - Verify service connectivity
   - Check backup availability

### Debugging

1. **Check Logs**: Review relevant log files
2. **Verify Permissions**: Check file and directory permissions
3. **Test Connectivity**: Test service connectivity
4. **Validate Configuration**: Verify configuration settings
5. **Check Resources**: Verify resource availability

## Integration

### CI/CD Integration

The utilities can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Secrets Management
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  rotate-secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Rotate Secrets
        run: ./scripts/manage_rotation.sh rotate-daily
      - name: Audit Permissions
        run: ./scripts/manage_permissions.sh audit /path/to/secrets
```

### Monitoring Integration

The utilities can be integrated with monitoring systems:

```bash
# Example monitoring script
#!/bin/bash
# Check for failed rotations
if grep -q "FAILED" /var/log/secrets_rotation.log; then
    # Send alert
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"Secrets rotation failed"}' \
        "$SLACK_WEBHOOK_URL"
fi

# Check for permission violations
if ./scripts/manage_permissions.sh check /path/to/secrets 700 | grep -q "MISMATCH"; then
    # Send alert
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"Permission violation detected"}' \
        "$SLACK_WEBHOOK_URL"
fi
```

This comprehensive utilities system provides enterprise-grade secrets management with security, auditability, and automation.


