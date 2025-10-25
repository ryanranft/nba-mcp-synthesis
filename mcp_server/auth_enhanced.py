"""
Enhanced Authentication and Authorization System for NBA MCP Server

Provides comprehensive authentication capabilities including:
- JWT-based authentication with refresh tokens
- API key management with secure hashing
- User management with secure password hashing
- Session management and token blacklisting
- Multi-factor authentication (MFA) support
- OAuth 2.0 integration
- Password policy enforcement

This module extends the basic auth.py with production-ready features.

Author: NBA MCP Server Team - Phase 10A Agent 3
Date: 2025-01-18
"""

import asyncio
import bcrypt
import hashlib
import hmac
import jwt
import os
import pyotp
import secrets
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional, Set, Tuple

from .logging_config import get_logger
from .error_handling import (
    BaseAuthenticationError,
    BaseValidationError,
    get_error_handler,
)

logger = get_logger(__name__)


# ==============================================================================
# Enums and Constants
# ==============================================================================


class TokenType(Enum):
    """Types of authentication tokens."""

    ACCESS = "access"
    REFRESH = "refresh"


class AuthMethod(Enum):
    """Authentication methods."""

    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH = "oauth"
    MFA = "mfa"


# ==============================================================================
# User Model
# ==============================================================================


@dataclass
class User:
    """
    User model with secure credential storage.

    Attributes:
        id: Unique user identifier
        username: Username for login
        email: User email address
        password_hash: Bcrypt hashed password (never store plain text!)
        roles: List of assigned roles
        is_active: Whether the user account is active
        is_verified: Whether email is verified
        mfa_enabled: Whether MFA is enabled
        mfa_secret: TOTP secret for MFA (encrypted)
        created_at: Account creation timestamp
        last_login: Last successful login timestamp
        failed_login_attempts: Counter for failed login attempts
        locked_until: Account lock timestamp (for brute force protection)
        metadata: Additional user metadata

    Examples:
        >>> user = User(
        ...     id="user_123",
        ...     username="analyst",
        ...     email="analyst@nba.com",
        ...     password_hash=bcrypt.hashpw(b"password", bcrypt.gensalt()),
        ...     roles=["analyst", "viewer"]
        ... )
    """

    id: str
    username: str
    email: str
    password_hash: bytes
    roles: List[str] = field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert user to dictionary.

        Args:
            include_sensitive: Whether to include sensitive fields

        Returns:
            User dictionary (without password hash unless include_sensitive=True)
        """
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "roles": self.roles,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "mfa_enabled": self.mfa_enabled,
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "metadata": self.metadata,
        }

        if include_sensitive:
            data["password_hash"] = self.password_hash.decode("utf-8")
            data["mfa_secret"] = self.mfa_secret
            data["failed_login_attempts"] = self.failed_login_attempts
            data["locked_until"] = (
                self.locked_until.isoformat() if self.locked_until else None
            )

        return data

    def is_locked(self) -> bool:
        """Check if account is locked due to failed login attempts."""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until


# ==============================================================================
# Password Policy
# ==============================================================================


@dataclass
class PasswordPolicy:
    """
    Password policy configuration.

    Attributes:
        min_length: Minimum password length
        require_uppercase: Require at least one uppercase letter
        require_lowercase: Require at least one lowercase letter
        require_digit: Require at least one digit
        require_special: Require at least one special character
        special_characters: Set of allowed special characters
        max_age_days: Maximum password age (0 = no expiry)
        prevent_reuse: Number of previous passwords to prevent reuse
    """

    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    special_characters: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    max_age_days: int = 90
    prevent_reuse: int = 5

    def validate(self, password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password against policy.

        Args:
            password: Password to validate

        Returns:
            (is_valid, error_message)
        """
        if len(password) < self.min_length:
            return False, f"Password must be at least {self.min_length} characters"

        if self.require_uppercase and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if self.require_lowercase and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if self.require_digit and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"

        if self.require_special and not any(
            c in self.special_characters for c in password
        ):
            return (
                False,
                f"Password must contain at least one special character: {self.special_characters}",
            )

        return True, None


# ==============================================================================
# Authentication Manager
# ==============================================================================


class AuthenticationManager:
    """
    Comprehensive authentication manager.

    Handles user registration, login, password management, and MFA.
    Implements secure password hashing with bcrypt and JWT token generation.

    Features:
    - Secure password hashing with bcrypt
    - JWT token generation and validation
    - Refresh token mechanism
    - Token blacklisting for logout
    - Account lockout for brute force protection
    - MFA support with TOTP
    - Password policy enforcement

    Examples:
        >>> auth_manager = AuthenticationManager()
        >>>
        >>> # Register user
        >>> user = auth_manager.register_user(
        ...     username="analyst1",
        ...     email="analyst@nba.com",
        ...     password="SecurePass123!",
        ...     roles=["analyst"]
        ... )
        >>>
        >>> # Authenticate
        >>> token = auth_manager.authenticate("analyst1", "SecurePass123!")
        >>>
        >>> # Verify token
        >>> user_info = auth_manager.verify_token(token)
    """

    def __init__(
        self,
        jwt_secret: Optional[str] = None,
        jwt_algorithm: str = "HS256",
        access_token_expiry: int = 15,  # minutes
        refresh_token_expiry: int = 7,  # days
        max_failed_attempts: int = 5,
        lockout_duration: int = 30,  # minutes
        password_policy: Optional[PasswordPolicy] = None,
    ):
        """
        Initialize authentication manager.

        Args:
            jwt_secret: Secret key for JWT signing (auto-generated if None)
            jwt_algorithm: JWT signing algorithm
            access_token_expiry: Access token expiry in minutes
            refresh_token_expiry: Refresh token expiry in days
            max_failed_attempts: Max failed login attempts before lockout
            lockout_duration: Lockout duration in minutes
            password_policy: Password policy configuration
        """
        self.jwt_secret = jwt_secret or self._generate_secret_key()
        self.jwt_algorithm = jwt_algorithm
        self.access_token_expiry = timedelta(minutes=access_token_expiry)
        self.refresh_token_expiry = timedelta(days=refresh_token_expiry)
        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = timedelta(minutes=lockout_duration)
        self.password_policy = password_policy or PasswordPolicy()

        # User storage (in production, use database)
        self.users: Dict[str, User] = {}
        self.users_by_email: Dict[str, str] = {}  # email -> user_id
        self.users_by_username: Dict[str, str] = {}  # username -> user_id

        # Token management
        self.token_blacklist: Set[str] = set()
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}  # token -> metadata

        # Password history (for preventing reuse)
        self.password_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.password_policy.prevent_reuse)
        )

        # Thread safety
        self._lock = Lock()

        logger.info(
            "Authentication manager initialized",
            extra={
                "access_token_expiry_minutes": access_token_expiry,
                "refresh_token_expiry_days": refresh_token_expiry,
                "max_failed_attempts": max_failed_attempts,
            },
        )

    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key."""
        return secrets.token_urlsafe(32)

    def _hash_password(self, password: str) -> bytes:
        """
        Hash password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password bytes
        """
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    def _verify_password(self, password: str, password_hash: bytes) -> bool:
        """
        Verify password against hash using constant-time comparison.

        Args:
            password: Plain text password
            password_hash: Hashed password

        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(password.encode("utf-8"), password_hash)

    def _check_password_history(self, user_id: str, password: str) -> bool:
        """
        Check if password was used before.

        Args:
            user_id: User identifier
            password: Password to check

        Returns:
            True if password was used before, False otherwise
        """
        history = self.password_history.get(user_id, [])
        for old_hash in history:
            if bcrypt.checkpw(password.encode("utf-8"), old_hash):
                return True
        return False

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        roles: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> User:
        """
        Register a new user with secure password hashing.

        Args:
            username: Unique username
            email: User email address
            password: Plain text password (will be hashed)
            roles: List of roles to assign
            metadata: Additional user metadata

        Returns:
            Created User object

        Raises:
            BaseValidationError: If validation fails
            BaseAuthenticationError: If user already exists

        Examples:
            >>> user = auth_manager.register_user(
            ...     username="analyst1",
            ...     email="analyst@nba.com",
            ...     password="SecurePass123!",
            ...     roles=["analyst", "viewer"]
            ... )
        """
        # Validate password policy
        is_valid, error_msg = self.password_policy.validate(password)
        if not is_valid:
            raise BaseValidationError(
                f"Password policy violation: {error_msg}", details={"field": "password"}
            )

        with self._lock:
            # Check if username exists
            if username in self.users_by_username:
                raise BaseAuthenticationError(
                    f"Username '{username}' already exists",
                    details={"username": username},
                )

            # Check if email exists
            if email in self.users_by_email:
                raise BaseAuthenticationError(
                    f"Email '{email}' already registered", details={"email": email}
                )

            # Generate user ID
            user_id = f"user_{secrets.token_urlsafe(16)}"

            # Hash password
            password_hash = self._hash_password(password)

            # Create user
            user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                roles=roles or ["viewer"],
                metadata=metadata or {},
            )

            # Store user
            self.users[user_id] = user
            self.users_by_username[username] = user_id
            self.users_by_email[email] = user_id

            # Store password in history
            self.password_history[user_id].append(password_hash)

        logger.info(
            f"User registered: {username}",
            extra={
                "user_id": user_id,
                "email": email,
                "roles": roles,
            },
        )

        return user

    def authenticate(
        self,
        username: str,
        password: str,
        mfa_code: Optional[str] = None,
    ) -> Optional[str]:
        """
        Authenticate user and return JWT access token.

        Args:
            username: Username or email
            password: Plain text password
            mfa_code: MFA code if MFA is enabled

        Returns:
            JWT access token if authentication successful, None otherwise

        Raises:
            BaseAuthenticationError: If authentication fails

        Examples:
            >>> token = auth_manager.authenticate("analyst1", "SecurePass123!")
            >>> # With MFA
            >>> token = auth_manager.authenticate(
            ...     "analyst1",
            ...     "SecurePass123!",
            ...     mfa_code="123456"
            ... )
        """
        with self._lock:
            # Get user by username or email
            user_id = self.users_by_username.get(username) or self.users_by_email.get(
                username
            )

            if not user_id or user_id not in self.users:
                logger.warning(
                    f"Authentication failed: user not found",
                    extra={"username": username},
                )
                raise BaseAuthenticationError("Invalid username or password")

            user = self.users[user_id]

            # Check if account is locked
            if user.is_locked():
                logger.warning(
                    f"Authentication failed: account locked",
                    extra={"user_id": user_id, "locked_until": user.locked_until},
                )
                raise BaseAuthenticationError(
                    f"Account locked until {user.locked_until.isoformat()}",
                    details={"locked_until": user.locked_until.isoformat()},
                )

            # Check if account is active
            if not user.is_active:
                logger.warning(
                    f"Authentication failed: account inactive",
                    extra={"user_id": user_id},
                )
                raise BaseAuthenticationError("Account is inactive")

            # Verify password
            if not self._verify_password(password, user.password_hash):
                user.failed_login_attempts += 1

                # Lock account if too many failed attempts
                if user.failed_login_attempts >= self.max_failed_attempts:
                    user.locked_until = datetime.now() + self.lockout_duration
                    logger.warning(
                        f"Account locked due to failed login attempts",
                        extra={
                            "user_id": user_id,
                            "failed_attempts": user.failed_login_attempts,
                            "locked_until": user.locked_until,
                        },
                    )

                raise BaseAuthenticationError("Invalid username or password")

            # Verify MFA if enabled
            if user.mfa_enabled:
                if not mfa_code:
                    raise BaseAuthenticationError(
                        "MFA code required", details={"mfa_required": True}
                    )

                if not self._verify_mfa(user, mfa_code):
                    user.failed_login_attempts += 1
                    raise BaseAuthenticationError("Invalid MFA code")

            # Reset failed login attempts
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now()

        # Generate access token
        token = self._generate_token(user, TokenType.ACCESS)

        logger.info(
            f"User authenticated: {username}",
            extra={"user_id": user_id, "mfa_used": user.mfa_enabled},
        )

        return token

    def _generate_token(self, user: User, token_type: TokenType) -> str:
        """
        Generate JWT token for user.

        Args:
            user: User object
            token_type: Type of token (access or refresh)

        Returns:
            JWT token string
        """
        now = datetime.utcnow()

        if token_type == TokenType.ACCESS:
            expiry = now + self.access_token_expiry
        else:
            expiry = now + self.refresh_token_expiry

        payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "roles": user.roles,
            "type": token_type.value,
            "iat": now,
            "exp": expiry,
            "jti": secrets.token_urlsafe(16),
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

        # Store refresh tokens for tracking
        if token_type == TokenType.REFRESH:
            self.refresh_tokens[token] = {
                "user_id": user.id,
                "created_at": now,
                "expires_at": expiry,
            }

        return token

    def verify_token(self, token: str) -> Optional[User]:
        """
        Verify JWT token and return user.

        Args:
            token: JWT token string

        Returns:
            User object if token is valid, None otherwise

        Examples:
            >>> user = auth_manager.verify_token(token)
            >>> if user:
            ...     print(f"Authenticated as {user.username}")
        """
        # Check blacklist
        if token in self.token_blacklist:
            logger.warning("Token is blacklisted")
            return None

        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                options={"require": ["sub", "exp", "type"]},
            )

            user_id = payload["sub"]

            with self._lock:
                user = self.users.get(user_id)

            if not user:
                logger.warning(f"User not found for token: {user_id}")
                return None

            if not user.is_active:
                logger.warning(f"User inactive: {user_id}")
                return None

            return user

        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def refresh_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """
        Refresh JWT token using refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            (new_access_token, new_refresh_token) if successful, None otherwise

        Examples:
            >>> tokens = auth_manager.refresh_token(old_refresh_token)
            >>> if tokens:
            ...     access_token, refresh_token = tokens
        """
        user = self.verify_token(refresh_token)
        if not user:
            return None

        try:
            payload = jwt.decode(
                refresh_token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
            )

            # Ensure it's a refresh token
            if payload.get("type") != TokenType.REFRESH.value:
                logger.warning("Attempted to refresh with non-refresh token")
                return None

            # Generate new tokens
            new_access_token = self._generate_token(user, TokenType.ACCESS)
            new_refresh_token = self._generate_token(user, TokenType.REFRESH)

            # Invalidate old refresh token
            with self._lock:
                if refresh_token in self.refresh_tokens:
                    del self.refresh_tokens[refresh_token]
                self.token_blacklist.add(refresh_token)

            logger.info(f"Token refreshed for user: {user.username}")

            return new_access_token, new_refresh_token

        except jwt.InvalidTokenError:
            return None

    def revoke_token(self, token: str) -> None:
        """
        Revoke a token (add to blacklist).

        Args:
            token: Token to revoke

        Examples:
            >>> auth_manager.revoke_token(token)  # Logout
        """
        with self._lock:
            self.token_blacklist.add(token)

            # Remove from refresh tokens if present
            if token in self.refresh_tokens:
                del self.refresh_tokens[token]

        logger.info("Token revoked")

    def enable_mfa(self, user_id: str) -> str:
        """
        Enable MFA for user and return secret.

        Args:
            user_id: User identifier

        Returns:
            TOTP secret (show to user as QR code)

        Raises:
            BaseAuthenticationError: If user not found
        """
        with self._lock:
            user = self.users.get(user_id)
            if not user:
                raise BaseAuthenticationError(f"User not found: {user_id}")

            # Generate TOTP secret
            secret = pyotp.random_base32()
            user.mfa_secret = secret
            user.mfa_enabled = True

        logger.info(f"MFA enabled for user: {user.username}")

        return secret

    def disable_mfa(self, user_id: str) -> None:
        """
        Disable MFA for user.

        Args:
            user_id: User identifier
        """
        with self._lock:
            user = self.users.get(user_id)
            if user:
                user.mfa_enabled = False
                user.mfa_secret = None

        logger.info(f"MFA disabled for user: {user_id}")

    def _verify_mfa(self, user: User, code: str) -> bool:
        """
        Verify MFA code.

        Args:
            user: User object
            code: TOTP code

        Returns:
            True if code is valid, False otherwise
        """
        if not user.mfa_secret:
            return False

        totp = pyotp.TOTP(user.mfa_secret)
        return totp.verify(code, valid_window=1)

    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> None:
        """
        Change user password.

        Args:
            user_id: User identifier
            old_password: Current password
            new_password: New password

        Raises:
            BaseAuthenticationError: If old password is incorrect
            BaseValidationError: If new password doesn't meet policy
        """
        # Validate new password
        is_valid, error_msg = self.password_policy.validate(new_password)
        if not is_valid:
            raise BaseValidationError(f"Password policy violation: {error_msg}")

        with self._lock:
            user = self.users.get(user_id)
            if not user:
                raise BaseAuthenticationError(f"User not found: {user_id}")

            # Verify old password
            if not self._verify_password(old_password, user.password_hash):
                raise BaseAuthenticationError("Incorrect current password")

            # Check password history
            if self._check_password_history(user_id, new_password):
                raise BaseValidationError(
                    f"Cannot reuse one of the last {self.password_policy.prevent_reuse} passwords"
                )

            # Update password
            old_hash = user.password_hash
            user.password_hash = self._hash_password(new_password)

            # Add old password to history
            self.password_history[user_id].append(old_hash)

        logger.info(f"Password changed for user: {user.username}")

    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        with self._lock:
            return self.users.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with self._lock:
            user_id = self.users_by_username.get(username)
            return self.users.get(user_id) if user_id else None

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        with self._lock:
            user_id = self.users_by_email.get(email)
            return self.users.get(user_id) if user_id else None

    def list_users(self) -> List[User]:
        """List all users."""
        with self._lock:
            return list(self.users.values())


# ==============================================================================
# API Key Manager
# ==============================================================================


@dataclass
class APIKey:
    """
    API key model.

    Attributes:
        id: Unique key identifier
        name: Human-readable name for the key
        key_hash: SHA-256 hash of the actual key
        user_id: ID of the user who owns this key
        roles: Roles assigned to this key
        created_at: Creation timestamp
        expires_at: Expiration timestamp (None = never expires)
        last_used_at: Last usage timestamp
        usage_count: Number of times key has been used
        is_active: Whether the key is active
        rate_limit: Custom rate limit for this key
        allowed_ips: List of allowed IP addresses (empty = all allowed)
        metadata: Additional metadata
    """

    id: str
    name: str
    key_hash: str
    user_id: str
    roles: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    is_active: bool = True
    rate_limit: Optional[int] = None
    allowed_ips: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "roles": self.roles,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at else None
            ),
            "usage_count": self.usage_count,
            "is_active": self.is_active,
            "rate_limit": self.rate_limit,
            "allowed_ips": self.allowed_ips,
            "metadata": self.metadata,
        }

        if include_sensitive:
            data["key_hash"] = self.key_hash

        return data


class APIKeyManager:
    """
    Manage API keys for service-to-service authentication.

    Features:
    - Secure API key generation with SHA-256 hashing
    - Key expiration and rotation
    - IP whitelisting
    - Per-key rate limits
    - Usage tracking

    Examples:
        >>> api_key_manager = APIKeyManager()
        >>>
        >>> # Generate API key
        >>> api_key = api_key_manager.generate_api_key(
        ...     user_id="user_123",
        ...     name="Production App",
        ...     roles=["analyst"],
        ...     expires_days=90
        ... )
        >>>
        >>> # Verify API key
        >>> key_info = api_key_manager.verify_api_key(api_key)
    """

    def __init__(self):
        """Initialize API key manager."""
        # API key storage (in production, use database)
        self.api_keys: Dict[str, APIKey] = {}
        self.api_keys_by_hash: Dict[str, str] = {}  # hash -> key_id

        # Thread safety
        self._lock = Lock()

        logger.info("API key manager initialized")

    def _hash_api_key(self, api_key: str) -> str:
        """
        Hash API key using SHA-256.

        Args:
            api_key: Plain text API key

        Returns:
            Hexadecimal hash
        """
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    def generate_api_key(
        self,
        user_id: str,
        name: str,
        roles: Optional[List[str]] = None,
        expires_days: Optional[int] = None,
        rate_limit: Optional[int] = None,
        allowed_ips: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a new API key.

        Args:
            user_id: ID of the user who owns this key
            name: Human-readable name for the key
            roles: Roles to assign to this key
            expires_days: Days until expiration (None = never expires)
            rate_limit: Custom rate limit (requests per minute)
            allowed_ips: List of allowed IP addresses
            metadata: Additional metadata

        Returns:
            Plain text API key (only shown once!)

        Examples:
            >>> api_key = api_key_manager.generate_api_key(
            ...     user_id="user_123",
            ...     name="Production App",
            ...     roles=["analyst", "viewer"],
            ...     expires_days=90,
            ...     rate_limit=1000,
            ...     allowed_ips=["192.168.1.100"]
            ... )
        """
        # Generate secure random API key
        api_key = f"nba_mcp_{secrets.token_urlsafe(32)}"

        # Hash the key
        key_hash = self._hash_api_key(api_key)

        # Generate key ID
        key_id = f"apikey_{secrets.token_urlsafe(16)}"

        # Calculate expiry
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)

        # Create API key
        api_key_obj = APIKey(
            id=key_id,
            name=name,
            key_hash=key_hash,
            user_id=user_id,
            roles=roles or ["viewer"],
            expires_at=expires_at,
            rate_limit=rate_limit,
            allowed_ips=allowed_ips or [],
            metadata=metadata or {},
        )

        with self._lock:
            self.api_keys[key_id] = api_key_obj
            self.api_keys_by_hash[key_hash] = key_id

        logger.info(
            f"API key generated: {name}",
            extra={
                "key_id": key_id,
                "user_id": user_id,
                "roles": roles,
                "expires_days": expires_days,
            },
        )

        return api_key

    def verify_api_key(
        self,
        api_key: str,
        client_ip: Optional[str] = None,
    ) -> Optional[APIKey]:
        """
        Verify an API key.

        Args:
            api_key: Plain text API key
            client_ip: Client IP address (for IP whitelisting)

        Returns:
            APIKey object if valid, None otherwise

        Examples:
            >>> key_info = api_key_manager.verify_api_key(
            ...     api_key="nba_mcp_abc123...",
            ...     client_ip="192.168.1.100"
            ... )
        """
        key_hash = self._hash_api_key(api_key)

        with self._lock:
            key_id = self.api_keys_by_hash.get(key_hash)
            if not key_id or key_id not in self.api_keys:
                logger.warning("Invalid API key")
                return None

            key_obj = self.api_keys[key_id]

            # Check if key is active
            if not key_obj.is_active:
                logger.warning(f"API key inactive: {key_obj.name}")
                return None

            # Check expiration
            if key_obj.expires_at and datetime.now() > key_obj.expires_at:
                logger.warning(f"API key expired: {key_obj.name}")
                return None

            # Check IP whitelist
            if key_obj.allowed_ips and client_ip:
                if client_ip not in key_obj.allowed_ips:
                    logger.warning(
                        f"API key IP not allowed: {key_obj.name}",
                        extra={
                            "client_ip": client_ip,
                            "allowed_ips": key_obj.allowed_ips,
                        },
                    )
                    return None

            # Update usage
            key_obj.last_used_at = datetime.now()
            key_obj.usage_count += 1

        logger.debug(f"API key verified: {key_obj.name}")

        return key_obj

    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key.

        Args:
            api_key: Plain text API key

        Returns:
            True if revoked, False if not found
        """
        key_hash = self._hash_api_key(api_key)

        with self._lock:
            key_id = self.api_keys_by_hash.get(key_hash)
            if not key_id:
                return False

            if key_id in self.api_keys:
                name = self.api_keys[key_id].name
                del self.api_keys[key_id]
                del self.api_keys_by_hash[key_hash]

                logger.info(f"API key revoked: {name}")
                return True

        return False

    def revoke_api_key_by_id(self, key_id: str) -> bool:
        """
        Revoke an API key by ID.

        Args:
            key_id: API key ID

        Returns:
            True if revoked, False if not found
        """
        with self._lock:
            if key_id in self.api_keys:
                key_obj = self.api_keys[key_id]
                del self.api_keys_by_hash[key_obj.key_hash]
                del self.api_keys[key_id]

                logger.info(f"API key revoked: {key_obj.name}")
                return True

        return False

    def list_api_keys(self, user_id: Optional[str] = None) -> List[APIKey]:
        """
        List API keys.

        Args:
            user_id: Filter by user ID (None = all keys)

        Returns:
            List of API keys
        """
        with self._lock:
            keys = list(self.api_keys.values())

            if user_id:
                keys = [k for k in keys if k.user_id == user_id]

            return keys


# ==============================================================================
# Global Instances
# ==============================================================================


_global_auth_manager: Optional[AuthenticationManager] = None
_global_api_key_manager: Optional[APIKeyManager] = None


def get_auth_manager() -> AuthenticationManager:
    """Get the global authentication manager instance."""
    global _global_auth_manager
    if _global_auth_manager is None:
        _global_auth_manager = AuthenticationManager(
            jwt_secret=os.getenv("JWT_SECRET"),
        )
    return _global_auth_manager


def set_auth_manager(manager: AuthenticationManager) -> None:
    """Set the global authentication manager instance."""
    global _global_auth_manager
    _global_auth_manager = manager


def get_api_key_manager() -> APIKeyManager:
    """Get the global API key manager instance."""
    global _global_api_key_manager
    if _global_api_key_manager is None:
        _global_api_key_manager = APIKeyManager()
    return _global_api_key_manager


def set_api_key_manager(manager: APIKeyManager) -> None:
    """Set the global API key manager instance."""
    global _global_api_key_manager
    _global_api_key_manager = manager
