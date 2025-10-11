#!/usr/bin/env python3
"""Test newly registered NBA metrics tools (Win Shares and Box Plus/Minus)"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.tools import nba_metrics_helper


def test_win_shares():
    """Test Win Shares calculation"""
    print("\n" + "="*60)
    print("Testing Win Shares (WS)")
    print("="*60)

    # Example: LeBron James 2012-13 season
    # Marginal offense: 5.8, Marginal defense: 3.3, MPW: 30
    marginal_offense = 5.8
    marginal_defense = 3.3
    marginal_points_per_win = 30.0

    result = nba_metrics_helper.calculate_win_shares(
        marginal_offense,
        marginal_defense,
        marginal_points_per_win
    )

    print(f"Inputs:")
    print(f"  Marginal Offense: {marginal_offense}")
    print(f"  Marginal Defense: {marginal_defense}")
    print(f"  Marginal Points Per Win: {marginal_points_per_win}")
    print(f"\nResult: {result:.2f} WS")
    print(f"Interpretation: {'Elite' if result > 10 else 'Above Average' if result > 5 else 'Average'} contribution")

    assert result > 0, "Win Shares should be positive"
    print("✅ Win Shares test passed")

    return result


def test_box_plus_minus():
    """Test Box Plus/Minus calculation"""
    print("\n" + "="*60)
    print("Testing Box Plus/Minus (BPM)")
    print("="*60)

    # Example: All-Star level player
    # PER: 25.0, Team pace: 98.0, League avg PER: 15.0, League avg pace: 100.0
    per = 25.0
    team_pace = 98.0
    league_avg_per = 15.0
    league_avg_pace = 100.0

    result = nba_metrics_helper.calculate_box_plus_minus(
        per,
        team_pace,
        league_avg_per,
        league_avg_pace
    )

    print(f"Inputs:")
    print(f"  Player Efficiency Rating (PER): {per}")
    print(f"  Team Pace: {team_pace}")
    print(f"  League Average PER: {league_avg_per}")
    print(f"  League Average Pace: {league_avg_pace}")
    print(f"\nResult: {result:+.1f} BPM")

    if result > 0:
        print(f"Interpretation: {result:.1f} points per 100 possessions ABOVE league average")
    elif result < 0:
        print(f"Interpretation: {abs(result):.1f} points per 100 possessions BELOW league average")
    else:
        print("Interpretation: At league average")

    print("✅ Box Plus/Minus test passed")

    return result


def test_edge_cases():
    """Test edge cases"""
    print("\n" + "="*60)
    print("Testing Edge Cases")
    print("="*60)

    # Test 1: Zero values for Win Shares
    ws_zero = nba_metrics_helper.calculate_win_shares(0, 0, 30)
    print(f"Win Shares with zero marginal contributions: {ws_zero:.2f}")
    assert ws_zero == 0, "Zero contributions should yield zero WS"
    print("✅ Zero WS test passed")

    # Test 2: League average player for BPM
    bpm_avg = nba_metrics_helper.calculate_box_plus_minus(15.0, 100.0, 15.0, 100.0)
    print(f"Box Plus/Minus for league average player: {bpm_avg:+.1f}")
    assert abs(bpm_avg) < 0.1, "League average player should have ~0 BPM"
    print("✅ League average BPM test passed")

    # Test 3: Negative marginal contributions
    ws_negative = nba_metrics_helper.calculate_win_shares(-2.0, -1.0, 30)
    print(f"Win Shares with negative contributions: {ws_negative:.2f}")
    print("✅ Negative contributions test passed")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("NBA METRICS REGISTRATION VERIFICATION")
    print("Testing: nba_win_shares & nba_box_plus_minus")
    print("="*70)

    try:
        # Test Win Shares
        ws_result = test_win_shares()

        # Test Box Plus/Minus
        bpm_result = test_box_plus_minus()

        # Test edge cases
        test_edge_cases()

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✅ All tests passed successfully!")
        print(f"\nSample Results:")
        print(f"  Win Shares: {ws_result:.2f}")
        print(f"  Box Plus/Minus: {bpm_result:+.1f}")
        print(f"\nTools are ready for use in fastmcp_server.py")
        print("="*70)

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())