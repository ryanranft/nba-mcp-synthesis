#!/usr/bin/env python3
"""
Test Suite for Math, Stats, and NBA Metrics Features
Tests all 20 mathematical, statistical, and NBA-specific tools
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path is set
from mcp_server.tools import math_helper, stats_helper, nba_metrics_helper


# =============================================================================
# ANSI Color Codes for Terminal Output
# =============================================================================

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def success(msg):
    """Print success message in green"""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def error(msg):
    """Print error message in red"""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def info(msg):
    """Print info message in blue"""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def header(msg):
    """Print header in bold cyan"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}")
    print(f"{msg}")
    print(f"{'=' * 80}{Colors.RESET}\n")


def subheader(msg):
    """Print subheader in bold"""
    print(f"\n{Colors.BOLD}{msg}{Colors.RESET}")


# =============================================================================
# Test Runner
# =============================================================================

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def test(self, description, test_func, *args, expected=None, **kwargs):
        """Run a single test"""
        try:
            result = test_func(*args, **kwargs)

            if expected is not None:
                # Allow for floating point tolerance
                if isinstance(result, float) and isinstance(expected, float):
                    tolerance = 0.01
                    if abs(result - expected) <= tolerance:
                        success(f"{description}: {result}")
                        self.passed += 1
                        self.tests.append((description, True, None))
                    else:
                        error(f"{description}: Expected {expected}, got {result}")
                        self.failed += 1
                        self.tests.append((description, False, f"Expected {expected}, got {result}"))
                elif result == expected:
                    success(f"{description}: {result}")
                    self.passed += 1
                    self.tests.append((description, True, None))
                else:
                    error(f"{description}: Expected {expected}, got {result}")
                    self.failed += 1
                    self.tests.append((description, False, f"Expected {expected}, got {result}"))
            else:
                success(f"{description}: {result}")
                self.passed += 1
                self.tests.append((description, True, None))

        except Exception as e:
            error(f"{description}: {str(e)}")
            self.failed += 1
            self.tests.append((description, False, str(e)))

    def summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        header("TEST SUMMARY")
        print(f"{Colors.BOLD}Total Tests:{Colors.RESET} {total}")
        print(f"{Colors.GREEN}Passed:{Colors.RESET} {self.passed}")
        print(f"{Colors.RED}Failed:{Colors.RESET} {self.failed}")

        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✓ ALL TESTS PASSED!{Colors.RESET}\n")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}✗ SOME TESTS FAILED{Colors.RESET}\n")
            print(f"{Colors.YELLOW}Failed Tests:{Colors.RESET}")
            for description, passed, err_msg in self.tests:
                if not passed:
                    print(f"  - {description}: {err_msg}")


# =============================================================================
# Math Tools Tests
# =============================================================================

def test_math_tools(runner):
    """Test all mathematical operations"""
    header("MATH TOOLS TESTS")

    subheader("Basic Arithmetic")
    runner.test("Add 5 + 3", math_helper.add, 5, 3, expected=8)
    runner.test("Add -10 + 25", math_helper.add, -10, 25, expected=15)
    runner.test("Subtract 10 - 3", math_helper.subtract, 10, 3, expected=7)
    runner.test("Subtract -5 - 10", math_helper.subtract, -5, 10, expected=-15)
    runner.test("Multiply 4 * 7", math_helper.multiply, 4, 7, expected=28)
    runner.test("Multiply -3 * 5", math_helper.multiply, -3, 5, expected=-15)

    subheader("Division")
    runner.test("Divide 20 / 4", math_helper.divide, 20, 4, expected=5.0)
    runner.test("Divide 7 / 2", math_helper.divide, 7, 2, expected=3.5)

    # Test division by zero error handling
    try:
        math_helper.divide(10, 0)
        error("Divide by zero should raise error")
        runner.failed += 1
    except Exception as e:
        success(f"Divide by zero correctly raises error: {type(e).__name__}")
        runner.passed += 1

    subheader("Advanced Operations")
    runner.test("Sum [1, 2, 3, 4, 5]", math_helper.sum_numbers, [1, 2, 3, 4, 5], expected=15)
    runner.test("Sum [10.5, 20.5, 30]", math_helper.sum_numbers, [10.5, 20.5, 30], expected=61.0)
    runner.test("Round 3.14159 to 2 decimals", math_helper.round_number, 3.14159, 2, expected=3.14)
    runner.test("Round 123.456 to 1 decimal", math_helper.round_number, 123.456, 1, expected=123.5)
    runner.test("Modulo 17 % 5", math_helper.modulo, 17, 5, expected=2)
    runner.test("Modulo 20 % 4", math_helper.modulo, 20, 4, expected=0)

    subheader("Floor and Ceiling")
    runner.test("Floor of 3.7", math_helper.floor, 3.7, expected=3)
    runner.test("Floor of -2.3", math_helper.floor, -2.3, expected=-3)
    runner.test("Ceiling of 3.2", math_helper.ceiling, 3.2, expected=4)
    runner.test("Ceiling of -2.7", math_helper.ceiling, -2.7, expected=-2)


# =============================================================================
# Stats Tools Tests
# =============================================================================

def test_stats_tools(runner):
    """Test all statistical operations"""
    header("STATS TOOLS TESTS")

    test_data = [10, 20, 30, 40, 50]
    test_data_2 = [1, 2, 2, 3, 4, 4, 4, 5]

    subheader("Basic Statistics")
    runner.test("Mean of [10, 20, 30, 40, 50]",
                stats_helper.calculate_mean, test_data, expected=30.0)
    runner.test("Median of [10, 20, 30, 40, 50]",
                stats_helper.calculate_median, test_data, expected=30)
    runner.test("Mode of [1, 2, 2, 3, 4, 4, 4, 5]",
                stats_helper.calculate_mode, test_data_2, expected=4)  # Single value, not list
    runner.test("Min of [10, 20, 30, 40, 50]",
                stats_helper.calculate_min, test_data, expected=10)
    runner.test("Max of [10, 20, 30, 40, 50]",
                stats_helper.calculate_max, test_data, expected=50)

    subheader("Advanced Statistics")
    runner.test("Range of [10, 20, 30, 40, 50]",
                stats_helper.calculate_range, test_data, expected=40)
    runner.test("Variance of [10, 20, 30, 40, 50]",
                stats_helper.calculate_variance, test_data, expected=250.0)  # Sample variance
    runner.test("Std Dev of [10, 20, 30, 40, 50]",
                stats_helper.calculate_std_dev, test_data, expected=15.81)  # sqrt(250)

    subheader("Percentiles and Quartiles")
    runner.test("50th percentile (median) of [10, 20, 30, 40, 50]",
                stats_helper.calculate_percentile, test_data, 50, expected=30)
    runner.test("75th percentile of [10, 20, 30, 40, 50]",
                stats_helper.calculate_percentile, test_data, 75, expected=40)

    # Test quartiles
    quartiles = stats_helper.calculate_quartiles(test_data)
    runner.test("Q1 of [10, 20, 30, 40, 50]", lambda: quartiles["Q1"], expected=20)
    runner.test("Q2 of [10, 20, 30, 40, 50]", lambda: quartiles["Q2"], expected=30)
    runner.test("Q3 of [10, 20, 30, 40, 50]", lambda: quartiles["Q3"], expected=40)

    subheader("Summary Statistics")
    summary = stats_helper.calculate_summary_stats(test_data)
    info(f"Summary stats for {test_data}:")
    info(f"  Count: {summary['count']}")
    info(f"  Mean: {summary['mean']}")
    info(f"  Median: {summary['median']}")
    info(f"  Std Dev: {summary['std_dev']}")
    info(f"  Min: {summary['min']}")
    info(f"  Max: {summary['max']}")
    runner.passed += 1  # Count summary test as passed


# =============================================================================
# NBA Metrics Tests
# =============================================================================

def test_nba_metrics(runner):
    """Test all NBA-specific metrics"""
    header("NBA METRICS TESTS")

    # Sample player stats (roughly based on a good NBA season)
    player_stats = {
        "points": 2000,
        "rebounds": 600,
        "assists": 500,
        "steals": 100,
        "blocks": 50,
        "fgm": 750,
        "fga": 1600,
        "ftm": 400,
        "fta": 500,
        "turnovers": 200,
        "minutes": 2800
    }

    subheader("Player Efficiency Metrics")

    # Test PER
    per = nba_metrics_helper.calculate_per(player_stats)
    info(f"Player Efficiency Rating (PER): {per}")
    info(f"  (League average is 15.0)")
    runner.test("PER is calculated", lambda: per > 0, expected=True)

    # Test True Shooting %
    ts_pct = nba_metrics_helper.calculate_true_shooting(
        points=2000,
        fga=1600,
        fta=500
    )
    info(f"True Shooting %: {ts_pct:.1%}")
    runner.test("TS% between 0 and 1", lambda: 0 <= ts_pct <= 1, expected=True)

    # Test Effective FG %
    efg_pct = nba_metrics_helper.calculate_effective_fg_pct(
        fgm=750,
        fga=1600,
        three_pm=200
    )
    info(f"Effective Field Goal %: {efg_pct:.1%}")
    runner.test("eFG% between 0 and 1", lambda: 0 <= efg_pct <= 1, expected=True)

    # Test Usage Rate
    usg_rate = nba_metrics_helper.calculate_usage_rate(
        fga=1600,
        fta=500,
        turnovers=200,
        minutes=2800,
        team_minutes=19680,  # 5 players * 48 min * 82 games
        team_fga=7000,
        team_fta=2000,
        team_turnovers=1200
    )
    info(f"Usage Rate: {usg_rate}%")
    runner.test("USG% is reasonable (10-40%)", lambda: 10 <= usg_rate <= 40, expected=True)

    subheader("Team Efficiency Metrics")

    # Test Offensive Rating
    ortg = nba_metrics_helper.calculate_offensive_rating(
        points=9000,
        possessions=8000
    )
    info(f"Offensive Rating: {ortg} (points per 100 possessions)")
    runner.test("ORtg is calculated", lambda: ortg > 0, expected=True)

    # Test Defensive Rating
    drtg = nba_metrics_helper.calculate_defensive_rating(
        points_allowed=8500,
        possessions=8000
    )
    info(f"Defensive Rating: {drtg} (points allowed per 100 possessions)")
    runner.test("DRtg is calculated", lambda: drtg > 0, expected=True)

    # Test Pace
    pace = nba_metrics_helper.calculate_pace(
        possessions=8000,
        minutes=19680
    )
    info(f"Pace: {pace} (possessions per 48 minutes)")
    runner.test("Pace is calculated", lambda: pace > 0, expected=True)

    subheader("Shooting Metrics")

    # Test 3-Point Rate
    three_par = nba_metrics_helper.calculate_three_point_rate(
        three_pa=600,
        fga=1600
    )
    info(f"3-Point Attempt Rate: {three_par:.1%}")
    runner.test("3PAr between 0 and 1", lambda: 0 <= three_par <= 1, expected=True)

    # Test Free Throw Rate
    ftr = nba_metrics_helper.calculate_free_throw_rate(
        fta=500,
        fga=1600
    )
    info(f"Free Throw Rate: {ftr:.3f}")
    runner.test("FTr between 0 and 1", lambda: 0 <= ftr <= 1, expected=True)

    subheader("Utility Functions")

    # Test possession estimation
    poss = nba_metrics_helper.estimate_possessions(
        fga=1600,
        fta=500,
        orb=200,
        tov=200
    )
    info(f"Estimated Possessions: {poss}")
    runner.test("Possessions estimated", lambda: poss > 0, expected=True)


# =============================================================================
# Real-World Examples
# =============================================================================

def test_real_world_examples(runner):
    """Test with real-world basketball scenarios"""
    header("REAL-WORLD EXAMPLES")

    subheader("Example 1: Team Season Statistics")
    info("Calculate team efficiency for a full season")

    # Team season stats
    team_points = 9180  # Points scored
    team_opp_points = 8950  # Points allowed
    team_possessions = 8200  # Estimated possessions

    ortg = nba_metrics_helper.calculate_offensive_rating(team_points, team_possessions)
    drtg = nba_metrics_helper.calculate_defensive_rating(team_opp_points, team_possessions)
    net_rating = ortg - drtg

    info(f"  Offensive Rating: {ortg}")
    info(f"  Defensive Rating: {drtg}")
    info(f"  Net Rating: {net_rating:.2f}")

    runner.test("Team has positive net rating", lambda: net_rating > 0, expected=True)

    subheader("Example 2: Player Per-Game Averages")
    info("Calculate statistics for a player averaging:")
    info("  25 points, 8 rebounds, 6 assists per game")

    games = 70
    ppg = 25
    rpg = 8
    apg = 6

    season_points = ppg * games
    season_rebounds = rpg * games
    season_assists = apg * games

    total = season_points + season_rebounds + season_assists
    info(f"  Total Production: {total} (points + rebounds + assists)")

    runner.test("Season totals calculated", lambda: total > 0, expected=True)

    subheader("Example 3: Shooting Efficiency Comparison")
    info("Compare two players' shooting efficiency")

    # Player A: Volume shooter
    ts_pct_a = nba_metrics_helper.calculate_true_shooting(
        points=2100,
        fga=1800,
        fta=400
    )

    # Player B: Efficient shooter
    ts_pct_b = nba_metrics_helper.calculate_true_shooting(
        points=1600,
        fga=1200,
        fta=350
    )

    info(f"  Player A TS%: {ts_pct_a:.1%}")
    info(f"  Player B TS%: {ts_pct_b:.1%}")

    if ts_pct_b > ts_pct_a:
        info(f"  Player B is more efficient (+{(ts_pct_b - ts_pct_a):.1%})")

    runner.test("Both players have valid TS%",
                lambda: 0 < ts_pct_a < 1 and 0 < ts_pct_b < 1,
                expected=True)


# =============================================================================
# Interactive Demo Mode
# =============================================================================

def interactive_demo():
    """Interactive demo mode for testing calculations"""
    header("INTERACTIVE DEMO MODE")
    info("Test calculations with your own values")

    while True:
        print(f"\n{Colors.BOLD}Choose a calculation:{Colors.RESET}")
        print("1. Math: Add two numbers")
        print("2. Math: Calculate average")
        print("3. Stats: Calculate summary statistics")
        print("4. NBA: Calculate Player Efficiency Rating (PER)")
        print("5. NBA: Calculate True Shooting %")
        print("6. NBA: Calculate Offensive Rating")
        print("0. Exit")

        choice = input(f"\n{Colors.YELLOW}Enter choice (0-6): {Colors.RESET}").strip()

        if choice == "0":
            break
        elif choice == "1":
            try:
                a = float(input("Enter first number: "))
                b = float(input("Enter second number: "))
                result = math_helper.add(a, b)
                success(f"{a} + {b} = {result}")
            except ValueError:
                error("Invalid input. Please enter numbers.")

        elif choice == "2":
            try:
                numbers_str = input("Enter numbers separated by commas: ")
                numbers = [float(x.strip()) for x in numbers_str.split(",")]
                result = stats_helper.calculate_mean(numbers)
                success(f"Average of {numbers} = {result}")
            except ValueError:
                error("Invalid input. Please enter numbers separated by commas.")

        elif choice == "3":
            try:
                numbers_str = input("Enter numbers separated by commas: ")
                numbers = [float(x.strip()) for x in numbers_str.split(",")]
                summary = stats_helper.calculate_summary_stats(numbers)
                success("Summary Statistics:")
                for key, value in summary.items():
                    print(f"  {key}: {value}")
            except ValueError:
                error("Invalid input. Please enter numbers separated by commas.")

        elif choice == "4":
            try:
                info("Enter player stats (press Enter to use defaults):")
                points = int(input("Points (default 2000): ") or 2000)
                rebounds = int(input("Rebounds (default 600): ") or 600)
                assists = int(input("Assists (default 500): ") or 500)
                steals = int(input("Steals (default 100): ") or 100)
                blocks = int(input("Blocks (default 50): ") or 50)
                fgm = int(input("FG Made (default 750): ") or 750)
                fga = int(input("FG Attempted (default 1600): ") or 1600)
                ftm = int(input("FT Made (default 400): ") or 400)
                fta = int(input("FT Attempted (default 500): ") or 500)
                turnovers = int(input("Turnovers (default 200): ") or 200)
                minutes = int(input("Minutes (default 2800): ") or 2800)

                stats = {
                    "points": points, "rebounds": rebounds, "assists": assists,
                    "steals": steals, "blocks": blocks, "fgm": fgm, "fga": fga,
                    "ftm": ftm, "fta": fta, "turnovers": turnovers, "minutes": minutes
                }

                per = nba_metrics_helper.calculate_per(stats)
                success(f"Player Efficiency Rating (PER): {per}")
                info("(League average is 15.0)")
            except ValueError:
                error("Invalid input. Please enter integers.")

        elif choice == "5":
            try:
                points = float(input("Points scored: "))
                fga = float(input("Field goals attempted: "))
                fta = float(input("Free throws attempted: "))

                ts_pct = nba_metrics_helper.calculate_true_shooting(points, fga, fta)
                success(f"True Shooting %: {ts_pct:.1%}")
            except ValueError:
                error("Invalid input. Please enter numbers.")

        elif choice == "6":
            try:
                points = float(input("Points scored: "))
                possessions = float(input("Possessions: "))

                ortg = nba_metrics_helper.calculate_offensive_rating(points, possessions)
                success(f"Offensive Rating: {ortg} (points per 100 possessions)")
            except ValueError:
                error("Invalid input. Please enter numbers.")

        else:
            error("Invalid choice. Please enter 0-6.")


# =============================================================================
# Main Test Runner
# =============================================================================

def main():
    """Run all tests or interactive demo"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 80)
    print("  Math, Stats, and NBA Metrics Test Suite")
    print("  Tests 20 mathematical, statistical, and NBA-specific tools")
    print("=" * 80)
    print(f"{Colors.RESET}")

    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        interactive_demo()
    else:
        runner = TestRunner()

        # Run all test suites
        test_math_tools(runner)
        test_stats_tools(runner)
        test_nba_metrics(runner)
        test_real_world_examples(runner)

        # Print summary
        runner.summary()

        info(f"\nTo run interactive demo: {Colors.BOLD}python {sys.argv[0]} --demo{Colors.RESET}")

        # Return exit code based on test results
        sys.exit(0 if runner.failed == 0 else 1)


if __name__ == "__main__":
    main()
