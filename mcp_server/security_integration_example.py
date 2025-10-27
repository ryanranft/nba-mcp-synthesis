"""
Security Integration Examples for NBA MCP Server

This file demonstrates how to use the comprehensive security features:
1. JWT Authentication Flow
2. Rate-Limited API Endpoints
3. RBAC Permission Checking
4. API Key Authentication
5. Secure Communication with DH Key Exchange

Author: NBA MCP Server Team - Phase 10A Agent 3
Date: 2025-01-18
"""

import asyncio
from datetime import datetime

# Import security modules
from .auth_enhanced import (
    AuthenticationManager,
    APIKeyManager,
    User,
    PasswordPolicy,
    get_auth_manager,
    get_api_key_manager,
)
from .rbac import (
    RBACManager,
    Permission,
    ResourceType,
    Role,
    require_permission,
    require_role,
    get_rbac_manager,
)
from .rate_limiter_enhanced import (
    RateLimiter,
    RateLimitConfig,
    rate_limit,
    get_rate_limiter,
)
from .crypto import (
    CryptoManager,
    modular_exponentiation,
    get_crypto_manager,
)
from .logging_config import get_logger

logger = get_logger(__name__)


# ==============================================================================
# Example 1: JWT Authentication Flow
# ==============================================================================


async def example_jwt_authentication():
    """
    Example: Complete JWT authentication workflow.

    This demonstrates:
    - User registration with password policy
    - Authentication with JWT tokens
    - Token verification
    - Token refresh
    - Logout (token revocation)
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: JWT Authentication Flow")
    logger.info("=" * 60)

    # Initialize authentication manager
    auth_manager = AuthenticationManager(
        access_token_expiry=15,  # 15 minutes
        refresh_token_expiry=7,  # 7 days
        password_policy=PasswordPolicy(min_length=12),
    )

    try:
        # Step 1: Register a new user
        logger.info("\nStep 1: Registering new user...")
        user = auth_manager.register_user(
            username="analyst1",
            email="analyst@nba.com",
            password="SecurePass123!",
            roles=["analyst", "viewer"],
            metadata={"department": "Analytics", "team": "Lakers"},
        )
        logger.info(f"✓ User registered: {user.username} (ID: {user.id})")
        logger.info(f"  Roles: {user.roles}")

        # Step 2: Authenticate and get tokens
        logger.info("\nStep 2: Authenticating user...")
        access_token = auth_manager.authenticate("analyst1", "SecurePass123!")
        logger.info(f"✓ Authentication successful")
        logger.info(f"  Access token: {access_token[:50]}...")

        # Step 3: Verify token
        logger.info("\nStep 3: Verifying access token...")
        verified_user = auth_manager.verify_token(access_token)
        if verified_user:
            logger.info(f"✓ Token valid for user: {verified_user.username}")
            logger.info(f"  Last login: {verified_user.last_login}")
        else:
            logger.error("✗ Token verification failed")

        # Step 4: Generate refresh token and refresh
        logger.info("\nStep 4: Token refresh flow...")
        refresh_token = auth_manager._generate_token(
            user, auth_manager.TokenType.REFRESH
        )
        new_tokens = auth_manager.refresh_token(refresh_token)
        if new_tokens:
            new_access, new_refresh = new_tokens
            logger.info(f"✓ Tokens refreshed successfully")
            logger.info(f"  New access token: {new_access[:50]}...")
        else:
            logger.error("✗ Token refresh failed")

        # Step 5: Logout (revoke token)
        logger.info("\nStep 5: Logging out (revoking token)...")
        auth_manager.revoke_token(access_token)
        logger.info(f"✓ Token revoked")

        # Verify revoked token doesn't work
        verified_user = auth_manager.verify_token(access_token)
        if verified_user is None:
            logger.info(f"✓ Revoked token correctly rejected")

    except Exception as e:
        logger.error(f"✗ Error in JWT authentication: {e}", exc_info=True)

    logger.info("\n" + "=" * 60 + "\n")


# ==============================================================================
# Example 2: Rate-Limited API Endpoint
# ==============================================================================


async def example_rate_limiting():
    """
    Example: Protecting API endpoints with rate limiting.

    This demonstrates:
    - Configuring rate limits
    - Per-user rate limiting
    - Rate limit headers
    - Handling rate limit errors
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 2: Rate-Limited API Endpoints")
    logger.info("=" * 60)

    # Initialize rate limiter
    config = RateLimitConfig(
        requests_per_minute=10,
        requests_per_hour=100,
        burst_size=5,
    )
    limiter = RateLimiter(config=config)

    # Define a rate-limited function
    @rate_limit(requests_per_minute=10, requests_per_hour=100)
    async def query_database(user_id: str, query: str):
        """Example database query with rate limiting."""
        logger.info(f"Executing query for {user_id}: {query}")
        return {"result": "success", "rows": 42}

    # Test rate limiting
    user_id = "user_123"

    try:
        logger.info(f"\nTesting rate limits for {user_id}...")

        # Make requests within limit
        for i in range(5):
            allowed, info = limiter.check_rate_limit(user_id)
            if allowed:
                logger.info(f"Request {i+1}: ✓ Allowed (remaining: {info.remaining})")
                logger.info(f"  Headers: {info.to_headers()}")
            else:
                logger.warning(
                    f"Request {i+1}: ✗ Rate limited (retry after: {info.retry_after}s)"
                )

        # Show rate limit status
        logger.info(f"\nRate limit status for {user_id}:")
        status = limiter.get_rate_limit_status(user_id)
        for window, data in status.items():
            logger.info(
                f"  {window}: {data['used']}/{data['limit']} used, {data['remaining']} remaining"
            )

    except Exception as e:
        logger.error(f"✗ Error in rate limiting: {e}", exc_info=True)

    logger.info("\n" + "=" * 60 + "\n")


# ==============================================================================
# Example 3: RBAC Permission Checking
# ==============================================================================


async def example_rbac():
    """
    Example: Role-based access control.

    This demonstrates:
    - Creating roles with permissions
    - Assigning roles to users
    - Checking permissions
    - Resource-based access control
    - Permission decorators
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 3: RBAC Permission Checking")
    logger.info("=" * 60)

    # Initialize RBAC manager
    rbac = RBACManager(enable_audit_logging=True)

    try:
        # Step 1: Create custom role
        logger.info("\nStep 1: Creating custom 'data_scientist' role...")
        ds_role = rbac.create_role(
            name="data_scientist",
            permissions={Permission.READ, Permission.EXECUTE, Permission.WRITE},
            resource_permissions={
                "database:*": {Permission.READ, Permission.EXECUTE},
                "nba_data:*": {Permission.READ, Permission.WRITE, Permission.EXECUTE},
                "tool:ml_*": {Permission.EXECUTE},
            },
            priority=65,
            description="Data scientist with ML tool access",
        )
        logger.info(f"✓ Role created: {ds_role.name}")
        logger.info(f"  Permissions: {[p.value for p in ds_role.permissions]}")

        # Step 2: Assign roles to user
        user_id = "user_456"
        logger.info(f"\nStep 2: Assigning roles to {user_id}...")
        rbac.assign_roles(user_id, ["data_scientist", "analyst"])
        roles = rbac.get_user_roles(user_id)
        logger.info(f"✓ Assigned roles: {[r.name for r in roles]}")

        # Step 3: Check permissions
        logger.info(f"\nStep 3: Checking permissions for {user_id}...")

        # Check various permissions
        checks = [
            (Permission.READ, "database:games_table"),
            (Permission.EXECUTE, "database:games_table"),
            (Permission.WRITE, "nba_data:player_stats"),
            (Permission.DELETE, "database:games_table"),
            (Permission.EXECUTE, "tool:ml_predict"),
        ]

        for permission, resource in checks:
            has_permission = rbac.check_permission(user_id, permission, resource)
            status = "✓" if has_permission else "✗"
            logger.info(
                f"  {status} {permission.value} on {resource}: {has_permission}"
            )

        # Step 4: Get all permissions for a resource
        logger.info(f"\nStep 4: All permissions for 'nba_data:*'...")
        perms = rbac.get_user_permissions(user_id, "nba_data:player_stats")
        logger.info(f"  Permissions: {[p.value for p in perms]}")

        # Step 5: Require permission (will raise exception if denied)
        logger.info(f"\nStep 5: Requiring specific permission...")
        try:
            rbac.require_permission(user_id, Permission.READ, "database:games_table")
            logger.info(f"  ✓ Permission granted")
        except Exception as e:
            logger.error(f"  ✗ Permission denied: {e}")

        # Step 6: View audit log
        logger.info(f"\nStep 6: Viewing access audit log...")
        log = rbac.get_access_log(user_id=user_id, limit=5)
        for attempt in log:
            status = "GRANTED" if attempt.granted else "DENIED"
            logger.info(
                f"  [{status}] {attempt.permission.value} on {attempt.resource}"
            )

    except Exception as e:
        logger.error(f"✗ Error in RBAC: {e}", exc_info=True)

    logger.info("\n" + "=" * 60 + "\n")


# ==============================================================================
# Example 4: API Key Authentication
# ==============================================================================


async def example_api_key_auth():
    """
    Example: API key authentication for service-to-service communication.

    This demonstrates:
    - Generating API keys
    - Verifying API keys
    - IP whitelisting
    - Key expiration
    - Usage tracking
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 4: API Key Authentication")
    logger.info("=" * 60)

    # Initialize API key manager
    api_key_manager = APIKeyManager()

    try:
        # Step 1: Generate API key
        logger.info("\nStep 1: Generating API key...")
        api_key = api_key_manager.generate_api_key(
            user_id="service_123",
            name="Production Analytics Service",
            roles=["analyst", "service"],
            expires_days=90,
            rate_limit=1000,  # requests per minute
            allowed_ips=["192.168.1.100", "10.0.0.50"],
            metadata={"environment": "production", "service": "analytics"},
        )
        logger.info(f"✓ API key generated: {api_key[:30]}...")
        logger.info(f"  NOTE: This is the only time the key will be shown!")

        # Step 2: Verify API key
        logger.info("\nStep 2: Verifying API key...")
        key_info = api_key_manager.verify_api_key(api_key, client_ip="192.168.1.100")
        if key_info:
            logger.info(f"✓ API key valid")
            logger.info(f"  Name: {key_info.name}")
            logger.info(f"  User ID: {key_info.user_id}")
            logger.info(f"  Roles: {key_info.roles}")
            logger.info(f"  Usage count: {key_info.usage_count}")
            logger.info(f"  Rate limit: {key_info.rate_limit} req/min")
        else:
            logger.error("✗ API key verification failed")

        # Step 3: Test IP whitelisting
        logger.info("\nStep 3: Testing IP whitelisting...")
        key_info = api_key_manager.verify_api_key(api_key, client_ip="1.2.3.4")
        if key_info:
            logger.warning("✗ IP check failed - allowed from non-whitelisted IP")
        else:
            logger.info("✓ IP check passed - blocked non-whitelisted IP")

        # Step 4: List all API keys
        logger.info("\nStep 4: Listing API keys...")
        keys = api_key_manager.list_api_keys(user_id="service_123")
        for key in keys:
            logger.info(f"  - {key.name}: {key.usage_count} uses")

        # Step 5: Revoke API key
        logger.info("\nStep 5: Revoking API key...")
        revoked = api_key_manager.revoke_api_key(api_key)
        if revoked:
            logger.info(f"✓ API key revoked")

            # Verify revoked key doesn't work
            key_info = api_key_manager.verify_api_key(api_key)
            if key_info is None:
                logger.info(f"✓ Revoked key correctly rejected")

    except Exception as e:
        logger.error(f"✗ Error in API key authentication: {e}", exc_info=True)

    logger.info("\n" + "=" * 60 + "\n")


# ==============================================================================
# Example 5: Secure Communication with DH Key Exchange
# ==============================================================================


async def example_crypto():
    """
    Example: Secure communication using cryptographic primitives.

    This demonstrates:
    - Diffie-Hellman key exchange
    - Message signing and verification
    - Symmetric encryption
    - Secure random generation
    - Constant-time comparisons
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 5: Secure Communication with Cryptography")
    logger.info("=" * 60)

    # Initialize crypto manager
    crypto = CryptoManager()

    try:
        # Part A: Diffie-Hellman Key Exchange
        logger.info("\nPart A: Diffie-Hellman Key Exchange")
        logger.info("-" * 40)

        # Alice generates keypair
        logger.info("Alice generates DH keypair...")
        alice_private, alice_public = crypto.generate_dh_keypair()
        logger.info(f"  Alice public key: {str(alice_public)[:50]}...")

        # Bob generates keypair
        logger.info("Bob generates DH keypair...")
        bob_private, bob_public = crypto.generate_dh_keypair()
        logger.info(f"  Bob public key: {str(bob_public)[:50]}...")

        # Both compute shared secret
        logger.info("Computing shared secrets...")
        alice_shared = crypto.compute_shared_secret(alice_private, bob_public)
        bob_shared = crypto.compute_shared_secret(bob_private, alice_public)

        # Verify they match
        if alice_shared == bob_shared:
            logger.info(f"✓ Shared secrets match!")
            logger.info(f"  Shared secret: {str(alice_shared)[:50]}...")
        else:
            logger.error("✗ Shared secrets don't match")

        # Part B: RSA Message Signing
        logger.info("\nPart B: RSA Message Signing")
        logger.info("-" * 40)

        # Generate RSA keypair
        logger.info("Generating RSA keypair...")
        rsa_private, rsa_public = crypto.generate_rsa_keypair(key_size=2048)
        logger.info(f"✓ RSA keypair generated (2048 bits)")

        # Sign a message
        message = b"NBA Analytics Service - Transaction #12345"
        logger.info(f"Signing message: {message.decode()}")
        signature = crypto.sign_message(message, rsa_private)
        logger.info(f"  Signature: {signature.hex()[:50]}...")

        # Verify signature
        logger.info("Verifying signature...")
        is_valid = crypto.verify_signature(message, signature, rsa_public)
        if is_valid:
            logger.info(f"✓ Signature verified successfully")
        else:
            logger.error("✗ Signature verification failed")

        # Try tampering with message
        tampered_message = b"NBA Analytics Service - Transaction #99999"
        logger.info(f"Verifying tampered message...")
        is_valid = crypto.verify_signature(tampered_message, signature, rsa_public)
        if not is_valid:
            logger.info(f"✓ Tampered message correctly rejected")

        # Part C: Symmetric Encryption
        logger.info("\nPart C: AES-GCM Encryption")
        logger.info("-" * 40)

        # Generate encryption key
        logger.info("Generating encryption key...")
        aes_key = crypto.generate_secure_random(32)  # 256-bit key
        logger.info(f"  Key: {aes_key.hex()[:40]}...")

        # Encrypt data
        plaintext = b"Secret NBA player contract details: $50M/year"
        logger.info(f"Encrypting: {plaintext.decode()}")
        ciphertext, nonce, tag = crypto.encrypt_aes_gcm(plaintext, aes_key)
        logger.info(f"  Ciphertext: {ciphertext.hex()[:50]}...")
        logger.info(f"  Nonce: {nonce.hex()}")
        logger.info(f"  Tag: {tag.hex()}")

        # Decrypt data
        logger.info("Decrypting...")
        decrypted = crypto.decrypt_aes_gcm(ciphertext, aes_key, nonce, tag)
        if decrypted == plaintext:
            logger.info(f"✓ Decrypted successfully: {decrypted.decode()}")
        else:
            logger.error("✗ Decryption failed")

        # Part D: Secure Token Generation
        logger.info("\nPart D: Secure Random Token Generation")
        logger.info("-" * 40)

        # Generate secure tokens
        logger.info("Generating secure tokens...")
        session_token = crypto.generate_secure_token(32)
        api_token = crypto.generate_secure_token(32)
        logger.info(f"  Session token: {session_token[:40]}...")
        logger.info(f"  API token: {api_token[:40]}...")

        # Part E: Key Derivation
        logger.info("\nPart E: Key Derivation from Password")
        logger.info("-" * 40)

        # Derive key from password
        password = b"user_password_123"
        salt = crypto.generate_secure_random(16)
        logger.info("Deriving key from password...")
        derived_key = crypto.derive_key(password, salt, iterations=100000)
        logger.info(f"  Derived key: {derived_key.hex()[:50]}...")
        logger.info(f"  Salt: {salt.hex()}")

        # Part F: HMAC Message Authentication
        logger.info("\nPart F: HMAC Message Authentication")
        logger.info("-" * 40)

        # Compute HMAC
        hmac_key = crypto.generate_secure_random(32)
        message = b"Authenticated message from analytics service"
        logger.info(f"Computing HMAC for: {message.decode()}")
        mac = crypto.hmac_sha256(hmac_key, message)
        logger.info(f"  HMAC: {mac.hex()}")

        # Verify HMAC
        logger.info("Verifying HMAC...")
        is_valid = crypto.verify_hmac(hmac_key, message, mac)
        if is_valid:
            logger.info(f"✓ HMAC verified successfully")
        else:
            logger.error("✗ HMAC verification failed")

    except Exception as e:
        logger.error(f"✗ Error in cryptography: {e}", exc_info=True)

    logger.info("\n" + "=" * 60 + "\n")


# ==============================================================================
# Main Function
# ==============================================================================


async def run_all_examples():
    """Run all security integration examples."""
    logger.info("\n" + "=" * 60)
    logger.info("NBA MCP SERVER - SECURITY INTEGRATION EXAMPLES")
    logger.info("=" * 60 + "\n")

    # Run all examples
    await example_jwt_authentication()
    await example_rate_limiting()
    await example_rbac()
    await example_api_key_auth()
    await example_crypto()

    logger.info("=" * 60)
    logger.info("All examples completed successfully!")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())
