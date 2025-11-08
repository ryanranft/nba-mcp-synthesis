"""
Integration Tests for Agents 1-3

Tests error handling, monitoring, and security working together.

Agents Covered:
- Agent 1: Error Handling & Recovery
- Agent 2: Monitoring & Observability
- Agent 3: Security & Authentication
"""

import pytest
import time
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime


# Import components from Agents 1-3
# Note: Adjust imports based on actual module structure


@pytest.mark.agents_1_3
class TestErrorHandlingMonitoringIntegration:
    """Test integration between error handling and monitoring systems"""

    def test_errors_are_logged_to_monitoring(self, sample_player_data):
        """Test that errors are properly logged to monitoring system"""
        # This tests that Agent 1 (error handling) integrates with Agent 2 (monitoring)

        from mcp_server.profiling.performance import get_profiler, profile

        profiler = get_profiler()
        profiler.reset()

        @profile
        def function_that_fails():
            raise ValueError("Test error for monitoring")

        # Execute and capture error
        with pytest.raises(ValueError):
            function_that_fails()

        # Verify error was profiled
        stats = profiler.get_summary()
        assert stats['total_calls'] >= 1, "Function call should be profiled even when it fails"

    def test_retry_logic_with_monitoring(self, sample_player_data):
        """Test retry logic is properly monitored"""
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        attempt_count = {'count': 0}

        @profile
        def flaky_function():
            attempt_count['count'] += 1
            if attempt_count['count'] < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        # Implement simple retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = flaky_function()
                break
            except ConnectionError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.01)

        # Verify retries were monitored
        assert attempt_count['count'] == 3, "Should have made 3 attempts"
        stats = profiler.get_summary()
        assert stats['total_calls'] >= 3, "All retry attempts should be profiled"

    def test_circuit_breaker_pattern_monitoring(self):
        """Test circuit breaker pattern is properly monitored"""
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        failure_count = {'count': 0}
        circuit_open = {'open': False}

        @profile
        def protected_function():
            if circuit_open['open']:
                raise Exception("Circuit breaker is open")

            failure_count['count'] += 1
            if failure_count['count'] < 5:
                raise ConnectionError("Service unavailable")
            return "success"

        # Simulate circuit breaker
        threshold = 3
        call_count = 0
        for _ in range(threshold):
            try:
                protected_function()
                call_count += 1
            except ConnectionError:
                call_count += 1
                if failure_count['count'] >= threshold:
                    circuit_open['open'] = True
                    break  # Stop after opening circuit

        # Verify circuit breaker state is tracked
        assert circuit_open['open'], "Circuit breaker should be open after threshold failures"

        # Try to call again (should fail immediately with circuit breaker exception)
        circuit_breaker_triggered = False
        try:
            protected_function()
        except Exception as e:
            if "Circuit breaker is open" in str(e):
                circuit_breaker_triggered = True
                call_count += 1

        assert circuit_breaker_triggered, "Circuit breaker should have triggered"

        # Verify all attempts were profiled
        stats = profiler.get_summary()
        assert stats['total_calls'] == call_count, f"All {call_count} attempts should be profiled"

    def test_error_context_preservation(self, sample_player_data):
        """Test that error context is preserved across components"""

        def process_data_with_context(data):
            """Function that adds context to errors"""
            try:
                # Simulate processing that might fail
                if 'invalid_column' in data.columns:
                    raise KeyError("Invalid column found")
                return data.describe()
            except KeyError as e:
                # Add context to error
                raise ValueError(f"Data processing failed: {str(e)}") from e

        # Create invalid data
        invalid_data = sample_player_data.copy()
        invalid_data['invalid_column'] = None

        # Verify error chain is preserved
        with pytest.raises(ValueError) as exc_info:
            process_data_with_context(invalid_data)

        assert "Data processing failed" in str(exc_info.value)
        assert exc_info.value.__cause__ is not None, "Original exception should be preserved"


@pytest.mark.agents_1_3
@pytest.mark.security
class TestSecurityMonitoringIntegration:
    """Test integration between security and monitoring systems"""

    def test_failed_authentication_attempts_logged(self):
        """Test that failed authentication attempts are logged"""
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        failed_attempts = []

        @profile
        def authenticate_user(username, password):
            """Simulated authentication"""
            if password != "correct_password":
                failed_attempts.append({
                    'username': username,
                    'timestamp': datetime.now()
                })
                raise PermissionError("Authentication failed")
            return True

        # Attempt failed authentication
        with pytest.raises(PermissionError):
            authenticate_user("test_user", "wrong_password")

        # Verify it was logged
        assert len(failed_attempts) == 1
        assert failed_attempts[0]['username'] == "test_user"

        # Verify it was profiled
        stats = profiler.get_summary()
        assert stats['total_calls'] >= 1

    def test_rate_limiting_with_monitoring(self):
        """Test rate limiting is properly monitored"""
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        rate_limit_tracker = {}

        @profile
        def rate_limited_function(user_id):
            """Function with rate limiting"""
            current_time = time.time()

            if user_id not in rate_limit_tracker:
                rate_limit_tracker[user_id] = []

            # Check rate limit (5 requests per second)
            recent_requests = [t for t in rate_limit_tracker[user_id]
                             if current_time - t < 1.0]

            if len(recent_requests) >= 5:
                raise Exception("Rate limit exceeded")

            rate_limit_tracker[user_id].append(current_time)
            return "success"

        # Make requests within rate limit
        user_id = "test_user"
        for _ in range(5):
            rate_limited_function(user_id)

        # Exceed rate limit
        with pytest.raises(Exception, match="Rate limit exceeded"):
            rate_limited_function(user_id)

        # Verify all attempts were profiled
        stats = profiler.get_summary()
        assert stats['total_calls'] >= 6

    def test_security_audit_trail(self, sample_player_data):
        """Test security audit trail generation"""
        audit_log = []

        def log_security_event(event_type, user, action, resource):
            """Log security event"""
            audit_log.append({
                'timestamp': datetime.now(),
                'event_type': event_type,
                'user': user,
                'action': action,
                'resource': resource
            })

        # Simulate various security events
        log_security_event('authentication', 'user1', 'login', 'api')
        log_security_event('authorization', 'user1', 'read', 'player_data')
        log_security_event('data_access', 'user1', 'query', 'database')

        # Verify audit trail
        assert len(audit_log) == 3
        assert all('timestamp' in event for event in audit_log)
        assert all('user' in event for event in audit_log)


@pytest.mark.agents_1_3
class TestErrorRecoverySecurityIntegration:
    """Test integration between error recovery and security"""

    def test_secure_error_messages(self):
        """Test that error messages don't leak sensitive information"""

        def secure_database_query(query, credentials):
            """Simulated database query with credentials"""
            if "DROP TABLE" in query:
                # Don't include credentials or query details in error
                raise ValueError("Invalid query detected")
            return []

        # Attempt malicious query
        malicious_query = "DROP TABLE users;"
        fake_credentials = {"password": "secret123"}

        with pytest.raises(ValueError) as exc_info:
            secure_database_query(malicious_query, fake_credentials)

        # Verify sensitive data not in error message
        error_msg = str(exc_info.value)
        assert "secret123" not in error_msg, "Password should not appear in error"
        assert "DROP TABLE" not in error_msg, "Query should not appear in error"

    def test_error_handling_preserves_security_context(self):
        """Test that error handling doesn't bypass security checks"""

        security_checks_passed = {'authentication': False, 'authorization': False}

        def secure_operation(user_role):
            """Operation requiring authentication and authorization"""
            try:
                # Authentication
                if user_role is None:
                    raise PermissionError("Not authenticated")
                security_checks_passed['authentication'] = True

                # Authorization
                if user_role != 'admin':
                    raise PermissionError("Insufficient permissions")
                security_checks_passed['authorization'] = True

                return "Operation successful"
            except PermissionError:
                # Reset security context on error
                security_checks_passed['authentication'] = False
                security_checks_passed['authorization'] = False
                raise

        # Test with insufficient permissions
        with pytest.raises(PermissionError):
            secure_operation('user')

        # Verify security context was reset
        assert not security_checks_passed['authorization'], \
            "Authorization should not persist after error"

    def test_cascading_failures_with_security(self):
        """Test that cascading failures maintain security boundaries"""

        def protected_resource_access(user, resource):
            """Access resource with permission check"""
            if user != 'authorized_user':
                raise PermissionError("Access denied")

            # Simulate accessing resource
            if resource == 'missing':
                raise FileNotFoundError("Resource not found")

            return f"Accessed {resource}"

        # Test permission failure
        with pytest.raises(PermissionError):
            protected_resource_access('unauthorized_user', 'data')

        # Test resource failure (after passing security)
        with pytest.raises(FileNotFoundError):
            protected_resource_access('authorized_user', 'missing')

        # Verify successful access
        result = protected_resource_access('authorized_user', 'data')
        assert result == "Accessed data"


@pytest.mark.agents_1_3
@pytest.mark.performance
class TestMonitoringPerformanceIntegration:
    """Test monitoring system performance under load"""

    def test_monitoring_overhead_acceptable(self, sample_player_data):
        """Test that monitoring adds acceptable overhead"""
        from mcp_server.profiling.performance import profile, get_profiler

        profiler = get_profiler()
        profiler.reset()

        def unmonitored_function(data):
            return data.describe()

        @profile
        def monitored_function(data):
            return data.describe()

        # Measure unmonitored performance
        start = time.time()
        for _ in range(10):
            unmonitored_function(sample_player_data)
        unmonitored_time = time.time() - start

        # Measure monitored performance
        start = time.time()
        for _ in range(10):
            monitored_function(sample_player_data)
        monitored_time = time.time() - start

        overhead_ms = (monitored_time - unmonitored_time) * 1000

        # Overhead should be less than 50ms total for 10 calls (5ms per call)
        assert overhead_ms < 50, f"Monitoring overhead too high: {overhead_ms:.2f}ms"

    def test_concurrent_monitoring(self, sample_player_data):
        """Test monitoring works correctly with concurrent operations"""
        from mcp_server.profiling.performance import profile, get_profiler
        from concurrent.futures import ThreadPoolExecutor

        profiler = get_profiler()
        profiler.reset()

        @profile
        def concurrent_task(task_id):
            time.sleep(0.01)
            return task_id

        # Execute tasks concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(concurrent_task, i) for i in range(20)]
            results = [f.result() for f in futures]

        # Verify all tasks were monitored
        assert len(results) == 20
        stats = profiler.get_summary()
        assert stats['total_calls'] >= 20, "All concurrent calls should be profiled"


@pytest.mark.agents_1_3
def test_comprehensive_agent_1_3_workflow(sample_player_data, test_helper):
    """
    Comprehensive test of Agents 1-3 working together

    Scenario: Process player data with error handling, monitoring, and security
    """
    from mcp_server.profiling.performance import profile, get_profiler

    profiler = get_profiler()
    profiler.reset()

    # Track workflow state
    workflow_state = {
        'authenticated': False,
        'data_validated': False,
        'processing_complete': False,
        'errors': [],
        'security_events': []
    }

    @profile
    def authenticate(user_id):
        """Step 1: Authentication"""
        if user_id is None:
            workflow_state['errors'].append('Authentication failed')
            raise PermissionError("User ID required")
        workflow_state['authenticated'] = True
        workflow_state['security_events'].append('user_authenticated')
        return True

    @profile
    def validate_data(data):
        """Step 2: Data validation"""
        if data is None or data.empty:
            workflow_state['errors'].append('Invalid data')
            raise ValueError("Data validation failed")

        required_cols = ['player_id', 'points', 'minutes']
        missing = [col for col in required_cols if col not in data.columns]
        if missing:
            workflow_state['errors'].append(f'Missing columns: {missing}')
            raise ValueError(f"Missing required columns: {missing}")

        workflow_state['data_validated'] = True
        return True

    @profile
    def process_data(data):
        """Step 3: Process data"""
        try:
            result = data.groupby('player_id')['points'].mean()
            workflow_state['processing_complete'] = True
            return result
        except Exception as e:
            workflow_state['errors'].append(f'Processing error: {str(e)}')
            raise

    # Execute workflow
    authenticate('test_user')
    validate_data(sample_player_data)
    result = process_data(sample_player_data)

    # Verify workflow completed successfully
    assert workflow_state['authenticated'], "Should be authenticated"
    assert workflow_state['data_validated'], "Data should be validated"
    assert workflow_state['processing_complete'], "Processing should complete"
    assert len(workflow_state['errors']) == 0, f"No errors expected: {workflow_state['errors']}"

    # Verify all steps were monitored
    stats = profiler.get_summary()
    assert stats['total_calls'] >= 3, "All workflow steps should be profiled"
    assert len(result) > 0, "Should have processed data"

    # Verify security events logged
    assert 'user_authenticated' in workflow_state['security_events']
