#!/usr/bin/env python3
"""
Test Suite for Security Module
Tests rate limiting, SQL injection prevention, path traversal protection,
request validation, and timeout enforcement
"""

import pytest
import asyncio
import time
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Import security module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.security import (
    RateLimitConfig,
    SecurityConfig,
    RateLimiter,
    SQLValidator,
    PathValidator,
    RequestValidator,
    SecurityManager,
    with_timeout,
    enforce_timeout
)


# ==============================================================================
# Rate Limiter Tests
# ==============================================================================

class TestRateLimiter:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_rate_limiter_initial_state(self):
        """Test rate limiter initial state"""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_size=5
        )
        limiter = RateLimiter(config)

        # Should allow initial requests up to burst size
        for i in range(5):
            allowed, message = await limiter.check_rate_limit("client1")
            assert allowed is True
            assert message is None

    @pytest.mark.asyncio
    async def test_rate_limiter_burst_exceeded(self):
        """Test rate limiter blocks after burst size exceeded"""
        config = RateLimitConfig(
            requests_per_minute=60,
            burst_size=3
        )
        limiter = RateLimiter(config)

        # First 3 should succeed
        for _ in range(3):
            allowed, message = await limiter.check_rate_limit("client1")
            assert allowed is True

        # 4th should fail (burst exceeded)
        allowed, message = await limiter.check_rate_limit("client1")
        assert allowed is False
        assert "Rate limit exceeded" in message

    @pytest.mark.asyncio
    async def test_rate_limiter_per_minute_limit(self):
        """Test per-minute rate limit"""
        config = RateLimitConfig(
            requests_per_minute=5,
            burst_size=10
        )
        limiter = RateLimiter(config)

        # Make 5 requests (within minute limit)
        for _ in range(5):
            allowed, message = await limiter.check_rate_limit("client1")
            assert allowed is True

        # 6th request should fail (minute limit exceeded)
        allowed, message = await limiter.check_rate_limit("client1")
        assert allowed is False
        assert "requests/minute" in message

    @pytest.mark.asyncio
    async def test_rate_limiter_per_hour_limit(self):
        """Test per-hour rate limit"""
        config = RateLimitConfig(
            requests_per_minute=1000,  # High minute limit
            requests_per_hour=10,      # Low hour limit
            burst_size=20
        )
        limiter = RateLimiter(config)

        # Make 10 requests
        for _ in range(10):
            allowed, message = await limiter.check_rate_limit("client1")
            assert allowed is True

        # 11th should fail (hour limit)
        allowed, message = await limiter.check_rate_limit("client1")
        assert allowed is False
        assert "requests/hour" in message

    @pytest.mark.asyncio
    async def test_rate_limiter_token_refill(self):
        """Test token bucket refills over time"""
        config = RateLimitConfig(
            requests_per_minute=60,  # 1 token per second
            burst_size=2
        )
        limiter = RateLimiter(config)

        # Consume all tokens
        await limiter.check_rate_limit("client1")
        await limiter.check_rate_limit("client1")

        # Should fail immediately
        allowed, _ = await limiter.check_rate_limit("client1")
        assert allowed is False

        # Wait for refill (~1.1 seconds = 1 token)
        await asyncio.sleep(1.1)

        # Should succeed now
        allowed, message = await limiter.check_rate_limit("client1")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limiter_per_client_isolation(self):
        """Test rate limits are per-client"""
        config = RateLimitConfig(
            requests_per_minute=2,
            burst_size=2
        )
        limiter = RateLimiter(config)

        # Client 1 uses up limit
        await limiter.check_rate_limit("client1")
        await limiter.check_rate_limit("client1")

        # Client 1 should be limited
        allowed, _ = await limiter.check_rate_limit("client1")
        assert allowed is False

        # Client 2 should not be affected
        allowed, _ = await limiter.check_rate_limit("client2")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limiter_reset_client(self):
        """Test resetting rate limit for specific client"""
        config = RateLimitConfig(
            requests_per_minute=2,
            burst_size=2
        )
        limiter = RateLimiter(config)

        # Consume limit
        await limiter.check_rate_limit("client1")
        await limiter.check_rate_limit("client1")

        # Should be limited
        allowed, _ = await limiter.check_rate_limit("client1")
        assert allowed is False

        # Reset client
        limiter.reset_client("client1")

        # Should work now
        allowed, _ = await limiter.check_rate_limit("client1")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_rate_limiter_get_stats(self):
        """Test getting client statistics"""
        config = RateLimitConfig(
            requests_per_minute=10,
            burst_size=5
        )
        limiter = RateLimiter(config)

        # Make some requests
        await limiter.check_rate_limit("client1")
        await limiter.check_rate_limit("client1")

        stats = limiter.get_client_stats("client1")
        assert stats["requests_this_minute"] == 2
        assert stats["tokens_remaining"] < 5
        assert stats["burst_size"] == 5

    @pytest.mark.asyncio
    async def test_rate_limiter_disabled(self):
        """Test rate limiter when disabled"""
        config = RateLimitConfig(enabled=False)
        limiter = RateLimiter(config)

        # Should allow unlimited requests
        for _ in range(100):
            allowed, message = await limiter.check_rate_limit("client1")
            assert allowed is True


# ==============================================================================
# SQL Validator Tests
# ==============================================================================

class TestSQLValidator:
    """Test SQL injection prevention"""

    def test_sql_validator_valid_select(self):
        """Test validator allows valid SELECT queries"""
        config = SecurityConfig()
        validator = SQLValidator(config)

        valid_queries = [
            "SELECT * FROM games",
            "SELECT player_name, points FROM players WHERE points > 20",
            "SELECT COUNT(*) FROM games WHERE game_date > '2024-01-01'",
            "EXPLAIN SELECT * FROM games",
            "SHOW TABLES",
            "DESCRIBE players"
        ]

        for query in valid_queries:
            valid, message = validator.validate_sql_query(query)
            assert valid is True, f"Query should be valid: {query}"

    def test_sql_validator_forbidden_keywords(self):
        """Test validator blocks forbidden keywords"""
        config = SecurityConfig()
        validator = SQLValidator(config)

        forbidden_queries = [
            "DROP TABLE games",
            "DELETE FROM players WHERE id = 1",
            "UPDATE games SET score = 0",
            "INSERT INTO players VALUES (1, 'Test')",
            "TRUNCATE TABLE games",
            "ALTER TABLE games ADD COLUMN test INT",
            "CREATE TABLE test (id INT)",
            "GRANT ALL ON games TO user",
            "REVOKE SELECT ON games FROM user"
        ]

        for query in forbidden_queries:
            valid, message = validator.validate_sql_query(query)
            assert valid is False, f"Query should be blocked: {query}"
            assert "Forbidden SQL keyword" in message

    def test_sql_validator_injection_patterns(self):
        """Test validator detects SQL injection patterns"""
        config = SecurityConfig()
        validator = SQLValidator(config)

        injection_attempts = [
            "SELECT * FROM games; DROP TABLE players",
            "SELECT * FROM games WHERE id = 1 OR 1=1",
            "SELECT * FROM games WHERE name = 'test' OR '1'='1'",
            "SELECT * FROM games UNION SELECT * FROM users",
            "SELECT * FROM games WHERE id = 1 --",
            "SELECT * FROM games WHERE id = 1 /* comment */",
            "SELECT * FROM games WHERE id = EXEC('malicious')"
        ]

        for query in injection_attempts:
            valid, message = validator.validate_sql_query(query)
            assert valid is False, f"Injection should be detected: {query}"

    def test_sql_validator_query_length(self):
        """Test validator enforces query length limit"""
        config = SecurityConfig(max_sql_query_length=100)
        validator = SQLValidator(config)

        # Short query should pass
        valid, _ = validator.validate_sql_query("SELECT * FROM games")
        assert valid is True

        # Long query should fail
        long_query = "SELECT * FROM games WHERE " + " AND ".join([f"col{i} = {i}" for i in range(100)])
        valid, message = validator.validate_sql_query(long_query)
        assert valid is False
        assert "too long" in message

    def test_sql_validator_empty_query(self):
        """Test validator rejects empty queries"""
        config = SecurityConfig()
        validator = SQLValidator(config)

        valid, message = validator.validate_sql_query("")
        assert valid is False
        assert "Empty" in message

        valid, message = validator.validate_sql_query("   ")
        assert valid is False
        assert "Empty" in message

    def test_sql_validator_must_start_with_allowed(self):
        """Test validator requires queries to start with allowed keywords"""
        config = SecurityConfig()
        validator = SQLValidator(config)

        # Should fail - doesn't start with allowed keyword
        valid, message = validator.validate_sql_query("FROM games SELECT *")
        assert valid is False
        assert "must start with allowed keyword" in message

    def test_sql_validator_sanitize_identifier(self):
        """Test SQL identifier sanitization"""
        config = SecurityConfig()
        validator = SQLValidator(config)

        # Valid identifiers
        assert validator.sanitize_sql_identifier("table_name") == "table_name"
        assert validator.sanitize_sql_identifier("Column123") == "Column123"

        # Remove special characters
        assert validator.sanitize_sql_identifier("table-name!@#") == "tablename"
        assert validator.sanitize_sql_identifier("table.name") == "tablename"

        # Fix leading digits
        assert validator.sanitize_sql_identifier("123table") == "_123table"


# ==============================================================================
# Path Validator Tests
# ==============================================================================

class TestPathValidator:
    """Test path traversal prevention"""

    def test_path_validator_valid_paths(self):
        """Test validator allows valid paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig()
            validator = PathValidator(config, tmpdir)

            valid_paths = [
                "test.py",
                "subdir/file.sql",
                "data/results.json",
                "logs/app.log"
            ]

            for path in valid_paths:
                valid, message = validator.validate_file_path(path)
                assert valid is True, f"Path should be valid: {path}"

    def test_path_validator_parent_directory_traversal(self):
        """Test validator blocks parent directory traversal"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig()
            validator = PathValidator(config, tmpdir)

            traversal_attempts = [
                "../etc/passwd",
                "../../secret.txt",
                "subdir/../../etc/shadow",
                "test/../../../etc/passwd"
            ]

            for path in traversal_attempts:
                valid, message = validator.validate_file_path(path)
                assert valid is False, f"Path should be blocked: {path}"
                assert "Forbidden path pattern" in message

    def test_path_validator_forbidden_patterns(self):
        """Test validator blocks forbidden path patterns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig()
            validator = PathValidator(config, tmpdir)

            forbidden_paths = [
                "~/.ssh/id_rsa",
                "/etc/passwd",
                "/root/.bashrc",
                ".env",
                ".git/config",
                "__pycache__/test.pyc"
            ]

            for path in forbidden_paths:
                valid, message = validator.validate_file_path(path)
                assert valid is False, f"Path should be blocked: {path}"

    def test_path_validator_file_extensions(self):
        """Test validator enforces file extension whitelist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig()
            validator = PathValidator(config, tmpdir)

            # Allowed extensions
            for ext in ['.py', '.sql', '.json', '.md', '.txt']:
                path = f"test{ext}"
                valid, message = validator.validate_file_path(path)
                assert valid is True, f"Extension should be allowed: {ext}"

            # Forbidden extensions
            forbidden_exts = ['.exe', '.sh', '.bat', '.dll']
            for ext in forbidden_exts:
                path = f"test{ext}"
                valid, message = validator.validate_file_path(path)
                assert valid is False, f"Extension should be blocked: {ext}"
                assert "not allowed" in message

    def test_path_validator_outside_project_root(self):
        """Test validator blocks paths outside project root"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig()
            validator = PathValidator(config, tmpdir)

            # Try to access file outside project root using absolute path
            outside_path = "/tmp/outside_project.py"
            valid, message = validator.validate_file_path(outside_path)
            assert valid is False
            assert "outside project root" in message

    def test_path_validator_empty_path(self):
        """Test validator rejects empty paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig()
            validator = PathValidator(config, tmpdir)

            valid, message = validator.validate_file_path("")
            assert valid is False
            assert "Empty" in message


# ==============================================================================
# Request Validator Tests
# ==============================================================================

class TestRequestValidator:
    """Test request size and parameter validation"""

    def test_request_validator_size_within_limit(self):
        """Test validator allows requests within size limit"""
        config = SecurityConfig(max_request_size_bytes=1000)
        validator = RequestValidator(config)

        small_data = {"query": "SELECT * FROM games"}
        valid, message = validator.validate_request_size(small_data)
        assert valid is True

    def test_request_validator_size_exceeds_limit(self):
        """Test validator blocks oversized requests"""
        config = SecurityConfig(max_request_size_bytes=100)
        validator = RequestValidator(config)

        large_data = {"data": "x" * 10000}
        valid, message = validator.validate_request_size(large_data)
        assert valid is False
        assert "too large" in message

    def test_request_validator_parameters_valid(self):
        """Test validator allows valid parameters"""
        config = SecurityConfig()
        validator = RequestValidator(config)

        valid_params = {
            "sql_query": "SELECT * FROM games",
            "limit": 10,
            "offset": 0
        }
        valid, message = validator.validate_parameters(valid_params)
        assert valid is True

    def test_request_validator_parameters_not_dict(self):
        """Test validator rejects non-dict parameters"""
        config = SecurityConfig()
        validator = RequestValidator(config)

        valid, message = validator.validate_parameters("not a dict")
        assert valid is False
        assert "must be a dictionary" in message

    def test_request_validator_empty_parameters(self):
        """Test validator rejects empty parameters"""
        config = SecurityConfig()
        validator = RequestValidator(config)

        valid, message = validator.validate_parameters({})
        assert valid is False
        assert "Empty parameters" in message

    def test_request_validator_parameter_too_long(self):
        """Test validator blocks excessively long parameter values"""
        config = SecurityConfig()
        validator = RequestValidator(config)

        params = {"query": "x" * 200000}
        valid, message = validator.validate_parameters(params)
        assert valid is False
        assert "too long" in message


# ==============================================================================
# Timeout Tests
# ==============================================================================

class TestTimeout:
    """Test timeout enforcement"""

    @pytest.mark.asyncio
    async def test_with_timeout_success(self):
        """Test with_timeout allows fast operations"""
        async def fast_operation():
            await asyncio.sleep(0.1)
            return "success"

        result = await with_timeout(fast_operation(), timeout=1.0, operation_name="test")
        assert result == "success"

    @pytest.mark.asyncio
    async def test_with_timeout_exceeded(self):
        """Test with_timeout raises error on timeout"""
        async def slow_operation():
            await asyncio.sleep(2.0)
            return "success"

        with pytest.raises(TimeoutError, match="timed out"):
            await with_timeout(slow_operation(), timeout=0.5, operation_name="test")

    @pytest.mark.asyncio
    async def test_enforce_timeout_decorator_success(self):
        """Test enforce_timeout decorator allows fast operations"""
        @enforce_timeout(1.0)
        async def fast_func():
            await asyncio.sleep(0.1)
            return "success"

        result = await fast_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_enforce_timeout_decorator_exceeded(self):
        """Test enforce_timeout decorator raises error on timeout"""
        @enforce_timeout(0.5)
        async def slow_func():
            await asyncio.sleep(2.0)
            return "success"

        with pytest.raises(TimeoutError, match="timed out"):
            await slow_func()


# ==============================================================================
# Security Manager Integration Tests
# ==============================================================================

class TestSecurityManager:
    """Test security manager orchestration"""

    @pytest.mark.asyncio
    async def test_security_manager_valid_database_request(self):
        """Test security manager allows valid database query"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig(
                rate_limit=RateLimitConfig(requests_per_minute=100)
            )
            manager = SecurityManager(config, tmpdir)

            valid, message = await manager.validate_request(
                client_id="client1",
                tool_name="query_database",
                arguments={"sql_query": "SELECT * FROM games LIMIT 10"}
            )

            assert valid is True

    @pytest.mark.asyncio
    async def test_security_manager_blocks_sql_injection(self):
        """Test security manager blocks SQL injection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig()
            manager = SecurityManager(config, tmpdir)

            valid, message = await manager.validate_request(
                client_id="client1",
                tool_name="query_database",
                arguments={"sql_query": "DROP TABLE games"}
            )

            assert valid is False
            assert "Forbidden SQL keyword" in message

    @pytest.mark.asyncio
    async def test_security_manager_blocks_path_traversal(self):
        """Test security manager blocks path traversal"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig()
            manager = SecurityManager(config, tmpdir)

            valid, message = await manager.validate_request(
                client_id="client1",
                tool_name="read_file",
                arguments={"file_path": "../../../etc/passwd"}
            )

            assert valid is False
            assert "Forbidden path pattern" in message

    @pytest.mark.asyncio
    async def test_security_manager_enforces_rate_limit(self):
        """Test security manager enforces rate limits"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig(
                rate_limit=RateLimitConfig(
                    requests_per_minute=3,
                    burst_size=3
                )
            )
            manager = SecurityManager(config, tmpdir)

            # First 3 should succeed
            for _ in range(3):
                valid, _ = await manager.validate_request(
                    client_id="client1",
                    tool_name="query_database",
                    arguments={"sql_query": "SELECT * FROM games"}
                )
                assert valid is True

            # 4th should fail
            valid, message = await manager.validate_request(
                client_id="client1",
                tool_name="query_database",
                arguments={"sql_query": "SELECT * FROM games"}
            )
            assert valid is False
            assert "Rate limit exceeded" in message

    @pytest.mark.asyncio
    async def test_security_manager_tracks_failed_requests(self):
        """Test security manager tracks failed requests"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig(max_failed_requests=3)
            manager = SecurityManager(config, tmpdir)

            # Make several SQL injection attempts
            for _ in range(5):
                await manager.validate_request(
                    client_id="attacker",
                    tool_name="query_database",
                    arguments={"sql_query": "DROP TABLE games"}
                )

            # Check failed request tracking
            assert "attacker" in manager.failed_requests
            assert len(manager.failed_requests["attacker"]) == 5

    @pytest.mark.asyncio
    async def test_security_manager_get_stats(self):
        """Test security manager provides statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig()
            manager = SecurityManager(config, tmpdir)

            # Make some requests
            await manager.validate_request(
                client_id="client1",
                tool_name="query_database",
                arguments={"sql_query": "SELECT * FROM games"}
            )

            stats = manager.get_security_stats()
            assert "active_clients" in stats
            assert "total_failed_requests" in stats
            assert stats["active_clients"] >= 1

    @pytest.mark.asyncio
    async def test_security_manager_validates_request_size(self):
        """Test security manager validates request size"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SecurityConfig(max_request_size_bytes=100)
            manager = SecurityManager(config, tmpdir)

            # Large request should fail
            valid, message = await manager.validate_request(
                client_id="client1",
                tool_name="query_database",
                arguments={"sql_query": "x" * 10000}
            )

            assert valid is False
            assert "too large" in message


# ==============================================================================
# Configuration Tests
# ==============================================================================

class TestSecurityConfig:
    """Test security configuration"""

    def test_rate_limit_config_defaults(self):
        """Test rate limit config default values"""
        config = RateLimitConfig()
        assert config.requests_per_minute == 60
        assert config.requests_per_hour == 1000
        assert config.burst_size == 10
        assert config.enabled is True

    def test_security_config_defaults(self):
        """Test security config default values"""
        config = SecurityConfig()
        assert config.max_request_size_bytes == 1_048_576  # 1MB
        assert config.max_sql_query_length == 10_000
        assert 'DROP' in config.forbidden_sql_keywords
        assert 'SELECT' in config.allowed_sql_keywords
        assert '.py' in config.allowed_file_extensions

    def test_security_config_custom_values(self):
        """Test security config with custom values"""
        config = SecurityConfig(
            rate_limit=RateLimitConfig(requests_per_minute=100),
            max_request_size_bytes=2_000_000,
            forbidden_sql_keywords={'DROP', 'DELETE'}
        )
        assert config.rate_limit.requests_per_minute == 100
        assert config.max_request_size_bytes == 2_000_000
        assert config.forbidden_sql_keywords == {'DROP', 'DELETE'}


# ==============================================================================
# Run Tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])