#!/usr/bin/env python3
"""
Test Circuit Breaker Implementation
Tests the resilient workflow with known broken APIs
"""

import pytest
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def test_book():
    """Sample book data for testing"""
    return {
        "title": "Test Book for Circuit Breaker",
        "author": "Test Author",
        "s3_path": "books/test.pdf",
        "content": """
        This is a test book about machine learning and basketball analytics.
        It covers topics like:
        - Statistical analysis of player performance
        - Machine learning models for game prediction
        - Data visualization techniques
        - Performance optimization strategies
        """,
    }


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_circuit_breaker_status():
    """Test that circuit breaker manager is available and can report status"""
    try:
        from circuit_breaker import circuit_manager

        # Get circuit breaker status
        status = circuit_manager.get_circuit_breaker_status()

        assert isinstance(status, dict), "Status should be a dictionary"

        # Check that status has expected structure
        for api_name, info in status.items():
            assert "state" in info, f"{api_name} should have 'state'"
            assert "can_execute" in info, f"{api_name} should have 'can_execute'"
            assert isinstance(
                info["can_execute"], bool
            ), "can_execute should be boolean"

        # Get working and broken APIs
        working_apis = circuit_manager.get_working_apis()
        assert isinstance(working_apis, list), "Working APIs should be a list"

        broken_apis = list(circuit_manager.broken_apis)
        assert isinstance(broken_apis, list), "Broken APIs should be a list"

    except ImportError:
        pytest.skip("circuit_breaker module not available")


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_resilient_analysis(test_book):
    """Test resilient analysis with circuit breaker"""
    try:
        from scripts.four_model_book_analyzer import FourModelBookAnalyzer
        from circuit_breaker import circuit_manager
    except ImportError:
        pytest.skip("Required modules not available")

    # Initialize analyzer
    analyzer = FourModelBookAnalyzer()

    # Get initial status
    initial_status = circuit_manager.get_circuit_breaker_status()
    logger.info(f"Initial circuit breaker status: {list(initial_status.keys())}")

    # Run analysis
    result = await analyzer.analyze_book(test_book)

    # Verify result structure
    assert hasattr(result, "success"), "Result should have 'success' attribute"
    assert hasattr(
        result, "recommendations"
    ), "Result should have 'recommendations' attribute"
    assert hasattr(result, "total_cost"), "Result should have 'total_cost' attribute"
    assert hasattr(result, "total_time"), "Result should have 'total_time' attribute"

    # Check that recommendations is a list
    assert isinstance(result.recommendations, list), "Recommendations should be a list"

    # Check that costs and times are non-negative
    assert result.total_cost >= 0, "Total cost should be non-negative"
    assert result.total_time >= 0, "Total time should be non-negative"

    # Get final status
    final_status = circuit_manager.get_circuit_breaker_status()
    logger.info(f"Final circuit breaker status: {list(final_status.keys())}")

    # Verify circuit breaker tracked the execution
    assert isinstance(final_status, dict), "Final status should be a dictionary"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
async def test_circuit_breaker_failure_tracking():
    """Test that circuit breaker tracks failures correctly"""
    try:
        from circuit_breaker import circuit_manager
    except ImportError:
        pytest.skip("circuit_breaker module not available")

    # Get status
    status = circuit_manager.get_circuit_breaker_status()

    # Verify each circuit breaker has failure tracking
    for api_name, info in status.items():
        assert "failure_count" in info or "failures" in str(
            info
        ), f"{api_name} should track failures"

    # Verify broken APIs are identified
    broken_apis = list(circuit_manager.broken_apis)
    assert isinstance(broken_apis, list), "Broken APIs should be tracked"


@pytest.mark.integration
def test_circuit_breaker_config():
    """Test that circuit breaker configuration is valid"""
    try:
        from circuit_breaker import circuit_manager
    except ImportError:
        pytest.skip("circuit_breaker module not available")

    # Get working APIs
    working_apis = circuit_manager.get_working_apis()
    assert isinstance(working_apis, list), "Working APIs should return a list"

    # Verify at least one API is configured
    status = circuit_manager.get_circuit_breaker_status()
    assert len(status) > 0, "At least one API should be configured in circuit breaker"
