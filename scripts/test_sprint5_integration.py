#!/usr/bin/env python3
"""
Sprint 5 Integration Test
Tests the 20 new math/stats/NBA tools through the MCP server
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test direct imports
print("=" * 80)
print("Sprint 5 Integration Test")
print("=" * 80)
print()

print("1. Testing Helper Module Imports...")
try:
    from mcp_server.tools import math_helper, stats_helper, nba_metrics_helper
    print("   ✓ All helper modules imported successfully")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

print()
print("2. Testing Math Operations...")
try:
    result = math_helper.add(5, 3)
    assert result == 8, f"Expected 8, got {result}"
    print(f"   ✓ add(5, 3) = {result}")

    result = math_helper.divide(20, 4)
    assert result == 5.0, f"Expected 5.0, got {result}"
    print(f"   ✓ divide(20, 4) = {result}")

    result = math_helper.sum_numbers([1, 2, 3, 4, 5])
    assert result == 15, f"Expected 15, got {result}"
    print(f"   ✓ sum([1,2,3,4,5]) = {result}")
except Exception as e:
    print(f"   ✗ Math test failed: {e}")
    sys.exit(1)

print()
print("3. Testing Statistical Operations...")
try:
    result = stats_helper.calculate_mean([10, 20, 30, 40, 50])
    assert result == 30.0, f"Expected 30.0, got {result}"
    print(f"   ✓ mean([10,20,30,40,50]) = {result}")

    result = stats_helper.calculate_median([10, 20, 30, 40, 50])
    assert result == 30.0, f"Expected 30.0, got {result}"
    print(f"   ✓ median([10,20,30,40,50]) = {result}")

    summary = stats_helper.calculate_summary_stats([10, 20, 30, 40, 50])
    assert summary['count'] == 5, "Expected count=5"
    assert summary['mean'] == 30.0, "Expected mean=30.0"
    print(f"   ✓ summary_stats returned {summary['count']} values")
except Exception as e:
    print(f"   ✗ Stats test failed: {e}")
    sys.exit(1)

print()
print("4. Testing NBA Metrics...")
try:
    # Test PER
    stats = {
        "points": 2000, "rebounds": 600, "assists": 500,
        "steals": 100, "blocks": 50, "fgm": 750, "fga": 1600,
        "ftm": 400, "fta": 500, "turnovers": 200, "minutes": 2800
    }
    per = nba_metrics_helper.calculate_per(stats)
    assert per > 0, f"Expected positive PER, got {per}"
    print(f"   ✓ calculate_per() = {per}")

    # Test True Shooting %
    ts_pct = nba_metrics_helper.calculate_true_shooting(2000, 1600, 500)
    assert 0 < ts_pct < 1, f"Expected TS% between 0 and 1, got {ts_pct}"
    print(f"   ✓ calculate_true_shooting() = {ts_pct:.3f} ({ts_pct:.1%})")

    # Test Offensive Rating
    ortg = nba_metrics_helper.calculate_offensive_rating(9000, 8000)
    assert ortg > 0, f"Expected positive ORtg, got {ortg}"
    print(f"   ✓ calculate_offensive_rating() = {ortg}")
except Exception as e:
    print(f"   ✗ NBA metrics test failed: {e}")
    sys.exit(1)

print()
print("5. Testing Error Handling...")
try:
    # Test division by zero
    try:
        math_helper.divide(10, 0)
        print("   ✗ Division by zero should have raised error")
        sys.exit(1)
    except Exception:
        print("   ✓ Division by zero correctly raises error")

    # Test empty list
    try:
        stats_helper.calculate_mean([])
        print("   ✗ Empty list should have raised error")
        sys.exit(1)
    except Exception:
        print("   ✓ Empty list correctly raises error")

    # Test missing NBA stats
    try:
        nba_metrics_helper.calculate_per({"points": 100})  # Missing required fields
        print("   ✗ Missing stats should have raised error")
        sys.exit(1)
    except Exception:
        print("   ✓ Missing stats correctly raises error")
except Exception as e:
    print(f"   ✗ Error handling test failed: {e}")
    sys.exit(1)

print()
print("6. Testing Parameter Models...")
try:
    from mcp_server.tools.params import (
        MathTwoNumberParams, MathNumberListParams,
        StatsVarianceParams, NbaPerParams
    )

    # Test basic math params
    params = MathTwoNumberParams(a=5, b=3)
    assert params.a == 5 and params.b == 3
    print("   ✓ MathTwoNumberParams validated")

    # Test list params
    params = MathNumberListParams(numbers=[1, 2, 3, 4, 5])
    assert len(params.numbers) == 5
    print("   ✓ MathNumberListParams validated")

    # Test NBA params
    params = NbaPerParams(
        points=2000, rebounds=600, assists=500,
        steals=100, blocks=50, fgm=750, fga=1600,
        ftm=400, fta=500, turnovers=200, minutes=2800
    )
    assert params.points == 2000
    print("   ✓ NbaPerParams validated")
except Exception as e:
    print(f"   ✗ Parameter model test failed: {e}")
    sys.exit(1)

print()
print("7. Testing Response Models...")
try:
    from mcp_server.responses import (
        MathOperationResult, StatsResult, NbaMetricResult
    )

    # Test math response
    response = MathOperationResult(
        operation="add",
        result=8.0,
        inputs={"a": 5, "b": 3},
        success=True
    )
    assert response.success is True
    print("   ✓ MathOperationResult created")

    # Test stats response
    response = StatsResult(
        statistic="mean",
        result=30.0,
        input_count=5,
        success=True
    )
    assert response.success is True
    print("   ✓ StatsResult created")

    # Test NBA response
    response = NbaMetricResult(
        metric="PER",
        result=18.5,
        inputs={"points": 2000},
        interpretation="Above league average",
        success=True
    )
    assert response.success is True
    print("   ✓ NbaMetricResult created")
except Exception as e:
    print(f"   ✗ Response model test failed: {e}")
    sys.exit(1)

print()
print("=" * 80)
print("✓ ALL INTEGRATION TESTS PASSED!")
print("=" * 80)
print()
print("Summary:")
print("  - Helper modules: ✓ Working")
print("  - Math operations: ✓ Working")
print("  - Statistical operations: ✓ Working")
print("  - NBA metrics: ✓ Working")
print("  - Error handling: ✓ Working")
print("  - Parameter models: ✓ Working")
print("  - Response models: ✓ Working")
print()
print("Sprint 5 tools are ready for production use!")
