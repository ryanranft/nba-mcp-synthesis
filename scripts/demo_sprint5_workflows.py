#!/usr/bin/env python3
"""
Sprint 5 Workflow Demonstrations
Real-world NBA analysis workflows using the new math/stats/NBA tools

Demonstrates:
1. Player Efficiency Analysis
2. Team Performance Comparison
3. Statistical Distribution Analysis
4. Shooting Efficiency Evaluation
5. Season Trend Analysis
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.tools import math_helper, stats_helper, nba_metrics_helper


# ANSI colors for output
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def header(text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}")
    print(f"{text}")
    print(f"{'=' * 80}{Colors.RESET}\n")


def subheader(text):
    print(f"\n{Colors.BOLD}{text}{Colors.RESET}")


def info(text):
    print(f"{Colors.BLUE}{text}{Colors.RESET}")


def success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def metric(name, value, unit=""):
    print(f"  {Colors.BOLD}{name:30s}{Colors.RESET} {value:>10s} {unit}")


# =============================================================================
# Workflow 1: Player Efficiency Analysis
# =============================================================================


def workflow_player_efficiency():
    """Analyze a player's efficiency using multiple metrics"""

    header("Workflow 1: Player Efficiency Analysis")

    info("Scenario: Analyzing a star player's season performance")
    print()

    # Sample player stats (e.g., LeBron James 2022-23)
    player_name = "Star Player"
    stats = {
        "points": 1590,
        "rebounds": 540,
        "assists": 470,
        "steals": 60,
        "blocks": 45,
        "fgm": 620,
        "fga": 1280,
        "ftm": 350,
        "fta": 460,
        "three_pm": 180,
        "turnovers": 195,
        "minutes": 2016,
    }

    subheader(f"Player: {player_name}")
    print(f"  Games: ~56 (estimated)")
    print(f"  Minutes: {stats['minutes']}")
    print()

    # Calculate per-game averages using math tools
    games = math_helper.round_number(stats["minutes"] / 36, 0)
    ppg = math_helper.round_number(stats["points"] / games, 1)
    rpg = math_helper.round_number(stats["rebounds"] / games, 1)
    apg = math_helper.round_number(stats["assists"] / games, 1)

    subheader("Per-Game Averages")
    metric("Points Per Game", f"{ppg}")
    metric("Rebounds Per Game", f"{rpg}")
    metric("Assists Per Game", f"{apg}")

    # Calculate efficiency metrics
    subheader("Efficiency Metrics")

    # PER - Player Efficiency Rating
    per = nba_metrics_helper.calculate_per(stats)
    metric("PER (Player Efficiency)", f"{per:.1f}", "(League avg: 15.0)")

    # True Shooting %
    ts_pct = nba_metrics_helper.calculate_true_shooting(
        stats["points"], stats["fga"], stats["fta"]
    )
    metric("True Shooting %", f"{ts_pct:.1%}", "(Good: >55%)")

    # Effective FG %
    efg_pct = nba_metrics_helper.calculate_effective_fg_pct(
        stats["fgm"], stats["fga"], stats["three_pm"]
    )
    metric("Effective FG %", f"{efg_pct:.1%}", "(Adjusts for 3PT)")

    # Interpretation
    subheader("Analysis")

    if per > 20:
        success(f"PER of {per:.1f} indicates All-Star level performance")
    elif per > 15:
        success(f"PER of {per:.1f} indicates above-average performance")
    else:
        info(f"PER of {per:.1f} indicates average or below performance")

    if ts_pct > 0.60:
        success(f"TS% of {ts_pct:.1%} indicates elite shooting efficiency")
    elif ts_pct > 0.55:
        success(f"TS% of {ts_pct:.1%} indicates good shooting efficiency")
    else:
        info(f"TS% of {ts_pct:.1%} indicates average shooting efficiency")

    print()


# =============================================================================
# Workflow 2: Team Performance Comparison
# =============================================================================


def workflow_team_comparison():
    """Compare offensive and defensive efficiency of multiple teams"""

    header("Workflow 2: Team Performance Comparison")

    info("Scenario: Comparing 4 NBA teams' offensive and defensive efficiency")
    print()

    teams = [
        {"name": "Team A", "points_for": 9180, "points_against": 8650, "poss": 8200},
        {"name": "Team B", "points_for": 8950, "points_against": 8900, "poss": 8150},
        {"name": "Team C", "points_for": 8720, "points_against": 9100, "poss": 8180},
        {"name": "Team D", "points_for": 9340, "points_against": 8580, "poss": 8220},
    ]

    # Calculate efficiency ratings for each team
    results = []
    for team in teams:
        ortg = nba_metrics_helper.calculate_offensive_rating(
            team["points_for"], team["poss"]
        )
        drtg = nba_metrics_helper.calculate_defensive_rating(
            team["points_against"], team["poss"]
        )
        net_rating = math_helper.subtract(ortg, drtg)
        net_rating = math_helper.round_number(net_rating, 1)

        results.append(
            {"name": team["name"], "ortg": ortg, "drtg": drtg, "net_rating": net_rating}
        )

    # Display results
    subheader("Efficiency Ratings (per 100 possessions)")
    print(f"  {'Team':8s} {'ORtg':>8s} {'DRtg':>8s} {'NetRtg':>8s}  {'Assessment':20s}")
    print(f"  {'-' * 60}")

    for r in results:
        if r["net_rating"] > 5:
            assessment = "Championship Caliber"
        elif r["net_rating"] > 2:
            assessment = "Playoff Team"
        elif r["net_rating"] > -2:
            assessment = "Average"
        else:
            assessment = "Below Average"

        print(
            f"  {r['name']:8s} {r['ortg']:8.1f} {r['drtg']:8.1f} {r['net_rating']:+8.1f}  {assessment:20s}"
        )

    # Statistical analysis of ratings
    subheader("League-Wide Statistics")

    ortg_values = [r["ortg"] for r in results]
    drtg_values = [r["drtg"] for r in results]
    net_values = [r["net_rating"] for r in results]

    ortg_mean = stats_helper.calculate_mean(ortg_values)
    drtg_mean = stats_helper.calculate_mean(drtg_values)

    metric("Average ORtg", f"{ortg_mean:.1f}")
    metric("Average DRtg", f"{drtg_mean:.1f}")
    metric("ORtg Range", f"{stats_helper.calculate_range(ortg_values):.1f}")
    metric("DRtg Range", f"{stats_helper.calculate_range(drtg_values):.1f}")

    # Find best offensive and defensive teams
    best_offense = max(results, key=lambda x: x["ortg"])
    best_defense = min(results, key=lambda x: x["drtg"])  # Lower is better for defense

    subheader("Standout Performers")
    success(f"Best Offense: {best_offense['name']} ({best_offense['ortg']:.1f} ORtg)")
    success(f"Best Defense: {best_defense['name']} ({best_defense['drtg']:.1f} DRtg)")

    print()


# =============================================================================
# Workflow 3: Statistical Distribution Analysis
# =============================================================================


def workflow_statistical_analysis():
    """Analyze the distribution of player statistics"""

    header("Workflow 3: Statistical Distribution Analysis")

    info("Scenario: Analyzing scoring distribution across 50 players")
    print()

    # Sample points-per-game data for 50 players
    ppg_data = [
        28.5,
        27.2,
        25.8,
        24.3,
        22.7,
        21.9,
        20.5,
        19.8,
        18.4,
        17.6,
        16.9,
        16.2,
        15.7,
        15.3,
        14.8,
        14.2,
        13.8,
        13.4,
        12.9,
        12.5,
        12.1,
        11.7,
        11.3,
        10.9,
        10.5,
        10.2,
        9.8,
        9.5,
        9.1,
        8.8,
        8.5,
        8.2,
        7.9,
        7.6,
        7.3,
        7.0,
        6.7,
        6.5,
        6.2,
        6.0,
        5.8,
        5.5,
        5.3,
        5.1,
        4.8,
        4.6,
        4.4,
        4.2,
        4.0,
        3.8,
    ]

    # Calculate comprehensive statistics
    summary = stats_helper.calculate_summary_stats(ppg_data)

    subheader("Points Per Game Distribution (n=50 players)")

    metric("Count", f"{summary['count']}")
    metric("Mean", f"{summary['mean']:.2f}", "ppg")
    metric("Median", f"{summary['median']:.2f}", "ppg")
    metric("Std Dev", f"{summary['std_dev']:.2f}", "ppg")
    print()
    metric("Minimum", f"{summary['min']:.1f}", "ppg")
    metric("Q1 (25th percentile)", f"{summary['Q1']:.2f}", "ppg")
    metric("Q2 (Median)", f"{summary['Q2']:.2f}", "ppg")
    metric("Q3 (75th percentile)", f"{summary['Q3']:.2f}", "ppg")
    metric("Maximum", f"{summary['max']:.1f}", "ppg")
    print()
    metric("Range", f"{summary['range']:.1f}", "ppg")
    metric("IQR (Q3 - Q1)", f"{summary['IQR']:.2f}", "ppg")

    # Identify scoring tiers
    subheader("Scoring Tiers")

    elite_scorers = [x for x in ppg_data if x >= 25]
    good_scorers = [x for x in ppg_data if 15 <= x < 25]
    average_scorers = [x for x in ppg_data if 10 <= x < 15]
    bench_players = [x for x in ppg_data if x < 10]

    print(
        f"  Elite Scorers (≥25 ppg): {len(elite_scorers)} players ({len(elite_scorers)/len(ppg_data)*100:.1f}%)"
    )
    print(
        f"  Good Scorers (15-24 ppg): {len(good_scorers)} players ({len(good_scorers)/len(ppg_data)*100:.1f}%)"
    )
    print(
        f"  Average Scorers (10-14 ppg): {len(average_scorers)} players ({len(average_scorers)/len(ppg_data)*100:.1f}%)"
    )
    print(
        f"  Bench Players (<10 ppg): {len(bench_players)} players ({len(bench_players)/len(ppg_data)*100:.1f}%)"
    )

    # Calculate averages for each tier
    subheader("Tier Averages")

    if elite_scorers:
        elite_avg = stats_helper.calculate_mean(elite_scorers)
        print(f"  Elite Scorers Average: {elite_avg:.2f} ppg")

    if good_scorers:
        good_avg = stats_helper.calculate_mean(good_scorers)
        print(f"  Good Scorers Average: {good_avg:.2f} ppg")

    if average_scorers:
        avg_avg = stats_helper.calculate_mean(average_scorers)
        print(f"  Average Scorers Average: {avg_avg:.2f} ppg")

    print()


# =============================================================================
# Workflow 4: Shooting Efficiency Evaluation
# =============================================================================


def workflow_shooting_efficiency():
    """Evaluate and compare shooting efficiency of multiple players"""

    header("Workflow 4: Shooting Efficiency Evaluation")

    info("Scenario: Comparing shooting efficiency of 5 players")
    print()

    players = [
        {
            "name": "Player A",
            "pts": 1800,
            "fgm": 680,
            "fga": 1400,
            "3pm": 200,
            "fta": 420,
        },
        {
            "name": "Player B",
            "pts": 2100,
            "fgm": 780,
            "fga": 1650,
            "3pm": 150,
            "fta": 510,
        },
        {
            "name": "Player C",
            "pts": 1650,
            "fgm": 640,
            "fga": 1200,
            "3pm": 110,
            "fta": 370,
        },
        {
            "name": "Player D",
            "pts": 1920,
            "fgm": 720,
            "fga": 1480,
            "3pm": 180,
            "fta": 480,
        },
        {
            "name": "Player E",
            "pts": 1740,
            "fgm": 650,
            "fga": 1350,
            "3pm": 160,
            "fta": 440,
        },
    ]

    # Calculate efficiency metrics for each player
    results = []
    for player in players:
        # Traditional FG%
        fg_pct = math_helper.divide(player["fgm"], player["fga"])

        # Effective FG% (accounts for 3-pointers)
        efg_pct = nba_metrics_helper.calculate_effective_fg_pct(
            player["fgm"], player["fga"], player["3pm"]
        )

        # True Shooting % (accounts for free throws)
        ts_pct = nba_metrics_helper.calculate_true_shooting(
            player["pts"], player["fga"], player["fta"]
        )

        # 3-point rate
        three_par = nba_metrics_helper.calculate_three_point_rate(
            player["3pm"] * 2.5, player["fga"]  # Estimate attempts from makes
        )

        results.append(
            {
                "name": player["name"],
                "fg_pct": fg_pct,
                "efg_pct": efg_pct,
                "ts_pct": ts_pct,
                "three_par": three_par,
            }
        )

    # Display results
    subheader("Shooting Efficiency Comparison")
    print(
        f"  {'Player':10s} {'FG%':>8s} {'eFG%':>8s} {'TS%':>8s} {'3PAr':>8s}  {'Grade':6s}"
    )
    print(f"  {'-' * 65}")

    for r in results:
        # Grade based on TS%
        if r["ts_pct"] > 0.60:
            grade = "A"
        elif r["ts_pct"] > 0.57:
            grade = "B+"
        elif r["ts_pct"] > 0.55:
            grade = "B"
        elif r["ts_pct"] > 0.52:
            grade = "C+"
        else:
            grade = "C"

        print(
            f"  {r['name']:10s} {r['fg_pct']:7.1%} {r['efg_pct']:7.1%} "
            f"{r['ts_pct']:7.1%} {r['three_par']:7.1%}  {grade:6s}"
        )

    # Statistical analysis
    subheader("League Average Comparison")

    ts_values = [r["ts_pct"] for r in results]
    ts_mean = stats_helper.calculate_mean(ts_values)
    ts_median = stats_helper.calculate_median(ts_values)

    metric("Average TS%", f"{ts_mean:.1%}")
    metric("Median TS%", f"{ts_median:.1%}")

    best_shooter = max(results, key=lambda x: x["ts_pct"])
    worst_shooter = min(results, key=lambda x: x["ts_pct"])

    subheader("Efficiency Leaders")
    success(
        f"Most Efficient: {best_shooter['name']} ({best_shooter['ts_pct']:.1%} TS%)"
    )
    info(
        f"Least Efficient: {worst_shooter['name']} ({worst_shooter['ts_pct']:.1%} TS%)"
    )

    # Calculate efficiency gap
    gap = math_helper.subtract(best_shooter["ts_pct"], worst_shooter["ts_pct"])
    gap_pct = math_helper.multiply(gap, 100)
    print(f"  Efficiency Gap: {gap_pct:.1f} percentage points")

    print()


# =============================================================================
# Workflow 5: Season Trend Analysis
# =============================================================================


def workflow_season_trends():
    """Analyze how player performance changes over a season"""

    header("Workflow 5: Season Trend Analysis")

    info("Scenario: Tracking a player's scoring trend over 20 games")
    print()

    # Game-by-game points (simulating a season progression)
    game_points = [
        18,
        22,
        19,
        25,
        21,
        24,
        26,
        23,
        28,
        30,  # Early season
        27,
        31,
        29,
        33,
        28,
        32,
        30,
        34,
        31,
        35,  # Late season
    ]

    # Split into early and late season
    early_season = game_points[:10]
    late_season = game_points[10:]

    subheader("Early Season Performance (Games 1-10)")
    early_summary = stats_helper.calculate_summary_stats(early_season)

    metric("Mean PPG", f"{early_summary['mean']:.1f}")
    metric("Median PPG", f"{early_summary['median']:.1f}")
    metric("Std Dev", f"{early_summary['std_dev']:.1f}")
    metric("Range", f"{early_summary['range']}")

    subheader("Late Season Performance (Games 11-20)")
    late_summary = stats_helper.calculate_summary_stats(late_season)

    metric("Mean PPG", f"{late_summary['mean']:.1f}")
    metric("Median PPG", f"{late_summary['median']:.1f}")
    metric("Std Dev", f"{late_summary['std_dev']:.1f}")
    metric("Range", f"{late_summary['range']}")

    # Calculate improvement
    subheader("Season Progression Analysis")

    improvement = math_helper.subtract(late_summary["mean"], early_summary["mean"])
    improvement = math_helper.round_number(improvement, 1)

    improvement_pct = math_helper.divide(improvement, early_summary["mean"])
    improvement_pct = math_helper.multiply(improvement_pct, 100)
    improvement_pct = math_helper.round_number(improvement_pct, 1)

    metric("PPG Improvement", f"+{improvement:.1f}", "points")
    metric("Improvement %", f"+{improvement_pct:.1f}%")

    # Consistency analysis
    if late_summary["std_dev"] < early_summary["std_dev"]:
        consistency = "MORE consistent"
        cons_change = math_helper.subtract(
            early_summary["std_dev"], late_summary["std_dev"]
        )
    else:
        consistency = "LESS consistent"
        cons_change = math_helper.subtract(
            late_summary["std_dev"], early_summary["std_dev"]
        )

    print()
    print(f"  The player became {consistency} as the season progressed")
    print(f"  Std Dev changed by {cons_change:.1f} points")

    # Overall season stats
    subheader("Full Season Statistics")
    full_season = stats_helper.calculate_summary_stats(game_points)

    metric("Games Played", f"{full_season['count']}")
    metric("Season Average", f"{full_season['mean']:.1f}", "ppg")
    metric("Median Performance", f"{full_season['median']:.1f}", "ppg")
    metric("Best Game", f"{full_season['max']}", "points")
    metric("Worst Game", f"{full_season['min']}", "points")
    metric("Consistency (Std Dev)", f"{full_season['std_dev']:.1f}")

    # Trend assessment
    subheader("Trend Assessment")

    if improvement > 5:
        success("Strong upward trend - player is heating up!")
    elif improvement > 2:
        success("Moderate improvement - player is finding rhythm")
    elif improvement > -2:
        info("Stable performance throughout season")
    else:
        info("Declining performance - may need rest")

    print()


# =============================================================================
# Main Demo Runner
# =============================================================================


def main():
    """Run all workflow demonstrations"""

    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 80)
    print("  Sprint 5: NBA Analysis Workflow Demonstrations")
    print("  Using Math, Stats, and NBA Metrics Tools")
    print("=" * 80)
    print(f"{Colors.RESET}")

    print("\nThis demo showcases 5 real-world NBA analysis workflows:")
    print("  1. Player Efficiency Analysis - Evaluate individual player performance")
    print("  2. Team Performance Comparison - Compare multiple teams' efficiency")
    print("  3. Statistical Distribution Analysis - Analyze scoring distributions")
    print("  4. Shooting Efficiency Evaluation - Compare shooting metrics")
    print("  5. Season Trend Analysis - Track performance over time")
    print()

    input("Press Enter to start the demonstrations...")

    # Run all workflows
    workflow_player_efficiency()
    input("\nPress Enter to continue to next workflow...")

    workflow_team_comparison()
    input("\nPress Enter to continue to next workflow...")

    workflow_statistical_analysis()
    input("\nPress Enter to continue to next workflow...")

    workflow_shooting_efficiency()
    input("\nPress Enter to continue to next workflow...")

    workflow_season_trends()

    # Final summary
    header("Demo Complete!")

    print("You've seen how Sprint 5 tools enable:")
    print("  ✓ Player efficiency calculations (PER, TS%, eFG%)")
    print("  ✓ Team performance analysis (ORtg, DRtg, Net Rating)")
    print("  ✓ Statistical analysis (mean, median, std dev, quartiles)")
    print("  ✓ Shooting efficiency comparisons")
    print("  ✓ Trend analysis and season progression")
    print()
    print("All calculations use the 20 new Sprint 5 tools:")
    print("  • 7 Math tools (add, subtract, multiply, divide, etc.)")
    print("  • 6 Stats tools (mean, median, variance, summary, etc.)")
    print("  • 7 NBA tools (PER, TS%, eFG%, ORtg, DRtg, etc.)")
    print()
    success("Sprint 5 tools are production-ready for NBA analytics!")
    print()


if __name__ == "__main__":
    main()
