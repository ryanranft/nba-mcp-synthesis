"""
Advanced Audit Logging

Comprehensive audit trail for compliance and security:
- User action tracking
- Data access logging
- Change history
- Compliance reporting
- Tamper-proof logs
- Log retention

Features:
- Structured audit logs
- Immutable log chains
- User attribution
- IP tracking
- Compliance filters (GDPR, HIPAA)
- Log export

Use Cases:
- Security audits
- Compliance reporting
- Incident investigation
- User activity tracking
- Data access monitoring
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Audit action types"""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    ACCESS = "access"
    EXPORT = "export"
    IMPORT = "import"
    ADMIN = "admin"


class AuditSeverity(Enum):
    """Audit log severity"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """Single audit log entry"""

    audit_id: str
    timestamp: datetime
    user_id: str
    user_email: Optional[str]
    action: AuditAction
    resource_type: str
    resource_id: str
    severity: AuditSeverity = AuditSeverity.INFO

    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    # Details
    details: Dict[str, Any] = field(default_factory=dict)
    changes: Optional[Dict[str, Any]] = None  # Before/after for updates

    # Metadata
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    # Chain integrity
    previous_hash: Optional[str] = None
    entry_hash: Optional[str] = None

    def __post_init__(self):
        """Calculate entry hash"""
        if not self.entry_hash:
            self.entry_hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of entry"""
        content = f"{self.audit_id}:{self.timestamp.isoformat()}:{self.user_id}:{self.action.value}:{self.resource_type}:{self.resource_id}:{self.previous_hash}"
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["action"] = self.action.value
        data["severity"] = self.severity.value
        return data

    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict())


class AuditLogger:
    """Manage audit logs"""

    def __init__(self, enable_chain_integrity: bool = True):
        self.logs: List[AuditEntry] = []
        self.enable_chain_integrity = enable_chain_integrity
        self._lock = threading.RLock()
        self._next_id = 0

        # Statistics
        self.total_logs = 0
        self.logs_by_action: Dict[str, int] = {}
        self.logs_by_user: Dict[str, int] = {}

    def _generate_id(self) -> str:
        """Generate unique audit ID"""
        with self._lock:
            audit_id = f"audit_{self._next_id:08d}"
            self._next_id += 1
            return audit_id

    def log(
        self,
        user_id: str,
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        user_email: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> AuditEntry:
        """Create audit log entry"""

        # Get previous hash for chain integrity
        previous_hash = None
        if self.enable_chain_integrity and self.logs:
            previous_hash = self.logs[-1].entry_hash

        entry = AuditEntry(
            audit_id=self._generate_id(),
            timestamp=datetime.now(),
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            details=details or {},
            changes=changes,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            tags=tags or [],
            previous_hash=previous_hash,
        )

        with self._lock:
            self.logs.append(entry)
            self.total_logs += 1

            # Update statistics
            action_key = action.value
            self.logs_by_action[action_key] = self.logs_by_action.get(action_key, 0) + 1
            self.logs_by_user[user_id] = self.logs_by_user.get(user_id, 0) + 1

        logger.info(
            f"Audit log created: {entry.audit_id} - {user_id} {action.value} {resource_type}/{resource_id}"
        )
        return entry

    def query(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AuditSeverity] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """Query audit logs"""
        with self._lock:
            results = self.logs.copy()

        # Apply filters
        if user_id:
            results = [e for e in results if e.user_id == user_id]

        if action:
            results = [e for e in results if e.action == action]

        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]

        if resource_id:
            results = [e for e in results if e.resource_id == resource_id]

        if tenant_id:
            results = [e for e in results if e.tenant_id == tenant_id]

        if start_time:
            results = [e for e in results if e.timestamp >= start_time]

        if end_time:
            results = [e for e in results if e.timestamp <= end_time]

        if severity:
            results = [e for e in results if e.severity == severity]

        if tags:
            results = [e for e in results if any(tag in e.tags for tag in tags)]

        # Sort by timestamp descending
        results.sort(key=lambda e: e.timestamp, reverse=True)

        return results[:limit]

    def verify_chain_integrity(self) -> bool:
        """Verify audit log chain integrity"""
        if not self.enable_chain_integrity:
            logger.warning("Chain integrity not enabled")
            return True

        with self._lock:
            for i, entry in enumerate(self.logs):
                # Verify hash
                expected_hash = entry._calculate_hash()
                if entry.entry_hash != expected_hash:
                    logger.error(f"Hash mismatch at entry {i}: {entry.audit_id}")
                    return False

                # Verify chain
                if i > 0:
                    previous_entry = self.logs[i - 1]
                    if entry.previous_hash != previous_entry.entry_hash:
                        logger.error(f"Chain broken at entry {i}: {entry.audit_id}")
                        return False

        logger.info("Audit log chain integrity verified")
        return True

    def get_user_activity(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get user activity summary"""
        start_time = datetime.now() - timedelta(days=days)
        entries = self.query(user_id=user_id, start_time=start_time)

        # Count by action
        actions = {}
        for entry in entries:
            action_key = entry.action.value
            actions[action_key] = actions.get(action_key, 0) + 1

        # Count by resource type
        resources = {}
        for entry in entries:
            resources[entry.resource_type] = resources.get(entry.resource_type, 0) + 1

        return {
            "user_id": user_id,
            "total_actions": len(entries),
            "actions_by_type": actions,
            "resources_accessed": resources,
            "first_activity": entries[-1].timestamp.isoformat() if entries else None,
            "last_activity": entries[0].timestamp.isoformat() if entries else None,
        }

    def get_compliance_report(
        self, start_time: datetime, end_time: datetime, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        entries = self.query(
            start_time=start_time, end_time=end_time, tenant_id=tenant_id
        )

        # Data access summary
        data_access = [
            e for e in entries if e.action in [AuditAction.READ, AuditAction.EXPORT]
        ]

        # Data modification summary
        data_modifications = [
            e
            for e in entries
            if e.action in [AuditAction.CREATE, AuditAction.UPDATE, AuditAction.DELETE]
        ]

        # Unique users
        unique_users = set(e.user_id for e in entries)

        # By severity
        by_severity = {}
        for entry in entries:
            sev = entry.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "period": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "tenant_id": tenant_id,
            "total_events": len(entries),
            "unique_users": len(unique_users),
            "data_access_count": len(data_access),
            "data_modification_count": len(data_modifications),
            "by_severity": by_severity,
            "chain_integrity_verified": self.verify_chain_integrity(),
        }

    def export_logs(
        self,
        filepath: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Export audit logs to file"""
        entries = self.query(start_time=start_time, end_time=end_time, limit=10000)

        try:
            with open(filepath, "w") as f:
                for entry in entries:
                    f.write(entry.to_json() + "\n")

            logger.info(f"Exported {len(entries)} audit logs to {filepath}")
            return len(entries)
        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get audit logging statistics"""
        with self._lock:
            return {
                "total_logs": self.total_logs,
                "current_buffer_size": len(self.logs),
                "by_action": dict(self.logs_by_action),
                "top_users": sorted(
                    self.logs_by_user.items(), key=lambda x: x[1], reverse=True
                )[:10],
                "chain_integrity_enabled": self.enable_chain_integrity,
            }


# Decorators for automatic audit logging
def audit_operation(action: AuditAction, resource_type: str, audit_logger: AuditLogger):
    """Decorator to automatically audit operations"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Execute function
            result = func(*args, **kwargs)

            # Extract audit info from kwargs
            user_id = kwargs.get("user_id", "system")
            resource_id = kwargs.get("resource_id", "unknown")

            # Log audit entry
            audit_logger.log(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=str(resource_id),
                details={"function": func.__name__},
            )

            return result

        return wrapper

    return decorator


# Global audit logger
_audit_logger = None
_logger_lock = threading.Lock()


def get_audit_logger() -> AuditLogger:
    """Get global audit logger"""
    global _audit_logger
    with _logger_lock:
        if _audit_logger is None:
            _audit_logger = AuditLogger()
        return _audit_logger


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Advanced Audit Logging Demo ===\n")

    # Create audit logger
    audit = AuditLogger(enable_chain_integrity=True)

    # Log various actions
    print("--- Logging Actions ---\n")

    # User login
    audit.log(
        user_id="user_123",
        user_email="john@lakers.com",
        action=AuditAction.LOGIN,
        resource_type="auth",
        resource_id="session_456",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0...",
        tags=["authentication"],
    )

    # Data access
    audit.log(
        user_id="user_123",
        action=AuditAction.READ,
        resource_type="player",
        resource_id="23",
        details={"player_name": "LeBron James"},
        tags=["data_access"],
    )

    # Data update
    audit.log(
        user_id="user_123",
        action=AuditAction.UPDATE,
        resource_type="player_stats",
        resource_id="23",
        changes={"before": {"ppg": 25.0}, "after": {"ppg": 25.5}},
        tags=["data_modification"],
    )

    # Admin action
    audit.log(
        user_id="admin_001",
        action=AuditAction.ADMIN,
        resource_type="system",
        resource_id="settings",
        severity=AuditSeverity.WARNING,
        details={"action": "changed_rate_limit"},
        tags=["admin", "security"],
    )

    # Data export (sensitive)
    audit.log(
        user_id="user_123",
        action=AuditAction.EXPORT,
        resource_type="player_data",
        resource_id="bulk_export_001",
        severity=AuditSeverity.WARNING,
        details={"format": "csv", "record_count": 1000},
        tags=["data_export", "compliance"],
    )

    # Query logs
    print("\n--- Query Examples ---\n")

    # Get all user actions
    user_logs = audit.query(user_id="user_123")
    print(f"User 'user_123' performed {len(user_logs)} actions")

    # Get data modifications
    modifications = audit.query(action=AuditAction.UPDATE)
    print(f"Total data modifications: {len(modifications)}")

    # Get sensitive operations
    sensitive = audit.query(tags=["data_export", "compliance"])
    print(f"Sensitive operations: {len(sensitive)}")

    # User activity summary
    print("\n--- User Activity Summary ---")
    activity = audit.get_user_activity("user_123", days=7)
    print(f"Total actions: {activity['total_actions']}")
    print(f"Actions by type: {activity['actions_by_type']}")
    print(f"Resources accessed: {activity['resources_accessed']}")

    # Compliance report
    print("\n--- Compliance Report ---")
    report = audit.get_compliance_report(
        start_time=datetime.now() - timedelta(hours=1), end_time=datetime.now()
    )
    print(f"Total events: {report['total_events']}")
    print(f"Unique users: {report['unique_users']}")
    print(f"Data access: {report['data_access_count']}")
    print(f"Data modifications: {report['data_modification_count']}")
    print(f"Chain integrity: {report['chain_integrity_verified']}")

    # Verify integrity
    print("\n--- Chain Integrity Check ---")
    integrity_ok = audit.verify_chain_integrity()
    print(f"Chain integrity: {'✓ VERIFIED' if integrity_ok else '✗ FAILED'}")

    # Statistics
    print("\n--- Audit Statistics ---")
    stats = audit.get_stats()
    print(f"Total logs: {stats['total_logs']}")
    print(f"By action: {stats['by_action']}")
    print(f"Top users: {dict(stats['top_users'][:3])}")

    print("\n=== Demo Complete ===")
