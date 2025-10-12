"""Data Privacy & PII Protection"""
import hashlib
import re
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# PII Detection Patterns
PII_PATTERNS = {
    'ssn': re.compile(r'\d{3}-\d{2}-\d{4}'),
    'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    'phone': re.compile(r'\d{3}-\d{3}-\d{4}'),
    'credit_card': re.compile(r'\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}'),
}


def anonymize_pii(text: str, replacement: str = "***") -> str:
    """Remove PII from text"""
    result = text
    for pii_type, pattern in PII_PATTERNS.items():
        result = pattern.sub(replacement, result)
    return result


def hash_pii(value: str, salt: Optional[str] = None) -> str:
    """Hash PII for storage (one-way)"""
    if salt:
        value = f"{value}{salt}"
    return hashlib.sha256(value.encode()).hexdigest()


def mask_data(data: Dict[str, Any], fields_to_mask: List[str]) -> Dict[str, Any]:
    """Mask sensitive fields in dictionary"""
    masked = data.copy()
    for field in fields_to_mask:
        if field in masked:
            masked[field] = "***MASKED***"
    return masked


class PrivacyAudit:
    """Audit trail for data access"""

    def __init__(self):
        self.access_log = []

    def log_access(self, user_id: str, resource: str, action: str):
        """Log data access"""
        self.access_log.append({
            'user_id': user_id,
            'resource': resource,
            'action': action,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        })
        logger.info(f"📋 Access: {user_id} {action} {resource}")


# Global audit instance
_privacy_audit = PrivacyAudit()


def get_privacy_audit() -> PrivacyAudit:
    """Get global privacy audit instance"""
    return _privacy_audit

