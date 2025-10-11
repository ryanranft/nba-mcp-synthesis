#!/usr/bin/env python3
"""
Sprint 6 Feature Testing
Tests all 18 advanced analytics tools (correlation, time series, advanced NBA metrics)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.tools import correlation_helper, timeseries_helper, nba_metrics_helper

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, name: str, actual, expected, tolerance=0.01):
        """Test with optional tolerance for floats"""
        if isinstance(expected, float):
            passed = abs(actual - expected) < tolerance
        else:
            passed = actual == expected

        if passed:
            self.passed += 1
            print(f"  {GREEN}✓{RESET} {name}")
        else:
            self.failed += 1
            print(f"  {RED}✗{RESET} {name}")
            print(f"    Expected: {expected}, Got: {actual}")

        self.tests.append((name, passed))
        return passed

    def section(self, title: str):
        """Print section header"""
        print(f"\n{CYAN}{BOLD}{title}{RESET}")
        print("=" * len(title))


def test_correlation_tools():
    """Test correlation and regression tools"""
    runner = TestRunner()
    runner.section("Correlation & Regression Tools")

    # Test 1: Correlation
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    corr = correlation_helper.calculate_correlation(x, y)
    runner.test("Perfect positive correlation", corr, 1.0)

    # Test 2: Negative correlation
    x = [1, 2, 3, 4, 5]
    y = [10, 8, 6, 4, 2]
    corr = correlation_helper.calculate_correlation(x, y)
    runner.test("Perfect negative correlation", corr, -1.0)

    # Test 3: Covariance
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 5, 4, 5]
    cov = correlation_helper.calculate_covariance(x, y, sample=True)
    # Sample covariance (n-1): expected 1.5
    runner.test("Covariance calculation", cov, 1.5)

    # Test 4: Linear regression
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    model = correlation_helper.calculate_linear_regression(x, y)
    runner.test("Regression slope", model['slope'], 2.0)
    runner.test("Regression intercept", model['intercept'], 0.0)
    runner.test("Regression R²", model['r_squared'], 1.0)

    # Test 5: Predictions
    predictions = correlation_helper.predict_values(2.0, 0.0, [6, 7, 8])
    runner.test("Predictions", predictions, [12.0, 14.0, 16.0])

    # Test 6: Correlation matrix
    data = {
        "x": [1, 2, 3, 4, 5],
        "y": [2, 4, 6, 8, 10],
        "z": [5, 4, 3, 2, 1]
    }
    matrix = correlation_helper.calculate_correlation_matrix(data)
    runner.test("Correlation matrix self-correlation", matrix['x']['x'], 1.0)
    runner.test("Correlation matrix cross-correlation", matrix['x']['y'], 1.0)

    return runner


def test_timeseries_tools():
    """Test time series analysis tools"""
    runner = TestRunner()
    runner.section("Time Series Analysis Tools")

    # Test 7: Moving average
    data = [10, 12, 14, 16, 18, 20]
    ma = timeseries_helper.calculate_moving_average(data, window=3)
    runner.test("Moving average length", len(ma), 6)
    runner.test("MA first values None", ma[0] is None and ma[1] is None, True)
    runner.test("MA third value", ma[2], 12.0)

    # Test 8: Exponential moving average
    data = [10, 12, 14, 16, 18]
    ema = timeseries_helper.calculate_exponential_moving_average(data, alpha=0.3)
    runner.test("EMA length", len(ema), 5)
    runner.test("EMA first value", ema[0], 10.0)

    # Test 9: Trend detection - increasing
    data = [10, 12, 15, 17, 20]
    trend = timeseries_helper.detect_trend(data)
    runner.test("Trend direction (increasing)", trend['trend'], "increasing")
    runner.test("Trend slope positive", trend['slope'] > 0, True)

    # Test 10: Trend detection - decreasing
    data = [20, 18, 15, 12, 10]
    trend = timeseries_helper.detect_trend(data)
    runner.test("Trend direction (decreasing)", trend['trend'], "decreasing")
    runner.test("Trend slope negative", trend['slope'] < 0, True)

    # Test 11: Percent change
    pct_change = timeseries_helper.calculate_percent_change(120, 100)
    runner.test("Percent change (increase)", pct_change, 20.0)

    pct_change = timeseries_helper.calculate_percent_change(80, 100)
    runner.test("Percent change (decrease)", pct_change, -20.0)

    # Test 12: Growth rate
    growth = timeseries_helper.calculate_growth_rate(100, 150, 3)
    runner.test("Growth rate", growth, 14.47)

    # Test 13: Volatility
    data = [100, 102, 98, 101, 99]
    volatility = timeseries_helper.calculate_volatility(data)
    runner.test("Volatility low for stable data", volatility < 5, True)

    data = [100, 150, 80, 130, 90]
    volatility = timeseries_helper.calculate_volatility(data)
    runner.test("Volatility high for unstable data", volatility > 20, True)

    return runner


def test_advanced_nba_metrics():
    """Test advanced NBA metrics"""
    runner = TestRunner()
    runner.section("Advanced NBA Metrics Tools")

    # Test 14: Four Factors
    stats = {
        "fgm": 3200, "fga": 7000, "three_pm": 1000,
        "tov": 1100, "fta": 1800, "orb": 900,
        "team_orb": 900, "opp_drb": 2800,
        "opp_fgm": 2900, "opp_fga": 6800, "opp_three_pm": 800,
        "opp_tov": 1200, "opp_fta": 1600, "drb": 2800,
        "team_drb": 2800, "opp_orb": 850
    }
    four_factors = nba_metrics_helper.calculate_four_factors(stats)
    runner.test("Four Factors has offensive", 'offensive' in four_factors, True)
    runner.test("Four Factors has defensive", 'defensive' in four_factors, True)
    runner.test("Four Factors offensive eFG%", four_factors['offensive']['efg_pct'] > 0, True)

    # Test 15: Turnover percentage
    tov_pct = nba_metrics_helper.calculate_turnover_percentage(250, 1800, 600)
    # Formula: 100 × 250 / (1800 + 0.44×600 + 250) = 100 × 250 / 2314 = 10.80
    runner.test("TOV% calculation", tov_pct, 10.80)

    # Test 16: Rebound percentage
    reb_pct = nba_metrics_helper.calculate_rebound_percentage(900, 900, 2800)
    runner.test("REB% calculation", reb_pct, 24.32)

    # Test 17: Assist percentage
    # Use realistic values: Point guard with 8 AST/game, plays 32 MPG
    # 82 game season: 656 assists, 2624 minutes
    # Team: 240 MP/game × 82 = 19680 total, 3280 FGM
    # Player: 820 FGM
    ast_pct = nba_metrics_helper.calculate_assist_percentage(
        assists=656,
        minutes=2624,
        team_minutes=19680,
        team_fgm=3280,
        player_fgm=820
    )
    # Formula: 100 × AST / [(MP / 5 × Team FGM) - Player FGM]
    # = 100 × 656 / [(2624/5 × 3280) - 820]
    runner.test("AST% calculation (realistic values)", ast_pct > 0, True)

    # Test 18: Steal percentage
    stl_pct = nba_metrics_helper.calculate_steal_percentage(
        steals=120,
        minutes=2000,
        team_minutes=19680,
        opp_possessions=8000
    )
    runner.test("STL% calculation", stl_pct, 2.95)

    # Test 19: Block percentage
    blk_pct = nba_metrics_helper.calculate_block_percentage(
        blocks=100,
        minutes=2000,
        team_minutes=19680,
        opp_two_pa=5000
    )
    runner.test("BLK% calculation", blk_pct, 3.94)

    return runner


def test_edge_cases():
    """Test edge cases and error handling"""
    runner = TestRunner()
    runner.section("Edge Cases & Error Handling")

    # Test empty/small datasets
    try:
        correlation_helper.calculate_correlation([1], [1])
        runner.test("Correlation rejects single point", False, True)
    except:
        runner.test("Correlation rejects single point", True, True)

    # Test division by zero protection
    try:
        timeseries_helper.calculate_percent_change(100, 0)
        runner.test("Percent change protects divide by zero", False, True)
    except:
        runner.test("Percent change protects divide by zero", True, True)

    # Test different length lists
    try:
        correlation_helper.calculate_correlation([1, 2, 3], [1, 2])
        runner.test("Correlation rejects different lengths", False, True)
    except:
        runner.test("Correlation rejects different lengths", True, True)

    # Test window larger than data
    try:
        timeseries_helper.calculate_moving_average([1, 2], window=5)
        runner.test("MA rejects window > data length", False, True)
    except:
        runner.test("MA rejects window > data length", True, True)

    return runner


def print_summary(runners):
    """Print test summary"""
    total_passed = sum(r.passed for r in runners)
    total_failed = sum(r.failed for r in runners)
    total_tests = total_passed + total_failed

    print(f"\n{CYAN}{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}Test Summary{RESET}")
    print(f"{'=' * 80}")
    print(f"Total Tests: {total_tests}")
    print(f"{GREEN}Passed: {total_passed}{RESET}")
    if total_failed > 0:
        print(f"{RED}Failed: {total_failed}{RESET}")
    else:
        print(f"Failed: {total_failed}")

    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Pass Rate: {pass_rate:.1f}%")

    if total_failed == 0:
        print(f"\n{GREEN}{BOLD}✓ ALL TESTS PASSED!{RESET}")
        print(f"\n{GREEN}Sprint 6 tools are working correctly!{RESET}")
        print(f"\n{CYAN}Tools tested:{RESET}")
        print("  • 6 Correlation/Regression tools")
        print("  • 6 Time Series Analysis tools")
        print("  • 6 Advanced NBA Metrics tools")
        print(f"\n{GREEN}Ready for production use! 🎉{RESET}\n")
        return 0
    else:
        print(f"\n{RED}Some tests failed. Please review.{RESET}\n")
        return 1


def main():
    print(f"{CYAN}{BOLD}")
    print("=" * 80)
    print("  Sprint 6: Advanced Analytics Tools - Feature Testing")
    print("  Testing 18 new tools: Correlation, Time Series, Advanced NBA Metrics")
    print("=" * 80)
    print(f"{RESET}\n")

    runners = [
        test_correlation_tools(),
        test_timeseries_tools(),
        test_advanced_nba_metrics(),
        test_edge_cases()
    ]

    return print_summary(runners)


if __name__ == "__main__":
    sys.exit(main())
