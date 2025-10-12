"""
API Authentication & Authorization for NBA MCP
Implements JWT tokens and API key authentication
"""
import jwt
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Role(Enum):
    """User roles for authorization"""
    ADMIN = "admin"
    USER = "user"
    READ_ONLY = "read_only"
    SERVICE = "service"  # For service-to-service auth


class JWTAuth:
    """JWT token management"""

    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        """
        Initialize JWT authentication

        Args:
            secret_key: Secret key for signing tokens (generate if None)
            algorithm: JWT algorithm (default HS256)
        """
        self.secret_key = secret_key or self._generate_secret_key()
        self.algorithm = algorithm
        self.token_expiry_hours = 24  # Tokens expire after 24 hours

    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key"""
        return secrets.token_urlsafe(32)

    def create_token(
        self,
        user_id: str,
        role: Role,
        custom_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a JWT token

        Args:
            user_id: Unique user identifier
            role: User role
            custom_claims: Additional claims to include

        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        expiry = now + timedelta(hours=self.token_expiry_hours)

        payload = {
            "sub": user_id,  # Subject (user ID)
            "role": role.value,
            "iat": now,  # Issued at
            "exp": expiry,  # Expiration
            "jti": secrets.token_urlsafe(16),  # JWT ID (unique token identifier)
        }

        # Add custom claims
        if custom_claims:
            payload.update(custom_claims)

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"✅ Created JWT token for user: {user_id} (role: {role.value})")

        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"require": ["sub", "role", "exp"]}
            )

            logger.debug(f"✅ Token verified for user: {payload['sub']}")
            return payload

        except jwt.ExpiredSignatureError:
            logger.warning("❌ Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"❌ Invalid token: {e}")
            return None

    def refresh_token(self, old_token: str) -> Optional[str]:
        """
        Refresh an existing token (if not expired)

        Args:
            old_token: Existing JWT token

        Returns:
            New token if successful, None if invalid
        """
        payload = self.verify_token(old_token)
        if not payload:
            return None

        # Create new token with same user_id and role
        new_token = self.create_token(
            user_id=payload["sub"],
            role=Role(payload["role"]),
            custom_claims={k: v for k, v in payload.items()
                          if k not in ["sub", "role", "iat", "exp", "jti"]}
        )

        logger.info(f"🔄 Refreshed token for user: {payload['sub']}")
        return new_token


class APIKeyAuth:
    """API Key authentication"""

    def __init__(self):
        """Initialize API key authentication"""
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        # In production, store in database or Secrets Manager

    def generate_api_key(
        self,
        name: str,
        role: Role,
        expires_days: Optional[int] = None
    ) -> str:
        """
        Generate a new API key

        Args:
            name: Name/description for this API key
            role: Role for this API key
            expires_days: Days until expiration (None = never expires)

        Returns:
            API key string
        """
        # Generate secure random API key
        api_key = f"nba_mcp_{secrets.token_urlsafe(32)}"

        # Hash the key for storage (never store plain text)
        key_hash = self._hash_api_key(api_key)

        # Calculate expiry
        expiry = None
        if expires_days:
            expiry = datetime.utcnow() + timedelta(days=expires_days)

        # Store hashed key with metadata
        self.api_keys[key_hash] = {
            "name": name,
            "role": role.value,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expiry.isoformat() if expiry else None,
            "last_used": None,
            "use_count": 0
        }

        logger.info(f"✅ Generated API key: {name} (role: {role.value})")

        # Return unhashed key to user (only time they'll see it)
        return api_key

    def _hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Verify an API key

        Args:
            api_key: API key to verify

        Returns:
            Key metadata if valid, None if invalid
        """
        key_hash = self._hash_api_key(api_key)

        if key_hash not in self.api_keys:
            logger.warning("❌ Invalid API key")
            return None

        metadata = self.api_keys[key_hash]

        # Check expiry
        if metadata["expires_at"]:
            expiry = datetime.fromisoformat(metadata["expires_at"])
            if datetime.utcnow() > expiry:
                logger.warning(f"❌ Expired API key: {metadata['name']}")
                return None

        # Update usage stats
        metadata["last_used"] = datetime.utcnow().isoformat()
        metadata["use_count"] += 1

        logger.debug(f"✅ Valid API key: {metadata['name']}")
        return metadata

    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key

        Args:
            api_key: API key to revoke

        Returns:
            True if revoked, False if not found
        """
        key_hash = self._hash_api_key(api_key)

        if key_hash in self.api_keys:
            name = self.api_keys[key_hash]["name"]
            del self.api_keys[key_hash]
            logger.info(f"🗑️  Revoked API key: {name}")
            return True

        return False

    def list_api_keys(self) -> List[Dict[str, Any]]:
        """
        List all API keys (without the actual keys)

        Returns:
            List of API key metadata
        """
        return list(self.api_keys.values())


class Authorization:
    """Role-based authorization"""

    # Define what each role can do
    PERMISSIONS = {
        Role.ADMIN: {
            "read": True,
            "write": True,
            "delete": True,
            "manage_users": True,
            "view_metrics": True
        },
        Role.USER: {
            "read": True,
            "write": True,
            "delete": False,
            "manage_users": False,
            "view_metrics": True
        },
        Role.READ_ONLY: {
            "read": True,
            "write": False,
            "delete": False,
            "manage_users": False,
            "view_metrics": True
        },
        Role.SERVICE: {
            "read": True,
            "write": True,
            "delete": False,
            "manage_users": False,
            "view_metrics": False
        }
    }

    @classmethod
    def can_perform(cls, role: Role, action: str) -> bool:
        """
        Check if a role can perform an action

        Args:
            role: User role
            action: Action to check (e.g., "read", "write", "delete")

        Returns:
            True if authorized, False otherwise
        """
        permissions = cls.PERMISSIONS.get(role, {})
        return permissions.get(action, False)

    @classmethod
    def require_permission(cls, role: Role, action: str):
        """
        Decorator to require a specific permission

        Args:
            role: User role
            action: Required action

        Raises:
            PermissionError if not authorized
        """
        if not cls.can_perform(role, action):
            raise PermissionError(
                f"Role '{role.value}' does not have permission for '{action}'"
            )


# Global instances
_jwt_auth: Optional[JWTAuth] = None
_api_key_auth: Optional[APIKeyAuth] = None


def get_jwt_auth() -> JWTAuth:
    """Get or create global JWT auth instance"""
    global _jwt_auth
    if _jwt_auth is None:
        # In production, get secret from Secrets Manager
        _jwt_auth = JWTAuth()
    return _jwt_auth


def get_api_key_auth() -> APIKeyAuth:
    """Get or create global API key auth instance"""
    global _api_key_auth
    if _api_key_auth is None:
        _api_key_auth = APIKeyAuth()
    return _api_key_auth


def authenticate_request(
    token: Optional[str] = None,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Authenticate a request using JWT or API key

    Args:
        token: JWT token (from Authorization: Bearer header)
        api_key: API key (from X-API-Key header)

    Returns:
        User info if authenticated, None otherwise
    """
    # Try JWT first
    if token:
        jwt_auth = get_jwt_auth()
        payload = jwt_auth.verify_token(token)
        if payload:
            return {
                "user_id": payload["sub"],
                "role": Role(payload["role"]),
                "auth_method": "jwt",
                "payload": payload
            }

    # Try API key
    if api_key:
        api_auth = get_api_key_auth()
        metadata = api_auth.verify_api_key(api_key)
        if metadata:
            return {
                "user_id": metadata["name"],
                "role": Role(metadata["role"]),
                "auth_method": "api_key",
                "metadata": metadata
            }

    logger.warning("❌ Authentication failed: no valid token or API key")
    return None

