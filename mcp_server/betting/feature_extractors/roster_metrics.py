"""
Roster Quality Metrics for NBA Betting

Provides advanced roster evaluation metrics including PER, usage rates,
depth scores, and team composition analysis.

These metrics help quantify team quality beyond simple win-loss records.

Example Usage:
-------------
    from mcp_server.betting.feature_extractors.roster_metrics import RosterMetrics

    metrics = RosterMetrics()

    # Calculate PER for a player's recent games
    per = metrics.calculate_per(
        points=25, rebounds=8, assists=6, steals=2, blocks=1,
        turnovers=3, fgm=10, fga=20, ftm=4, fta=5, minutes=35
    )

    # Depth score for a team
    depth = metrics.calculate_depth_score(roster_stats)
"""

from typing import Dict, List, Optional
import numpy as np


class RosterMetrics:
    """
    Calculate advanced roster quality metrics
    """

    def __init__(self):
        """Initialize roster metrics calculator"""
        # League average constants (can be updated seasonally)
        self.league_avg_pace = 100.0  # Possessions per 48 minutes
        self.league_avg_offensive_rating = 112.0  # Points per 100 possessions

    def calculate_per(
        self,
        points: float,
        rebounds: float,
        assists: float,
        steals: float,
        blocks: float,
        turnovers: float,
        fgm: float,
        fga: float,
        ftm: float,
        fta: float,
        minutes: float,
        team_pace: Optional[float] = None,
    ) -> float:
        """
        Calculate Player Efficiency Rating (PER)

        Simplified PER formula:
        PER = (points + rebounds + assists + steals + blocks
               - missed_shots - turnovers) / minutes * 48

        More accurate formula accounts for team pace, but requires additional data.

        Args:
            points: Points scored
            rebounds: Total rebounds
            assists: Assists
            steals: Steals
            blocks: Blocks
            turnovers: Turnovers
            fgm: Field goals made
            fga: Field goals attempted
            ftm: Free throws made
            fta: Free throws attempted
            minutes: Minutes played
            team_pace: Team pace (possessions per 48 min), optional

        Returns:
            PER score (league average is ~15)
        """
        if minutes <= 0:
            return 0.0

        # Missed shots penalty
        missed_fg = fga - fgm
        missed_ft = fta - ftm

        # Basic PER calculation
        positive_actions = points + rebounds + assists + steals + blocks
        negative_actions = (
            turnovers + missed_fg + (0.44 * missed_ft)
        )  # FT misses weighted less

        # Normalize to per-48-minutes
        per = (positive_actions - negative_actions) / minutes * 48

        # Adjust for pace if provided
        if team_pace:
            pace_adjustment = team_pace / self.league_avg_pace
            per = per * pace_adjustment

        return float(per)

    def calculate_usage_rate(
        self,
        fga: float,
        fta: float,
        turnovers: float,
        minutes: float,
        team_minutes: float = 240.0,  # 5 players * 48 minutes
        team_fga: Optional[float] = None,
        team_fta: Optional[float] = None,
        team_turnovers: Optional[float] = None,
    ) -> float:
        """
        Calculate Usage Rate

        Usage Rate = 100 * ((FGA + 0.44 * FTA + TOV) * (Team Minutes / 5))
                     / (Minutes * (Team FGA + 0.44 * Team FTA + Team TOV))

        Approximation when team stats unavailable:
        Usage Rate ≈ (FGA + 0.44 * FTA + TOV) / Minutes * 100

        Args:
            fga: Player's field goal attempts
            fta: Player's free throw attempts
            turnovers: Player's turnovers
            minutes: Player's minutes played
            team_minutes: Total team minutes (default 240 = 5 * 48)
            team_fga: Team's total FGA (optional)
            team_fta: Team's total FTA (optional)
            team_turnovers: Team's total turnovers (optional)

        Returns:
            Usage rate percentage (league average is ~20%)
        """
        if minutes <= 0:
            return 0.0

        # Player possessions used
        player_poss_used = fga + (0.44 * fta) + turnovers

        # If team stats provided, use full formula
        if team_fga is not None and team_fta is not None and team_turnovers is not None:
            team_poss = team_fga + (0.44 * team_fta) + team_turnovers
            if team_poss > 0:
                usage_rate = (
                    100
                    * (player_poss_used * (team_minutes / 5))
                    / (minutes * team_poss)
                )
                return float(usage_rate)

        # Approximation when team stats unavailable
        usage_rate = (player_poss_used / minutes) * 100

        return float(usage_rate)

    def calculate_true_shooting_pct(
        self, points: float, fga: float, fta: float
    ) -> float:
        """
        Calculate True Shooting Percentage

        TS% = Points / (2 * (FGA + 0.44 * FTA))

        Accounts for the value of 3-pointers and free throws.
        League average is ~56-57%.

        Args:
            points: Points scored
            fga: Field goal attempts
            fta: Free throw attempts

        Returns:
            True shooting percentage (0.0 to 1.0, or >1.0 in rare cases)
        """
        denominator = 2 * (fga + (0.44 * fta))

        if denominator <= 0:
            return 0.0

        ts_pct = points / denominator

        return float(ts_pct)

    def calculate_depth_score(self, player_ppg_list: List[float]) -> float:
        """
        Calculate team depth score

        Measures how evenly distributed scoring is across the roster.
        Higher score = better depth (less reliance on stars).

        Method: Coefficient of variation of PPG for players 1-10
        Lower CV = more balanced scoring = better depth

        Args:
            player_ppg_list: List of PPG for team's players (sorted desc)

        Returns:
            Depth score (0-100, higher is better)
        """
        if not player_ppg_list or len(player_ppg_list) < 5:
            return 0.0

        # Take top 10 players (or fewer if roster is smaller)
        top_players = player_ppg_list[: min(10, len(player_ppg_list))]

        # Calculate coefficient of variation
        mean_ppg = np.mean(top_players)
        std_ppg = np.std(top_players)

        if mean_ppg <= 0:
            return 0.0

        cv = std_ppg / mean_ppg

        # Convert to depth score (lower CV = higher depth)
        # CV typically ranges from 0.3 (very balanced) to 1.0 (very top-heavy)
        # Scale to 0-100
        depth_score = max(0, 100 * (1 - cv))

        return float(depth_score)

    def calculate_roster_strength_index(
        self,
        top_players_per: List[float],
        depth_score: float,
        star_weight: float = 0.7,
        depth_weight: float = 0.3,
    ) -> float:
        """
        Calculate overall roster strength index

        Combines star power (sum of PER for top players) with depth.

        Args:
            top_players_per: List of PER for top 5 players
            depth_score: Team depth score (0-100)
            star_weight: Weight for star power (default 0.7)
            depth_weight: Weight for depth (default 0.3)

        Returns:
            Roster strength index (0-100+)
        """
        # Normalize star power (sum of top 5 PER, typical range 50-100)
        star_power = sum(top_players_per[:5]) if top_players_per else 0
        normalized_star_power = min(100, star_power)  # Cap at 100

        # Weighted combination
        roster_index = (star_weight * normalized_star_power) + (
            depth_weight * depth_score
        )

        return float(roster_index)

    def calculate_offensive_rating(
        self, points_scored: float, possessions: float
    ) -> float:
        """
        Calculate Offensive Rating

        ORtg = (Points / Possessions) * 100

        Estimates points scored per 100 possessions.
        League average is ~112.

        Args:
            points_scored: Total points scored
            possessions: Number of possessions (can estimate from FGA, TOV, FTA)

        Returns:
            Offensive rating
        """
        if possessions <= 0:
            return 0.0

        ortg = (points_scored / possessions) * 100

        return float(ortg)

    def calculate_defensive_rating(
        self, points_allowed: float, possessions: float
    ) -> float:
        """
        Calculate Defensive Rating

        DRtg = (Points Allowed / Possessions) * 100

        Estimates points allowed per 100 possessions.
        League average is ~112. Lower is better.

        Args:
            points_allowed: Total points allowed
            possessions: Number of defensive possessions

        Returns:
            Defensive rating
        """
        if possessions <= 0:
            return 0.0

        drtg = (points_allowed / possessions) * 100

        return float(drtg)

    def estimate_possessions(
        self, fga: float, orb: float, turnovers: float, fta: float
    ) -> float:
        """
        Estimate number of possessions

        Possessions ≈ FGA + 0.44 * FTA - ORB + TOV

        Args:
            fga: Field goal attempts
            orb: Offensive rebounds
            turnovers: Turnovers
            fta: Free throw attempts

        Returns:
            Estimated possessions
        """
        possessions = fga + (0.44 * fta) - orb + turnovers

        return max(0, float(possessions))

    def calculate_net_rating(
        self, offensive_rating: float, defensive_rating: float
    ) -> float:
        """
        Calculate Net Rating

        NetRtg = ORtg - DRtg

        Positive means team scores more than it allows per 100 possessions.

        Args:
            offensive_rating: Offensive rating
            defensive_rating: Defensive rating

        Returns:
            Net rating (can be positive or negative)
        """
        return float(offensive_rating - defensive_rating)

    def classify_player_role(
        self, ppg: float, usage_rate: float, minutes: float
    ) -> str:
        """
        Classify player role based on stats

        Args:
            ppg: Points per game
            usage_rate: Usage rate percentage
            minutes: Minutes per game

        Returns:
            Role classification: 'star', 'starter', 'role_player', 'bench'
        """
        if ppg >= 20 and usage_rate >= 25 and minutes >= 30:
            return "star"
        elif ppg >= 12 and minutes >= 25:
            return "starter"
        elif minutes >= 15:
            return "role_player"
        else:
            return "bench"

    def calculate_injury_adjusted_rating(
        self,
        base_rating: float,
        missing_players_contribution_pct: float,
        adjustment_factor: float = 0.8,
    ) -> float:
        """
        Adjust team rating for missing players

        Args:
            base_rating: Base team rating when healthy
            missing_players_contribution_pct: % of team output from injured players (0-1)
            adjustment_factor: How much missing players affects team (0.8 = 80% impact)

        Returns:
            Injury-adjusted rating
        """
        # Reduce rating proportional to missing contribution
        adjustment = base_rating * missing_players_contribution_pct * adjustment_factor
        adjusted_rating = base_rating - adjustment

        return float(max(0, adjusted_rating))
