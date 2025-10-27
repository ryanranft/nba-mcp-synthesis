"""
Comprehensive Security Test Suite for NBA MCP Server

Tests all security modules:
- Authentication (auth_enhanced.py)
- RBAC (rbac.py)
- Rate Limiting (rate_limiter_enhanced.py)
- Cryptography (crypto.py)

Author: NBA MCP Server Team - Phase 10A Agent 3
Date: 2025-01-18
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta

# Import security modules
from mcp_server.auth_enhanced import (
    AuthenticationManager,
    APIKeyManager,
    User,
    PasswordPolicy,
)
from mcp_server.rbac import (
    RBACManager,
    Permission,
    ResourceType,
    Role,
)
from mcp_server.rate_limiter_enhanced import (
    RateLimiter,
    RateLimitConfig,
    RateLimitAlgorithm,
    TokenBucketLimiter,
    SlidingWindowLimiter,
)
from mcp_server.crypto import (
    CryptoManager,
    modular_exponentiation,
    is_prime,
)


# ==============================================================================
# Authentication Tests
# ==============================================================================


class TestAuthentication:
    """Test authentication functionality."""

    @pytest.fixture
    def auth_manager(self):
        """Create authentication manager for testing."""
        return AuthenticationManager(
            access_token_expiry=15,
            refresh_token_expiry=7,
            max_failed_attempts=3,
            lockout_duration=5,
        )

    def test_user_registration(self, auth_manager):
        """Test user registration with password policy."""
        user = auth_manager.register_user(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!",
            roles=["analyst"],
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert "analyst" in user.roles
        assert user.is_active
        assert not user.is_verified

    def test_password_policy_validation(self, auth_manager):
        """Test password policy enforcement."""
        # Too short
        with pytest.raises(Exception):
            auth_manager.register_user(
                username="user1",
                email="user1@example.com",
                password="short",
            )

        # Missing uppercase
        with pytest.raises(Exception):
            auth_manager.register_user(
                username="user2",
                email="user2@example.com",
                password="nocapital123!",
            )

        # Missing digit
        with pytest.raises(Exception):
            auth_manager.register_user(
                username="user3",
                email="user3@example.com",
                password="NoDigitsHere!",
            )

        # Missing special character
        with pytest.raises(Exception):
            auth_manager.register_user(
                username="user4",
                email="user4@example.com",
                password="NoSpecial123",
            )

    def test_user_authentication(self, auth_manager):
        """Test user authentication."""
        # Register user
        user = auth_manager.register_user(
            username="analyst1",
            email="analyst@example.com",
            password="SecurePass123!",
        )

        # Authenticate
        token = auth_manager.authenticate("analyst1", "SecurePass123!")
        assert token is not None
        assert len(token) > 0

        # Verify token
        verified_user = auth_manager.verify_token(token)
        assert verified_user is not None
        assert verified_user.id == user.id
        assert verified_user.username == user.username

    def test_failed_login_attempts(self, auth_manager):
        """Test account lockout after failed attempts."""
        # Register user
        auth_manager.register_user(
            username="locktest",
            email="locktest@example.com",
            password="SecurePass123!",
        )

        # Try wrong password multiple times
        for i in range(3):
            with pytest.raises(Exception):
                auth_manager.authenticate("locktest", "WrongPassword123!")

        # Account should be locked
        user = auth_manager.get_user_by_username("locktest")
        assert user.is_locked()

    def test_token_refresh(self, auth_manager):
        """Test JWT token refresh."""
        # Register and authenticate
        user = auth_manager.register_user(
            username="refreshuser",
            email="refresh@example.com",
            password="SecurePass123!",
        )

        # Generate refresh token
        refresh_token = auth_manager._generate_token(
            user, auth_manager.TokenType.REFRESH
        )

        # Refresh
        new_tokens = auth_manager.refresh_token(refresh_token)
        assert new_tokens is not None

        new_access, new_refresh = new_tokens
        assert len(new_access) > 0
        assert len(new_refresh) > 0

    def test_token_revocation(self, auth_manager):
        """Test token revocation (logout)."""
        # Register and authenticate
        user = auth_manager.register_user(
            username="revokeuser",
            email="revoke@example.com",
            password="SecurePass123!",
        )

        token = auth_manager.authenticate("revokeuser", "SecurePass123!")

        # Verify token works
        verified = auth_manager.verify_token(token)
        assert verified is not None

        # Revoke token
        auth_manager.revoke_token(token)

        # Verify token doesn't work anymore
        verified = auth_manager.verify_token(token)
        assert verified is None

    def test_password_change(self, auth_manager):
        """Test password change."""
        # Register user
        user = auth_manager.register_user(
            username="passchange",
            email="passchange@example.com",
            password="OldPass123!",
        )

        # Change password
        auth_manager.change_password(
            user.id,
            "OldPass123!",
            "NewPass123!",
        )

        # Old password shouldn't work
        with pytest.raises(Exception):
            auth_manager.authenticate("passchange", "OldPass123!")

        # New password should work
        token = auth_manager.authenticate("passchange", "NewPass123!")
        assert token is not None

    def test_mfa_enable_disable(self, auth_manager):
        """Test MFA functionality."""
        # Register user
        user = auth_manager.register_user(
            username="mfauser",
            email="mfa@example.com",
            password="SecurePass123!",
        )

        # Enable MFA
        secret = auth_manager.enable_mfa(user.id)
        assert secret is not None
        assert len(secret) > 0

        # Verify MFA is enabled
        user = auth_manager.get_user(user.id)
        assert user.mfa_enabled

        # Disable MFA
        auth_manager.disable_mfa(user.id)

        # Verify MFA is disabled
        user = auth_manager.get_user(user.id)
        assert not user.mfa_enabled


class TestAPIKeys:
    """Test API key authentication."""

    @pytest.fixture
    def api_key_manager(self):
        """Create API key manager for testing."""
        return APIKeyManager()

    def test_api_key_generation(self, api_key_manager):
        """Test API key generation."""
        api_key = api_key_manager.generate_api_key(
            user_id="service_123",
            name="Test Service",
            roles=["service"],
        )

        assert api_key is not None
        assert api_key.startswith("nba_mcp_")
        assert len(api_key) > 40

    def test_api_key_verification(self, api_key_manager):
        """Test API key verification."""
        # Generate key
        api_key = api_key_manager.generate_api_key(
            user_id="service_123",
            name="Test Service",
            roles=["service"],
        )

        # Verify key
        key_info = api_key_manager.verify_api_key(api_key)
        assert key_info is not None
        assert key_info.name == "Test Service"
        assert key_info.user_id == "service_123"
        assert "service" in key_info.roles

    def test_api_key_expiration(self, api_key_manager):
        """Test API key expiration."""
        # Generate key that expires in 1 second
        api_key = api_key_manager.generate_api_key(
            user_id="service_123",
            name="Expiring Service",
            roles=["service"],
            expires_days=1,
        )

        # Manually set expiration to past
        key_hash = api_key_manager._hash_api_key(api_key)
        key_id = api_key_manager.api_keys_by_hash[key_hash]
        api_key_manager.api_keys[key_id].expires_at = datetime.now() - timedelta(days=1)

        # Verify expired key doesn't work
        key_info = api_key_manager.verify_api_key(api_key)
        assert key_info is None

    def test_api_key_ip_whitelist(self, api_key_manager):
        """Test IP whitelisting."""
        # Generate key with IP whitelist
        api_key = api_key_manager.generate_api_key(
            user_id="service_123",
            name="IP Restricted Service",
            roles=["service"],
            allowed_ips=["192.168.1.100", "10.0.0.50"],
        )

        # Verify with allowed IP
        key_info = api_key_manager.verify_api_key(api_key, client_ip="192.168.1.100")
        assert key_info is not None

        # Verify with non-allowed IP
        key_info = api_key_manager.verify_api_key(api_key, client_ip="1.2.3.4")
        assert key_info is None

    def test_api_key_revocation(self, api_key_manager):
        """Test API key revocation."""
        # Generate key
        api_key = api_key_manager.generate_api_key(
            user_id="service_123",
            name="Revoke Test",
            roles=["service"],
        )

        # Verify it works
        key_info = api_key_manager.verify_api_key(api_key)
        assert key_info is not None

        # Revoke key
        revoked = api_key_manager.revoke_api_key(api_key)
        assert revoked

        # Verify it doesn't work anymore
        key_info = api_key_manager.verify_api_key(api_key)
        assert key_info is None


# ==============================================================================
# RBAC Tests
# ==============================================================================


class TestRBAC:
    """Test RBAC functionality."""

    @pytest.fixture
    def rbac_manager(self):
        """Create RBAC manager for testing."""
        return RBACManager(enable_audit_logging=True)

    def test_role_creation(self, rbac_manager):
        """Test role creation."""
        role = rbac_manager.create_role(
            name="test_role",
            permissions={Permission.READ, Permission.EXECUTE},
            priority=50,
            description="Test role",
        )

        assert role.name == "test_role"
        assert Permission.READ in role.permissions
        assert Permission.EXECUTE in role.permissions
        assert role.priority == 50

    def test_role_assignment(self, rbac_manager):
        """Test role assignment to users."""
        # Assign role
        rbac_manager.assign_role("user_123", "analyst")

        # Verify assignment
        roles = rbac_manager.get_user_roles("user_123")
        assert len(roles) == 1
        assert roles[0].name == "analyst"

    def test_permission_checking(self, rbac_manager):
        """Test permission checking."""
        # Assign role
        rbac_manager.assign_role("user_123", "analyst")

        # Check permissions
        assert rbac_manager.check_permission(
            "user_123",
            Permission.READ,
            "database:games",
            log_attempt=False,
        )

        assert rbac_manager.check_permission(
            "user_123",
            Permission.EXECUTE,
            "database:games",
            log_attempt=False,
        )

        assert not rbac_manager.check_permission(
            "user_123",
            Permission.DELETE,
            "database:games",
            log_attempt=False,
        )

    def test_resource_based_permissions(self, rbac_manager):
        """Test resource-based permissions."""
        # Create role with resource-specific permissions
        rbac_manager.create_role(
            name="db_reader",
            resource_permissions={
                "database:games": {Permission.READ},
                "database:players": {Permission.READ, Permission.WRITE},
            },
        )

        rbac_manager.assign_role("user_456", "db_reader")

        # Check permissions on different resources
        assert rbac_manager.check_permission(
            "user_456",
            Permission.READ,
            "database:games",
            log_attempt=False,
        )

        assert not rbac_manager.check_permission(
            "user_456",
            Permission.WRITE,
            "database:games",
            log_attempt=False,
        )

        assert rbac_manager.check_permission(
            "user_456",
            Permission.WRITE,
            "database:players",
            log_attempt=False,
        )

    def test_admin_permission(self, rbac_manager):
        """Test admin permission grants all access."""
        rbac_manager.assign_role("admin_user", "admin")

        # Admin should have all permissions
        assert rbac_manager.check_permission(
            "admin_user",
            Permission.DELETE,
            "database:*",
            log_attempt=False,
        )

        assert rbac_manager.check_permission(
            "admin_user",
            Permission.WRITE,
            "system:config",
            log_attempt=False,
        )

    def test_access_audit_log(self, rbac_manager):
        """Test access audit logging."""
        rbac_manager.assign_role("user_789", "viewer")

        # Make some access attempts
        rbac_manager.check_permission("user_789", Permission.READ, "database:games")
        rbac_manager.check_permission("user_789", Permission.WRITE, "database:games")
        rbac_manager.check_permission("user_789", Permission.DELETE, "database:games")

        # Check audit log
        log = rbac_manager.get_access_log(user_id="user_789")
        assert len(log) >= 3

        # Check denied access is logged
        denied = [a for a in log if not a.granted]
        assert len(denied) >= 2  # WRITE and DELETE should be denied


# ==============================================================================
# Rate Limiting Tests
# ==============================================================================


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_token_bucket_basic(self):
        """Test token bucket algorithm."""
        limiter = TokenBucketLimiter(capacity=10, refill_rate=1.0)

        # Should allow requests up to capacity
        for i in range(10):
            allowed, tokens = limiter.allow_request(cost=1.0)
            assert allowed

        # Should deny next request
        allowed, tokens = limiter.allow_request(cost=1.0)
        assert not allowed

    def test_token_bucket_refill(self):
        """Test token bucket refills over time."""
        limiter = TokenBucketLimiter(capacity=10, refill_rate=10.0)  # 10 tokens/sec

        # Drain bucket
        for i in range(10):
            limiter.allow_request(cost=1.0)

        # Wait for refill
        time.sleep(1.0)

        # Should allow requests again
        allowed, tokens = limiter.allow_request(cost=1.0)
        assert allowed

    def test_sliding_window(self):
        """Test sliding window algorithm."""
        limiter = SlidingWindowLimiter(max_requests=5, window_seconds=60)

        # Should allow up to max_requests
        for i in range(5):
            allowed, count = limiter.allow_request()
            assert allowed

        # Should deny next request
        allowed, count = limiter.allow_request()
        assert not allowed
        assert count == 5

    def test_rate_limiter_hierarchical(self):
        """Test hierarchical rate limits."""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000,
            burst_size=5,
        )

        limiter = RateLimiter(config=config)

        # Make requests within limit
        for i in range(5):
            allowed, info = limiter.check_rate_limit("user_123")
            assert allowed
            assert info.limit == config.requests_per_minute
            assert info.remaining >= 0

    def test_rate_limit_headers(self):
        """Test rate limit header generation."""
        config = RateLimitConfig(requests_per_minute=60)
        limiter = RateLimiter(config=config)

        allowed, info = limiter.check_rate_limit("user_123")

        headers = info.to_headers()
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

    def test_rate_limit_reset(self):
        """Test rate limit reset."""
        limiter = RateLimiter()

        # Make some requests
        for i in range(5):
            limiter.check_rate_limit("user_123")

        # Reset
        limiter.reset_rate_limit("user_123")

        # Should have full quota again
        status = limiter.get_rate_limit_status("user_123")
        assert status["minute"]["used"] == 0


# ==============================================================================
# Cryptography Tests
# ==============================================================================


class TestCryptography:
    """Test cryptographic utilities."""

    @pytest.fixture
    def crypto_manager(self):
        """Create crypto manager for testing."""
        return CryptoManager()

    def test_modular_exponentiation(self):
        """Test modular exponentiation."""
        result = modular_exponentiation(5, 3, 13)
        assert result == 8  # 5^3 mod 13 = 125 mod 13 = 8

    def test_is_prime(self):
        """Test prime number detection."""
        assert is_prime(17)
        assert is_prime(19)
        assert not is_prime(16)
        assert not is_prime(100)

    def test_diffie_hellman_key_exchange(self, crypto_manager):
        """Test Diffie-Hellman key exchange."""
        # Alice generates keypair
        alice_private, alice_public = crypto_manager.generate_dh_keypair()

        # Bob generates keypair
        bob_private, bob_public = crypto_manager.generate_dh_keypair()

        # Both compute shared secret
        alice_shared = crypto_manager.compute_shared_secret(alice_private, bob_public)
        bob_shared = crypto_manager.compute_shared_secret(bob_private, alice_public)

        # Shared secrets should match
        assert alice_shared == bob_shared

    def test_rsa_signature(self, crypto_manager):
        """Test RSA message signing and verification."""
        # Generate keypair
        private_key, public_key = crypto_manager.generate_rsa_keypair(key_size=2048)

        # Sign message
        message = b"Test message for signing"
        signature = crypto_manager.sign_message(message, private_key)

        # Verify signature
        is_valid = crypto_manager.verify_signature(message, signature, public_key)
        assert is_valid

        # Tampered message should fail
        tampered = b"Tampered message"
        is_valid = crypto_manager.verify_signature(tampered, signature, public_key)
        assert not is_valid

    def test_constant_time_compare(self, crypto_manager):
        """Test constant-time comparison."""
        a = b"secret_value_123"
        b = b"secret_value_123"
        c = b"different_value"

        assert crypto_manager.constant_time_compare(a, b)
        assert not crypto_manager.constant_time_compare(a, c)

    def test_secure_random_generation(self, crypto_manager):
        """Test secure random generation."""
        random1 = crypto_manager.generate_secure_random(32)
        random2 = crypto_manager.generate_secure_random(32)

        assert len(random1) == 32
        assert len(random2) == 32
        assert random1 != random2  # Should be different

    def test_secure_token_generation(self, crypto_manager):
        """Test secure token generation."""
        token1 = crypto_manager.generate_secure_token(32)
        token2 = crypto_manager.generate_secure_token(32)

        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2

    def test_key_derivation(self, crypto_manager):
        """Test PBKDF2 key derivation."""
        password = b"my_password"
        salt = crypto_manager.generate_secure_random(16)

        key = crypto_manager.derive_key(password, salt, iterations=1000)

        assert len(key) == 32  # Default key length

        # Same password and salt should give same key
        key2 = crypto_manager.derive_key(password, salt, iterations=1000)
        assert key == key2

        # Different salt should give different key
        salt2 = crypto_manager.generate_secure_random(16)
        key3 = crypto_manager.derive_key(password, salt2, iterations=1000)
        assert key != key3

    def test_aes_gcm_encryption(self, crypto_manager):
        """Test AES-GCM encryption and decryption."""
        key = crypto_manager.generate_secure_random(32)
        plaintext = b"Secret message to encrypt"

        # Encrypt
        ciphertext, nonce, tag = crypto_manager.encrypt_aes_gcm(plaintext, key)

        assert len(ciphertext) > 0
        assert len(nonce) == 12
        assert len(tag) == 16

        # Decrypt
        decrypted = crypto_manager.decrypt_aes_gcm(ciphertext, key, nonce, tag)
        assert decrypted == plaintext

        # Wrong key should fail
        wrong_key = crypto_manager.generate_secure_random(32)
        decrypted = crypto_manager.decrypt_aes_gcm(ciphertext, wrong_key, nonce, tag)
        assert decrypted is None

    def test_sha256_hash(self, crypto_manager):
        """Test SHA-256 hashing."""
        data = b"Data to hash"
        hash1 = crypto_manager.hash_sha256(data)

        assert len(hash1) == 32  # SHA-256 produces 32 bytes

        # Same data should give same hash
        hash2 = crypto_manager.hash_sha256(data)
        assert hash1 == hash2

        # Different data should give different hash
        hash3 = crypto_manager.hash_sha256(b"Different data")
        assert hash1 != hash3

    def test_hmac_sha256(self, crypto_manager):
        """Test HMAC-SHA256."""
        key = crypto_manager.generate_secure_random(32)
        message = b"Message to authenticate"

        # Compute HMAC
        mac = crypto_manager.hmac_sha256(key, message)
        assert len(mac) == 32

        # Verify HMAC
        is_valid = crypto_manager.verify_hmac(key, message, mac)
        assert is_valid

        # Wrong message should fail
        is_valid = crypto_manager.verify_hmac(key, b"Wrong message", mac)
        assert not is_valid


# ==============================================================================
# Integration Tests
# ==============================================================================


class TestSecurityIntegration:
    """Integration tests combining multiple security features."""

    def test_full_authentication_flow(self):
        """Test complete authentication flow."""
        auth = AuthenticationManager()
        rbac = RBACManager()

        # Register user
        user = auth.register_user(
            username="integrationuser",
            email="integration@example.com",
            password="SecurePass123!",
            roles=["analyst"],
        )

        # Assign RBAC role
        rbac.assign_role(user.id, "analyst")

        # Authenticate
        token = auth.authenticate("integrationuser", "SecurePass123!")
        assert token is not None

        # Verify token
        verified_user = auth.verify_token(token)
        assert verified_user is not None

        # Check RBAC permissions
        has_permission = rbac.check_permission(
            user.id,
            Permission.READ,
            "database:games",
            log_attempt=False,
        )
        assert has_permission

    def test_rate_limited_with_auth(self):
        """Test rate limiting with authentication."""
        auth = AuthenticationManager()
        limiter = RateLimiter(config=RateLimitConfig(requests_per_minute=10))

        # Register user
        user = auth.register_user(
            username="ratelimituser",
            email="ratelimit@example.com",
            password="SecurePass123!",
        )

        # Make requests with rate limiting
        for i in range(10):
            allowed, info = limiter.check_rate_limit(user.id)
            assert allowed

        # Next request should be denied
        allowed, info = limiter.check_rate_limit(user.id)
        assert not allowed


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
