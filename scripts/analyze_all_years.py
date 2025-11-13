#!/usr/bin/env python3
"""
Year-Over-Year Data Quality Analysis

Analyzes play-by-play data quality across all years to identify which seasons
have reliable data vs systematic errors. Creates ML-ready metadata flags.

Usage:
    python scripts/analyze_all_years.py --sample-size 10
    python scripts/analyze_all_years.py --years 2020-2024 --sample-size 5
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import (
    load_secrets_hierarchical,
    get_database_config,
)
import psycopg2
from psycopg2.extras import RealDictCursor
from mcp_server.play_by_play import BoxScoreAggregator, EventParser


class YearOverYearAnalyzer:
    """Analyzes data quality across all years."""

    def __init__(self, sample_size=10):
        load_secrets_hierarchical()
        self.db_config = get_database_config()
        self.sample_size = sample_size
        self.aggregator = BoxScoreAggregator()
        self.parser = EventParser()

    def get_available_years(self) -> List[int]:
        """Get all years with play-by-play data."""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        query = """
            SELECT DISTINCT EXTRACT(YEAR FROM g.game_date)::INTEGER as year
            FROM hoopr_play_by_play pbp
            JOIN games g ON CAST(pbp.game_id AS TEXT) = g.game_id
            WHERE g.game_date IS NOT NULL
            ORDER BY year
        """

        cursor.execute(query)
        years = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return years

    def sample_games_for_year(self, year: int) -> List[str]:
        """Sample representative games from a year."""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        # Get all games with play-by-play for this year
        query = """
            WITH year_games AS (
                SELECT DISTINCT
                    pbp.game_id,
                    g.game_date,
                    g.home_team_id,
                    EXTRACT(DOY FROM g.game_date) as day_of_year
                FROM hoopr_play_by_play pbp
                JOIN games g ON CAST(pbp.game_id AS TEXT) = g.game_id
                WHERE EXTRACT(YEAR FROM g.game_date) = %s
            ),
            ranked_games AS (
                SELECT
                    game_id,
                    CASE
                        WHEN day_of_year < 100 THEN 'early'
                        WHEN day_of_year < 200 THEN 'mid'
                        ELSE 'late'
                    END as season_phase,
                    ROW_NUMBER() OVER (
                        PARTITION BY
                            CASE
                                WHEN day_of_year < 100 THEN 'early'
                                WHEN day_of_year < 200 THEN 'mid'
                                ELSE 'late'
                            END
                        ORDER BY RANDOM()
                    ) as rn
                FROM year_games
            )
            SELECT CAST(game_id AS TEXT) as game_id
            FROM ranked_games
            WHERE (season_phase = 'early' AND rn <= 3)
               OR (season_phase = 'mid' AND rn <= 4)
               OR (season_phase = 'late' AND rn <= 3)
            ORDER BY RANDOM()
            LIMIT %s
        """

        cursor.execute(query, (year, self.sample_size))
        game_ids = [str(row[0]) for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return game_ids

    def validate_game_quick(self, game_id: str) -> Dict:
        """Quick validation of a single game (internal consistency only)."""
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Load play-by-play
        cursor.execute(
            """
            SELECT * FROM hoopr_play_by_play
            WHERE game_id = %s
            ORDER BY sequence_number
        """,
            (game_id,),
        )
        events = [dict(e) for e in cursor.fetchall()]

        if not events:
            cursor.close()
            conn.close()
            return {"error": "No play-by-play data"}

        # Get game info
        cursor.execute(
            """
            SELECT game_id, home_team_id, away_team_id, game_date
            FROM games WHERE game_id = %s
        """,
            (game_id,),
        )
        game_info = cursor.fetchone()

        if not game_info:
            cursor.close()
            conn.close()
            return {"error": "No game info"}

        # Get player-team mapping
        cursor.execute(
            """
            SELECT DISTINCT
                CAST(athlete_id AS INTEGER) as player_id,
                CAST(team_id AS INTEGER) as team_id
            FROM hoopr_player_box
            WHERE game_id = %s
        """,
            (game_id,),
        )
        player_team_map = {m["player_id"]: m["team_id"] for m in cursor.fetchall()}

        # Load Hoopr box scores for comparison
        cursor.execute(
            """
            SELECT
                CAST(athlete_id AS INTEGER) as player_id,
                field_goals_attempted as fga,
                field_goals_made as fgm,
                points as pts
            FROM hoopr_player_box
            WHERE game_id = %s
        """,
            (game_id,),
        )
        hoopr_players = [dict(p) for p in cursor.fetchall()]

        cursor.close()
        conn.close()

        # Compute box scores
        try:
            computed = self.aggregator.generate_box_scores_from_pbp(
                game_id=game_id,
                events=events,
                home_team_id=game_info["home_team_id"],
                away_team_id=game_info["away_team_id"],
                player_team_mapping=player_team_map,
            )

            # Quick internal consistency check
            parsed_events = [self.parser.parse_event(e) for e in events]
            final_event = parsed_events[-1] if parsed_events else None

            internal_ok = True
            if final_event:
                if computed.home_score != final_event.home_score:
                    internal_ok = False
                if computed.away_score != final_event.away_score:
                    internal_ok = False

            # Quick Hoopr comparison (FGA/FGM/PTS only for speed)
            computed_lookup = {
                p.player_id: p for p in computed.home_players + computed.away_players
            }

            matches = 0
            total = 0
            discrepancies_by_stat = defaultdict(list)

            for hoopr in hoopr_players:
                pid = hoopr["player_id"]
                comp = computed_lookup.get(pid)
                if not comp:
                    continue

                for stat in ["fga", "fgm", "pts"]:
                    total += 1
                    h_val = hoopr.get(stat, 0) or 0
                    c_val = getattr(comp, stat, 0)

                    if h_val == c_val:
                        matches += 1
                    else:
                        discrepancies_by_stat[stat].append(c_val - h_val)

            match_rate = (matches / total * 100) if total > 0 else 0

            return {
                "game_id": game_id,
                "game_date": str(game_info["game_date"]),
                "num_events": len(events),
                "internal_consistent": internal_ok,
                "hoopr_match_rate": round(match_rate, 2),
                "stats_compared": total,
                "discrepancies": {
                    stat: {
                        "count": len(diffs),
                        "mean_diff": sum(diffs) / len(diffs) if diffs else 0,
                    }
                    for stat, diffs in discrepancies_by_stat.items()
                },
            }

        except Exception as e:
            return {"error": str(e)}

    def analyze_year(self, year: int) -> Dict:
        """Analyze data quality for a specific year."""
        print(f"\nAnalyzing year {year}...")

        game_ids = self.sample_games_for_year(year)
        print(f"  Sampled {len(game_ids)} games")

        if not game_ids:
            return {"year": year, "error": "No games with play-by-play data"}

        results = []
        for i, game_id in enumerate(game_ids, 1):
            print(f"  Validating game {i}/{len(game_ids)}: {game_id}", end="\r")
            result = self.validate_game_quick(game_id)
            results.append(result)

        print()  # New line after progress

        # Calculate year-level metrics
        valid_results = [r for r in results if "error" not in r]

        if not valid_results:
            return {"year": year, "error": "All validations failed"}

        match_rates = [r["hoopr_match_rate"] for r in valid_results]
        internal_checks = [r["internal_consistent"] for r in valid_results]

        # Aggregate discrepancies
        all_discrepancies = defaultdict(list)
        for r in valid_results:
            for stat, data in r.get("discrepancies", {}).items():
                all_discrepancies[stat].append(data["mean_diff"])

        year_summary = {
            "year": year,
            "games_sampled": len(game_ids),
            "games_validated": len(valid_results),
            "internal_consistency_rate": sum(internal_checks)
            / len(internal_checks)
            * 100,
            "mean_match_rate": sum(match_rates) / len(match_rates),
            "min_match_rate": min(match_rates),
            "max_match_rate": max(match_rates),
            "games_above_95": sum(1 for r in match_rates if r >= 95),
            "games_above_90": sum(1 for r in match_rates if r >= 90),
            "games_below_85": sum(1 for r in match_rates if r < 85),
            "common_discrepancies": {
                stat: {
                    "frequency": len(diffs),
                    "mean_diff": sum(diffs) / len(diffs) if diffs else 0,
                }
                for stat, diffs in all_discrepancies.items()
            },
            "game_results": results,
        }

        return year_summary

    def calculate_quality_score(self, year_data: Dict) -> int:
        """Calculate composite quality score (0-100)."""
        if "error" in year_data:
            return 0

        score = 0

        # 40 points: Internal consistency
        internal_rate = year_data.get("internal_consistency_rate", 0)
        score += (internal_rate / 100) * 40

        # 30 points: Hoopr match rate
        match_rate = year_data.get("mean_match_rate", 0)
        score += (match_rate / 100) * 30

        # 20 points: Error pattern penalty
        num_error_types = len(year_data.get("common_discrepancies", {}))
        error_penalty = min(num_error_types * 2, 20)
        score += 20 - error_penalty

        # 10 points: Consistency across games
        min_rate = year_data.get("min_match_rate", 0)
        max_rate = year_data.get("max_match_rate", 100)
        consistency = 100 - (max_rate - min_rate)
        score += (consistency / 100) * 10

        return int(score)

    def classify_tier(self, quality_score: int) -> str:
        """Classify year into quality tier."""
        if quality_score >= 95:
            return "A"
        elif quality_score >= 85:
            return "B"
        elif quality_score >= 70:
            return "C"
        else:
            return "D"


def main():
    parser = argparse.ArgumentParser(
        description="Analyze play-by-play data quality year-over-year"
    )
    parser.add_argument(
        "--sample-size", type=int, default=10, help="Number of games to sample per year"
    )
    parser.add_argument("--years", help="Year range (e.g., 2020-2024) or single year")
    parser.add_argument(
        "--output",
        default="reports/year_over_year_data_quality.json",
        help="Output JSON file path",
    )

    args = parser.parse_args()

    analyzer = YearOverYearAnalyzer(sample_size=args.sample_size)

    # Determine which years to analyze
    if args.years:
        if "-" in args.years:
            start, end = map(int, args.years.split("-"))
            years = list(range(start, end + 1))
        else:
            years = [int(args.years)]
    else:
        years = analyzer.get_available_years()

    print(f"Analyzing {len(years)} years: {years[0]}-{years[-1]}")
    print(f"Sample size: {args.sample_size} games per year")

    # Analyze each year
    all_results = {}
    for year in years:
        year_data = analyzer.analyze_year(year)
        year_data["quality_score"] = analyzer.calculate_quality_score(year_data)
        year_data["tier"] = analyzer.classify_tier(year_data["quality_score"])
        all_results[str(year)] = year_data

    # Generate summary
    tiers = defaultdict(list)
    for year, data in all_results.items():
        if "tier" in data:
            tiers[data["tier"]].append(int(year))

    summary = {
        "analysis_timestamp": datetime.now().isoformat(),
        "years_analyzed": len(years),
        "sample_size_per_year": args.sample_size,
        "tier_summary": {
            "tier_a_years": sorted(tiers["A"]),
            "tier_b_years": sorted(tiers["B"]),
            "tier_c_years": sorted(tiers["C"]),
            "tier_d_years": sorted(tiers["D"]),
        },
        "by_year": all_results,
    }

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved to: {output_path}")
    print(f"\nTier Summary:")
    print(f"  Tier A (Excellent): {len(tiers['A'])} years - {tiers['A']}")
    print(f"  Tier B (Good):      {len(tiers['B'])} years - {tiers['B']}")
    print(f"  Tier C (Fair):      {len(tiers['C'])} years - {tiers['C']}")
    print(f"  Tier D (Poor):      {len(tiers['D'])} years - {tiers['D']}")


if __name__ == "__main__":
    main()
