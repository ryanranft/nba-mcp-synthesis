"""Tests for authentication and authorization"""

import pytest
from datetime import datetime, timedelta
from mcp_server.auth import (
    JWTAuth,
    APIKeyAuth,
    Authorization,
    Role,
    get_jwt_auth,
    get_api_key_auth,
    authenticate_request,
)


class TestJWTAuth:
    """Test JWT authentication"""

    def test_create_token(self):
        """Test creating a JWT token"""
        auth = JWTAuth()
        token = auth.create_token("user123", Role.USER)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self):
        """Test verifying a valid token"""
        auth = JWTAuth()
        token = auth.create_token("user123", Role.ADMIN)
        payload = auth.verify_token(token)

        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"

    def test_verify_invalid_token(self):
        """Test verifying an invalid token"""
        auth = JWTAuth()
        payload = auth.verify_token("invalid.token.here")
        assert payload is None

    def test_token_expiry(self):
        """Test that expired tokens are rejected"""
        auth = JWTAuth()
        auth.token_expiry_hours = -1  # Make it expired
        token = auth.create_token("user123", Role.USER)
        payload = auth.verify_token(token)
        assert payload is None  # Should be rejected as expired

    def test_refresh_token(self):
        """Test refreshing a token"""
        auth = JWTAuth()
        old_token = auth.create_token("user123", Role.USER)
        new_token = auth.refresh_token(old_token)

        assert new_token is not None
        assert new_token != old_token  # Should be different

        # Both tokens should have same user/role
        old_payload = auth.verify_token(old_token)
        new_payload = auth.verify_token(new_token)
        assert old_payload["sub"] == new_payload["sub"]
        assert old_payload["role"] == new_payload["role"]

    def test_custom_claims(self):
        """Test adding custom claims to tokens"""
        auth = JWTAuth()
        token = auth.create_token(
            "user123",
            Role.USER,
            custom_claims={"team": "Lakers", "permissions": ["read", "write"]},
        )
        payload = auth.verify_token(token)

        assert payload["team"] == "Lakers"
        assert payload["permissions"] == ["read", "write"]


class TestAPIKeyAuth:
    """Test API key authentication"""

    def test_generate_api_key(self):
        """Test generating an API key"""
        auth = APIKeyAuth()
        api_key = auth.generate_api_key("Test Key", Role.USER)

        assert isinstance(api_key, str)
        assert api_key.startswith("nba_mcp_")

    def test_verify_valid_api_key(self):
        """Test verifying a valid API key"""
        auth = APIKeyAuth()
        api_key = auth.generate_api_key("Test Key", Role.ADMIN)
        metadata = auth.verify_api_key(api_key)

        assert metadata is not None
        assert metadata["name"] == "Test Key"
        assert metadata["role"] == "admin"
        assert metadata["use_count"] == 1

    def test_verify_invalid_api_key(self):
        """Test verifying an invalid API key"""
        auth = APIKeyAuth()
        metadata = auth.verify_api_key("invalid_key")
        assert metadata is None

    def test_api_key_expiry(self):
        """Test that expired API keys are rejected"""
        auth = APIKeyAuth()
        api_key = auth.generate_api_key("Temp Key", Role.USER, expires_days=-1)
        metadata = auth.verify_api_key(api_key)
        assert metadata is None  # Should be expired

    def test_revoke_api_key(self):
        """Test revoking an API key"""
        auth = APIKeyAuth()
        api_key = auth.generate_api_key("Test Key", Role.USER)

        # Verify it works
        assert auth.verify_api_key(api_key) is not None

        # Revoke it
        result = auth.revoke_api_key(api_key)
        assert result is True

        # Verify it no longer works
        assert auth.verify_api_key(api_key) is None

    def test_list_api_keys(self):
        """Test listing API keys"""
        auth = APIKeyAuth()
        auth.generate_api_key("Key 1", Role.USER)
        auth.generate_api_key("Key 2", Role.ADMIN)

        keys = auth.list_api_keys()
        assert len(keys) == 2
        assert any(k["name"] == "Key 1" for k in keys)
        assert any(k["name"] == "Key 2" for k in keys)

    def test_usage_tracking(self):
        """Test that API key usage is tracked"""
        auth = APIKeyAuth()
        api_key = auth.generate_api_key("Test Key", Role.USER)

        # Use it 3 times
        for i in range(3):
            metadata = auth.verify_api_key(api_key)
            assert metadata["use_count"] == i + 1


class TestAuthorization:
    """Test role-based authorization"""

    def test_admin_permissions(self):
        """Test admin has all permissions"""
        assert Authorization.can_perform(Role.ADMIN, "read")
        assert Authorization.can_perform(Role.ADMIN, "write")
        assert Authorization.can_perform(Role.ADMIN, "delete")
        assert Authorization.can_perform(Role.ADMIN, "manage_users")

    def test_user_permissions(self):
        """Test regular user permissions"""
        assert Authorization.can_perform(Role.USER, "read")
        assert Authorization.can_perform(Role.USER, "write")
        assert not Authorization.can_perform(Role.USER, "delete")
        assert not Authorization.can_perform(Role.USER, "manage_users")

    def test_readonly_permissions(self):
        """Test read-only user permissions"""
        assert Authorization.can_perform(Role.READ_ONLY, "read")
        assert not Authorization.can_perform(Role.READ_ONLY, "write")
        assert not Authorization.can_perform(Role.READ_ONLY, "delete")

    def test_service_permissions(self):
        """Test service account permissions"""
        assert Authorization.can_perform(Role.SERVICE, "read")
        assert Authorization.can_perform(Role.SERVICE, "write")
        assert not Authorization.can_perform(Role.SERVICE, "delete")

    def test_require_permission_success(self):
        """Test require_permission allows authorized actions"""
        try:
            Authorization.require_permission(Role.ADMIN, "delete")
            # Should not raise
        except PermissionError:
            pytest.fail("Should not raise PermissionError")

    def test_require_permission_failure(self):
        """Test require_permission blocks unauthorized actions"""
        with pytest.raises(PermissionError):
            Authorization.require_permission(Role.READ_ONLY, "delete")


class TestAuthenticateRequest:
    """Test unified authentication"""

    def test_authenticate_with_jwt(self):
        """Test authentication with JWT token"""
        from mcp_server.auth import get_jwt_auth

        jwt_auth = get_jwt_auth()  # Use global instance
        token = jwt_auth.create_token("user123", Role.USER)

        result = authenticate_request(token=token)
        assert result is not None
        assert result["user_id"] == "user123"
        assert result["role"] == Role.USER
        assert result["auth_method"] == "jwt"

    def test_authenticate_with_api_key(self):
        """Test authentication with API key"""
        from mcp_server.auth import get_api_key_auth

        api_auth = get_api_key_auth()  # Use global instance
        api_key = api_auth.generate_api_key("Test Key", Role.ADMIN)

        result = authenticate_request(api_key=api_key)
        assert result is not None
        assert result["user_id"] == "Test Key"
        assert result["role"] == Role.ADMIN
        assert result["auth_method"] == "api_key"

    def test_authenticate_with_invalid_credentials(self):
        """Test authentication fails with invalid credentials"""
        result = authenticate_request(token="invalid", api_key="invalid")
        assert result is None

    def test_authenticate_with_no_credentials(self):
        """Test authentication fails with no credentials"""
        result = authenticate_request()
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
