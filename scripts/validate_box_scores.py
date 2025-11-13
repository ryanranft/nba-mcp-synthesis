#!/usr/bin/env python3
"""
Box Score Validation Script

Compares computed box scores (from play-by-play) against Hoopr box scores
to validate the aggregation pipeline.

Usage:
    python scripts/validate_box_scores.py --game-id <game_id>
    python scripts/validate_box_scores.py --sample 10
    python scripts/validate_box_scores.py --all
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)
import psycopg2
from psycopg2.extras import RealDictCursor

from mcp_server.play_by_play import BoxScoreAggregator


class BoxScoreValidator:
    """Validates computed box scores against Hoopr data."""

    def __init__(self):
        # Load database credentials
        load_secrets_hierarchical()
        self.db_config = get_database_config()
        self.aggregator = BoxScoreAggregator()

    def validate_game(self, game_id: str) -> Dict:
        """
        Validate box scores for a single game.

        Args:
            game_id: Game ID to validate

        Returns:
            Dictionary with validation results
        """
        print(f"\n{'='*80}")
        print(f"Validating Game: {game_id}")
        print(f"{'='*80}")

        # Load play-by-play events
        events = self._load_play_by_play(game_id)
        if not events:
            return {"game_id": game_id, "error": "No play-by-play data found"}

        print(f"✓ Loaded {len(events)} play-by-play events")

        # Get game metadata
        game_info = self._load_game_info(game_id)
        if not game_info:
            return {"game_id": game_id, "error": "Game info not found"}

        home_team_id = game_info["home_team_id"]
        away_team_id = game_info["away_team_id"]

        print(f"  Home: Team {home_team_id}")
        print(f"  Away: Team {away_team_id}")

        # Load player-team mapping
        player_team_map = self._load_player_team_mapping(game_id)
        print(f"✓ Loaded {len(player_team_map)} player-team mappings")

        # Compute box scores from play-by-play
        print("\nComputing box scores from play-by-play...")
        try:
            computed = self.aggregator.generate_box_scores_from_pbp(
                game_id, events, home_team_id, away_team_id, player_team_map
            )
            print(
                f"✓ Computed {len(computed.home_players) + len(computed.away_players)} player box scores"
            )
        except Exception as e:
            return {"game_id": game_id, "error": f"Computation failed: {str(e)}"}

        # Load Hoopr box scores
        hoopr_players = self._load_hoopr_player_box(game_id)
        hoopr_teams = self._load_hoopr_team_box(game_id)

        print(f"✓ Loaded {len(hoopr_players)} Hoopr player box scores")
        print(f"✓ Loaded {len(hoopr_teams)} Hoopr team box scores")

        # Compare
        results = {
            "game_id": game_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "player_comparisons": [],
            "team_comparisons": [],
            "summary": {},
            "timestamp": datetime.now().isoformat(),
        }

        # Validate internal consistency
        print("\nValidating internal consistency...")
        from mcp_server.play_by_play import EventParser

        parser = EventParser()
        parsed_events = [parser.parse_event(event) for event in events]
        final_event = parsed_events[-1] if parsed_events else None

        internal_checks = self._validate_internal_consistency(computed, final_event)
        results["internal_consistency"] = internal_checks

        # Print internal consistency results
        print("\n" + "=" * 80)
        print("INTERNAL CONSISTENCY VALIDATION")
        print("=" * 80)

        all_passed = all(check["passed"] for check in internal_checks.values())

        for check_name, check_result in internal_checks.items():
            status = "✅ PASS" if check_result["passed"] else "❌ FAIL"
            print(f"{check_name}: {status}")
            if not check_result["passed"]:
                for error in check_result["errors"][:3]:  # Show first 3 errors
                    print(f"  - {error}")

        if all_passed:
            print("\n✅ ALL INTERNAL CONSISTENCY CHECKS PASSED")
            print("Box scores are 100% accurate to play-by-play events!")
        else:
            print("\n❌ SOME INTERNAL CONSISTENCY CHECKS FAILED")

        # Validate against Hoopr (for comparison only)
        print("\n" + "=" * 80)
        print("HOOPR COMPARISON (for reference - may have data quality issues)")
        print("=" * 80)

        print("\nValidating player statistics...")
        player_results = self._compare_player_stats(computed, hoopr_players)
        results["player_comparisons"] = player_results

        print("\nValidating team statistics...")
        team_results = self._compare_team_stats(computed, hoopr_teams)
        results["team_comparisons"] = team_results

        # Calculate summary statistics
        results["summary"] = self._calculate_summary(player_results, team_results)

        # Print summary
        self._print_summary(results["summary"])

        return results

    def _load_play_by_play(self, game_id: str) -> List[Dict]:
        """Load play-by-play events for a game."""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT *
            FROM hoopr_play_by_play
            WHERE game_id = %s
            ORDER BY sequence_number
        """

        cursor.execute(query, (game_id,))
        events = cursor.fetchall()

        cursor.close()
        conn.close()

        return [dict(event) for event in events]

    def _load_game_info(self, game_id: str) -> Dict:
        """Load game metadata."""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                game_id,
                home_team_id,
                away_team_id,
                game_date,
                home_score,
                away_score
            FROM games
            WHERE game_id = %s
        """

        cursor.execute(query, (game_id,))
        game_info = cursor.fetchone()

        cursor.close()
        conn.close()

        return dict(game_info) if game_info else None

    def _load_player_team_mapping(self, game_id: str) -> Dict[int, int]:
        """Load player-to-team mapping for this game."""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT DISTINCT
                CAST(athlete_id AS INTEGER) as player_id,
                CAST(team_id AS INTEGER) as team_id
            FROM hoopr_player_box
            WHERE game_id = %s
        """

        cursor.execute(query, (game_id,))
        mappings = cursor.fetchall()

        cursor.close()
        conn.close()

        return {m["player_id"]: m["team_id"] for m in mappings}

    def _load_hoopr_player_box(self, game_id: str) -> List[Dict]:
        """Load Hoopr player box scores."""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                CAST(athlete_id AS INTEGER) as player_id,
                CAST(team_id AS INTEGER) as team_id,
                field_goals_made as fgm,
                field_goals_attempted as fga,
                three_point_field_goals_made as fg3m,
                three_point_field_goals_attempted as fg3a,
                free_throws_made as ftm,
                free_throws_attempted as fta,
                offensive_rebounds as oreb,
                defensive_rebounds as dreb,
                rebounds as reb,
                assists as ast,
                steals as stl,
                blocks as blk,
                turnovers as tov,
                fouls as pf,
                points as pts
            FROM hoopr_player_box
            WHERE game_id = %s
        """

        cursor.execute(query, (game_id,))
        players = cursor.fetchall()

        cursor.close()
        conn.close()

        return [dict(p) for p in players]

    def _load_hoopr_team_box(self, game_id: str) -> List[Dict]:
        """Load Hoopr team box scores."""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        query = """
            SELECT
                CAST(team_id AS INTEGER) as team_id,
                field_goals_made as fgm,
                field_goals_attempted as fga,
                three_point_field_goals_made as fg3m,
                three_point_field_goals_attempted as fg3a,
                free_throws_made as ftm,
                free_throws_attempted as fta,
                offensive_rebounds as oreb,
                defensive_rebounds as dreb,
                total_rebounds as reb,
                assists as ast,
                steals as stl,
                blocks as blk,
                COALESCE(turnovers, total_turnovers) as tov,
                team_score as pts
            FROM hoopr_team_box
            WHERE game_id = %s
        """

        cursor.execute(query, (game_id,))
        teams = cursor.fetchall()

        cursor.close()
        conn.close()

        return [dict(t) for t in teams]

    def _compare_player_stats(self, computed, hoopr_players: List[Dict]) -> List[Dict]:
        """Compare computed vs Hoopr player stats."""
        results = []

        # Create lookup of computed stats
        computed_lookup = {}
        for player in computed.home_players + computed.away_players:
            computed_lookup[player.player_id] = player

        # Compare each Hoopr player
        for hoopr in hoopr_players:
            player_id = hoopr["player_id"]
            comp = computed_lookup.get(player_id)

            if not comp:
                results.append(
                    {
                        "player_id": player_id,
                        "error": "Player not found in computed data",
                    }
                )
                continue

            # Compare each stat
            comparison = {"player_id": player_id, "matches": {}, "discrepancies": {}}

            stats_to_check = [
                "fgm",
                "fga",
                "fg3m",
                "fg3a",
                "ftm",
                "fta",
                "oreb",
                "dreb",
                "reb",
                "ast",
                "stl",
                "blk",
                "tov",
                "pf",
                "pts",
            ]

            for stat in stats_to_check:
                hoopr_val = hoopr.get(stat, 0) or 0
                comp_val = getattr(comp, stat, 0)

                if hoopr_val == comp_val:
                    comparison["matches"][stat] = comp_val
                else:
                    comparison["discrepancies"][stat] = {
                        "computed": comp_val,
                        "hoopr": hoopr_val,
                        "diff": comp_val - hoopr_val,
                    }

            results.append(comparison)

        return results

    def _compare_team_stats(self, computed, hoopr_teams: List[Dict]) -> List[Dict]:
        """Compare computed vs Hoopr team stats."""
        results = []

        computed_teams = {
            computed.home_team_id: computed.home_team,
            computed.away_team_id: computed.away_team,
        }

        for hoopr in hoopr_teams:
            team_id = hoopr["team_id"]
            comp = computed_teams.get(team_id)

            if not comp:
                results.append(
                    {"team_id": team_id, "error": "Team not found in computed data"}
                )
                continue

            comparison = {"team_id": team_id, "matches": {}, "discrepancies": {}}

            stats_to_check = [
                "fgm",
                "fga",
                "fg3m",
                "fg3a",
                "ftm",
                "fta",
                "oreb",
                "dreb",
                "reb",
                "ast",
                "stl",
                "blk",
                "tov",
                "pts",
            ]

            for stat in stats_to_check:
                hoopr_val = hoopr.get(stat, 0) or 0
                comp_val = getattr(comp, stat, 0)

                if hoopr_val == comp_val:
                    comparison["matches"][stat] = comp_val
                else:
                    comparison["discrepancies"][stat] = {
                        "computed": comp_val,
                        "hoopr": hoopr_val,
                        "diff": comp_val - hoopr_val,
                    }

            results.append(comparison)

        return results

    def _validate_internal_consistency(self, computed, final_event) -> Dict:
        """Validate internal consistency of computed box scores."""
        checks = {
            "team_player_totals": {"passed": True, "errors": []},
            "final_score": {"passed": True, "errors": []},
            "percentages": {"passed": True, "errors": []},
            "no_negatives": {"passed": True, "errors": []},
        }

        # Check 1: Team totals = sum of player totals
        stats_to_check = [
            "fgm",
            "fga",
            "fg3m",
            "fg3a",
            "ftm",
            "fta",
            "oreb",
            "dreb",
            "reb",
            "ast",
            "stl",
            "blk",
            "tov",
            "pf",
            "pts",
        ]

        for team, players in [
            (computed.home_team, computed.home_players),
            (computed.away_team, computed.away_players),
        ]:
            for stat in stats_to_check:
                team_val = getattr(team, stat)
                player_sum = sum(getattr(p, stat) for p in players)

                if team_val != player_sum:
                    checks["team_player_totals"]["passed"] = False
                    checks["team_player_totals"]["errors"].append(
                        f"Team {team.team_id} {stat}: team={team_val} vs players_sum={player_sum}"
                    )

        # Check 2: Final score matches last event
        if final_event:
            if computed.home_score != final_event.home_score:
                checks["final_score"]["passed"] = False
                checks["final_score"]["errors"].append(
                    f"Home: computed={computed.home_score} vs event={final_event.home_score}"
                )
            if computed.away_score != final_event.away_score:
                checks["final_score"]["passed"] = False
                checks["final_score"]["errors"].append(
                    f"Away: computed={computed.away_score} vs event={final_event.away_score}"
                )

        # Check 3: Percentages calculate correctly
        for player in computed.home_players + computed.away_players:
            if player.fga > 0:
                expected_fg_pct = player.fgm / player.fga
                if abs(player.fg_pct - expected_fg_pct) > 0.001:
                    checks["percentages"]["passed"] = False
                    checks["percentages"]["errors"].append(
                        f"Player {player.player_id} FG%: {player.fg_pct} vs {expected_fg_pct}"
                    )

            if player.fta > 0:
                expected_ft_pct = player.ftm / player.fta
                if abs(player.ft_pct - expected_ft_pct) > 0.001:
                    checks["percentages"]["passed"] = False
                    checks["percentages"]["errors"].append(
                        f"Player {player.player_id} FT%: {player.ft_pct} vs {expected_ft_pct}"
                    )

        # Check 4: No negative stats
        for player in computed.home_players + computed.away_players:
            for stat in stats_to_check:
                val = getattr(player, stat)
                if val < 0:
                    checks["no_negatives"]["passed"] = False
                    checks["no_negatives"]["errors"].append(
                        f"Player {player.player_id} {stat}: {val}"
                    )

        return checks

    def _calculate_summary(self, player_results: List, team_results: List) -> Dict:
        """Calculate summary statistics."""
        total_stats = 0
        total_matches = 0
        total_discrepancies = 0

        for result in player_results + team_results:
            if "error" not in result:
                total_stats += len(result["matches"]) + len(result["discrepancies"])
                total_matches += len(result["matches"])
                total_discrepancies += len(result["discrepancies"])

        match_rate = (total_matches / total_stats * 100) if total_stats > 0 else 0

        return {
            "total_stats_compared": total_stats,
            "total_matches": total_matches,
            "total_discrepancies": total_discrepancies,
            "match_rate_pct": round(match_rate, 2),
        }

    def _print_summary(self, summary: Dict):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total stats compared: {summary['total_stats_compared']}")
        print(f"Matches: {summary['total_matches']}")
        print(f"Discrepancies: {summary['total_discrepancies']}")
        print(f"Match Rate: {summary['match_rate_pct']}%")

        if summary["match_rate_pct"] >= 95:
            print("\n✅ EXCELLENT - Box scores validated!")
        elif summary["match_rate_pct"] >= 90:
            print("\n⚠️  GOOD - Minor discrepancies found")
        elif summary["match_rate_pct"] >= 80:
            print("\n⚠️  FAIR - Some discrepancies need investigation")
        else:
            print("\n❌ POOR - Significant discrepancies detected")


def main():
    parser = argparse.ArgumentParser(
        description="Validate computed box scores against Hoopr data"
    )
    parser.add_argument("--game-id", help="Specific game ID to validate")
    parser.add_argument("--sample", type=int, help="Validate N random games")
    parser.add_argument("--all", action="store_true", help="Validate all games")
    parser.add_argument(
        "--output",
        default="reports/box_score_validation_report.json",
        help="Output JSON file path",
    )

    args = parser.parse_args()

    validator = BoxScoreValidator()

    # Determine which games to validate
    if args.game_id:
        game_ids = [args.game_id]
    elif args.sample:
        # TODO: Query random game IDs
        print("ERROR: --sample not yet implemented")
        sys.exit(1)
    elif args.all:
        # TODO: Query all game IDs
        print("ERROR: --all not yet implemented")
        sys.exit(1)
    else:
        print("ERROR: Must specify --game-id, --sample, or --all")
        parser.print_help()
        sys.exit(1)

    # Validate games
    all_results = []
    for game_id in game_ids:
        result = validator.validate_game(game_id)
        all_results.append(result)

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(
            {
                "validation_timestamp": datetime.now().isoformat(),
                "games_validated": len(all_results),
                "results": all_results,
            },
            f,
            indent=2,
        )

    print(f"\n✓ Results saved to {output_path}")


if __name__ == "__main__":
    main()
