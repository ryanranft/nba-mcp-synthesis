"""
Odds Utilities Module

Provides essential tools for working with betting odds:
1. Odds format conversion (American, Decimal, Fractional, Implied Probability)
2. Vig removal (devigging) to get fair market probabilities
3. Edge calculation
4. Fair odds computation

Key Problem:
-----------
Bookmakers don't offer fair odds. They add "vig" (vigorish/juice) to ensure profit.

Example:
    Fair coin flip should be:
        Heads: 2.00 decimal odds (50% implied)
        Tails: 2.00 decimal odds (50% implied)
        Total: 100%

    Bookmaker offers:
        Heads: 1.91 decimal odds (52.4% implied)
        Tails: 1.91 decimal odds (52.4% implied)
        Total: 104.8% (4.8% vig!)

To use Kelly Criterion correctly, you must remove vig to get the true market probability,
then compare against your calibrated probability.

Edge Calculation:
----------------
    edge = P_calibrated - P_market_fair

    If edge > 0: You have an advantage
    If edge < 0: Market disagrees (dangerous!)

Example Usage:
-------------
    from mcp_server.betting.odds_utilities import OddsUtilities

    # Remove vig
    home_fair, away_fair = OddsUtilities.remove_vig_multiplicative(
        home_odds=1.50,  # Decimal
        away_odds=2.80
    )

    # Calculate edge
    your_prob = 0.85  # From calibrated simulation
    edge = your_prob - home_fair

    if edge > 0.03:  # At least 3% edge
        print(f"Bet! Edge: {edge:.1%}")
"""

from typing import Tuple, Optional, Dict, Any
import numpy as np
from enum import Enum


class OddsFormat(Enum):
    """Supported odds formats"""
    AMERICAN = "american"      # e.g., -110, +150
    DECIMAL = "decimal"         # e.g., 1.91, 2.50
    FRACTIONAL = "fractional"   # e.g., 10/11, 3/2
    IMPLIED = "implied"         # e.g., 0.524 (52.4%)


class VigRemovalMethod(Enum):
    """Methods for removing vig from odds"""
    MULTIPLICATIVE = "multiplicative"  # Most accurate (assumes proportional margin)
    ADDITIVE = "additive"              # Simple subtraction
    POWER = "power"                    # Power method (for extreme vig)


class OddsUtilities:
    """Collection of odds conversion and manipulation utilities"""

    # -------------------------------------------------------------------------
    # Odds Format Conversions
    # -------------------------------------------------------------------------

    @staticmethod
    def american_to_decimal(american_odds: float) -> float:
        """
        Convert American odds to Decimal

        Args:
            american_odds: American format (negative for favorite, positive for underdog)
                          e.g., -110, +150

        Returns:
            Decimal odds (e.g., 1.91, 2.50)

        Examples:
            -110 → 1.91
            +150 → 2.50
            -200 → 1.50
        """
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1

    @staticmethod
    def decimal_to_american(decimal_odds: float) -> float:
        """
        Convert Decimal odds to American

        Args:
            decimal_odds: Decimal format (e.g., 1.91, 2.50)

        Returns:
            American odds (e.g., -110, +150)
        """
        if decimal_odds >= 2.0:
            return (decimal_odds - 1) * 100
        else:
            return -100 / (decimal_odds - 1)

    @staticmethod
    def decimal_to_implied_probability(decimal_odds: float) -> float:
        """
        Convert decimal odds to implied probability

        Args:
            decimal_odds: Decimal format (e.g., 2.00)

        Returns:
            Implied probability (0 to 1)

        Example:
            2.00 → 0.50 (50%)
            1.50 → 0.667 (66.7%)
        """
        return 1 / decimal_odds

    @staticmethod
    def implied_probability_to_decimal(prob: float) -> float:
        """Convert probability to decimal odds"""
        if prob <= 0 or prob >= 1:
            raise ValueError("Probability must be between 0 and 1")
        return 1 / prob

    @staticmethod
    def american_to_implied_probability(american_odds: float) -> float:
        """Convert American odds directly to implied probability"""
        decimal = OddsUtilities.american_to_decimal(american_odds)
        return OddsUtilities.decimal_to_implied_probability(decimal)

    # -------------------------------------------------------------------------
    # Vig Removal (Critical for Kelly Criterion)
    # -------------------------------------------------------------------------

    @staticmethod
    def remove_vig_multiplicative(
        home_odds: float,
        away_odds: float,
    ) -> Tuple[float, float]:
        """
        Remove vig using multiplicative method (RECOMMENDED)

        This is the most accurate method, assuming bookmakers apply proportional margin.

        Algorithm:
            1. Convert odds to implied probabilities
            2. Sum probabilities (will be > 1.0 due to vig)
            3. Normalize by dividing each by the sum

        Args:
            home_odds: Decimal odds for home team
            away_odds: Decimal odds for away team

        Returns:
            (home_fair_prob, away_fair_prob) - Fair probabilities summing to 1.0

        Example:
            Home: 1.91 (52.4% implied)
            Away: 1.91 (52.4% implied)
            Sum: 104.8% (4.8% vig)

            Fair home: 52.4% / 104.8% = 50.0%
            Fair away: 52.4% / 104.8% = 50.0%
        """
        # Implied probabilities (biased)
        p_home_raw = 1 / home_odds
        p_away_raw = 1 / away_odds

        # Total probability (overround)
        total = p_home_raw + p_away_raw

        # Normalize to remove vig
        p_home_fair = p_home_raw / total
        p_away_fair = p_away_raw / total

        return p_home_fair, p_away_fair

    @staticmethod
    def remove_vig_additive(
        home_odds: float,
        away_odds: float,
    ) -> Tuple[float, float]:
        """
        Remove vig using additive method

        Simple but less accurate than multiplicative.
        Subtracts half the overround from each probability.

        Args:
            home_odds: Decimal odds for home team
            away_odds: Decimal odds for away team

        Returns:
            (home_fair_prob, away_fair_prob)
        """
        p_home_raw = 1 / home_odds
        p_away_raw = 1 / away_odds

        # Calculate vig
        vig = (p_home_raw + p_away_raw) - 1.0

        # Subtract half vig from each
        p_home_fair = p_home_raw - (vig / 2)
        p_away_fair = p_away_raw - (vig / 2)

        return p_home_fair, p_away_fair

    @staticmethod
    def remove_vig_power(
        home_odds: float,
        away_odds: float,
        k: float = 1.0,
    ) -> Tuple[float, float]:
        """
        Remove vig using power method (Shin method)

        More sophisticated, handles extreme vig better.
        Uses power adjustment: p_fair = p^k / sum(p^k)

        Args:
            home_odds: Decimal odds for home team
            away_odds: Decimal odds for away team
            k: Power parameter (1.0 = multiplicative, higher = more aggressive)

        Returns:
            (home_fair_prob, away_fair_prob)
        """
        p_home_raw = 1 / home_odds
        p_away_raw = 1 / away_odds

        # Power transformation
        p_home_power = p_home_raw ** k
        p_away_power = p_away_raw ** k

        # Normalize
        total = p_home_power + p_away_power
        p_home_fair = p_home_power / total
        p_away_fair = p_away_power / total

        return p_home_fair, p_away_fair

    @staticmethod
    def calculate_vig_percentage(home_odds: float, away_odds: float) -> float:
        """
        Calculate the vig percentage (overround)

        Args:
            home_odds: Decimal odds for home team
            away_odds: Decimal odds for away team

        Returns:
            Vig percentage (e.g., 0.048 for 4.8% vig)
        """
        p_home = 1 / home_odds
        p_away = 1 / away_odds
        return (p_home + p_away) - 1.0

    # -------------------------------------------------------------------------
    # Edge Calculation
    # -------------------------------------------------------------------------

    @staticmethod
    def calculate_edge(
        your_probability: float,
        market_odds: float,
        away_odds: Optional[float] = None,
        vig_method: VigRemovalMethod = VigRemovalMethod.MULTIPLICATIVE,
    ) -> float:
        """
        Calculate your edge over the market

        Edge = Your probability - Market fair probability

        Positive edge = you have an advantage
        Negative edge = market disagrees (dangerous!)

        Args:
            your_probability: Your calibrated win probability (0 to 1)
            market_odds: Market decimal odds for the outcome
            away_odds: Optional away odds for vig removal (recommended)
            vig_method: Method to remove vig

        Returns:
            Edge as decimal (e.g., 0.05 = 5% edge)

        Example:
            your_prob = 0.85  # 85% from calibrated simulation
            market_odds = 1.50  # Bookmaker offers 1.50
            away_odds = 2.80

            edge = calculate_edge(0.85, 1.50, 2.80)
            # Returns: ~0.19 (19% edge)
        """
        if away_odds is not None:
            # Remove vig for more accurate edge
            if vig_method == VigRemovalMethod.MULTIPLICATIVE:
                market_fair_prob, _ = OddsUtilities.remove_vig_multiplicative(market_odds, away_odds)
            elif vig_method == VigRemovalMethod.ADDITIVE:
                market_fair_prob, _ = OddsUtilities.remove_vig_additive(market_odds, away_odds)
            elif vig_method == VigRemovalMethod.POWER:
                market_fair_prob, _ = OddsUtilities.remove_vig_power(market_odds, away_odds)
            else:
                market_fair_prob = 1 / market_odds
        else:
            # No vig removal (less accurate)
            market_fair_prob = 1 / market_odds

        edge = your_probability - market_fair_prob
        return edge

    @staticmethod
    def fair_odds(probability: float) -> float:
        """
        Calculate fair decimal odds for a given probability

        Args:
            probability: Win probability (0 to 1)

        Returns:
            Fair decimal odds

        Example:
            0.50 → 2.00 (even money)
            0.67 → 1.50
            0.33 → 3.00
        """
        if probability <= 0 or probability >= 1:
            raise ValueError("Probability must be between 0 and 1")
        return 1 / probability

    # -------------------------------------------------------------------------
    # Expected Value
    # -------------------------------------------------------------------------

    @staticmethod
    def expected_value(
        bet_amount: float,
        probability: float,
        odds: float,
    ) -> float:
        """
        Calculate expected value of a bet

        EV = (probability * profit) - ((1 - probability) * loss)

        Args:
            bet_amount: Amount wagered
            probability: Win probability (0 to 1)
            odds: Decimal odds

        Returns:
            Expected value (positive = +EV, negative = -EV)

        Example:
            Bet $100 at 2.00 odds with 60% win probability:
            EV = (0.60 * $100) - (0.40 * $100) = $20
        """
        profit_if_win = bet_amount * (odds - 1)
        loss_if_lose = bet_amount

        ev = (probability * profit_if_win) - ((1 - probability) * loss_if_lose)
        return ev

    @staticmethod
    def expected_roi(probability: float, odds: float) -> float:
        """
        Calculate expected return on investment

        Args:
            probability: Win probability
            odds: Decimal odds

        Returns:
            Expected ROI as decimal (e.g., 0.20 = 20% ROI)
        """
        ev = OddsUtilities.expected_value(1.0, probability, odds)
        return ev  # Since bet amount is 1.0, EV = ROI

    # -------------------------------------------------------------------------
    # Utility Functions
    # -------------------------------------------------------------------------

    @staticmethod
    def is_positive_ev(
        your_probability: float,
        odds: float,
        away_odds: Optional[float] = None,
    ) -> bool:
        """
        Check if a bet has positive expected value

        Args:
            your_probability: Your win probability estimate
            odds: Market odds
            away_odds: Optional for vig removal

        Returns:
            True if +EV, False if -EV
        """
        edge = OddsUtilities.calculate_edge(your_probability, odds, away_odds)
        return edge > 0

    @staticmethod
    def breakeven_probability(odds: float) -> float:
        """
        Calculate the minimum win probability needed to break even

        Args:
            odds: Decimal odds

        Returns:
            Breakeven probability (0 to 1)

        Example:
            2.00 odds → need 50% to break even
            1.50 odds → need 66.7% to break even
        """
        return 1 / odds

    @staticmethod
    def required_edge_for_kelly(odds: float, kelly_fraction: float = 0.25) -> float:
        """
        Calculate minimum edge needed for a given Kelly fraction

        Args:
            odds: Decimal odds
            kelly_fraction: Target Kelly fraction

        Returns:
            Minimum required edge

        Example:
            Want to bet 10% of bankroll at 2.00 odds?
            Required edge ≈ 20%
        """
        b = odds - 1  # Net odds
        # Kelly formula: f = (bp - q) / b
        # Solving for edge when f = kelly_fraction:
        # edge = f * b / b = f
        # (This is simplified - actual depends on specific odds)
        required_edge = kelly_fraction * (1 + b) / b
        return required_edge


class OddsConverter:
    """
    Convenient wrapper for odds conversions with caching
    """

    def __init__(self):
        self._cache = {}

    def convert(
        self,
        value: float,
        from_format: OddsFormat,
        to_format: OddsFormat,
    ) -> float:
        """
        Convert between any two odds formats

        Args:
            value: Odds value in source format
            from_format: Source format
            to_format: Target format

        Returns:
            Converted odds value
        """
        cache_key = (value, from_format, to_format)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Convert to decimal as intermediate
        if from_format == OddsFormat.DECIMAL:
            decimal = value
        elif from_format == OddsFormat.AMERICAN:
            decimal = OddsUtilities.american_to_decimal(value)
        elif from_format == OddsFormat.IMPLIED:
            decimal = OddsUtilities.implied_probability_to_decimal(value)
        else:
            raise ValueError(f"Unsupported from_format: {from_format}")

        # Convert from decimal to target
        if to_format == OddsFormat.DECIMAL:
            result = decimal
        elif to_format == OddsFormat.AMERICAN:
            result = OddsUtilities.decimal_to_american(decimal)
        elif to_format == OddsFormat.IMPLIED:
            result = OddsUtilities.decimal_to_implied_probability(decimal)
        else:
            raise ValueError(f"Unsupported to_format: {to_format}")

        self._cache[cache_key] = result
        return result


if __name__ == "__main__":
    # Example usage
    print("Odds Utilities Examples")
    print("=" * 60)

    # Example 1: Vig Removal
    print("\n1. Vig Removal")
    print("-" * 60)
    home_odds = 1.91
    away_odds = 1.91

    p_home_fair, p_away_fair = OddsUtilities.remove_vig_multiplicative(home_odds, away_odds)
    vig_pct = OddsUtilities.calculate_vig_percentage(home_odds, away_odds)

    print(f"Market Odds: Home {home_odds}, Away {away_odds}")
    print(f"Vig: {vig_pct:.2%}")
    print(f"Fair Probabilities: Home {p_home_fair:.1%}, Away {p_away_fair:.1%}")

    # Example 2: Edge Calculation
    print("\n2. Edge Calculation")
    print("-" * 60)
    your_prob = 0.85
    market_home = 1.50
    market_away = 2.80

    edge = OddsUtilities.calculate_edge(your_prob, market_home, market_away)
    print(f"Your Probability: {your_prob:.1%}")
    print(f"Market Odds: {market_home}")
    print(f"Your Edge: {edge:.1%}")

    if edge > 0:
        print("✓ Positive EV - Consider betting!")
    else:
        print("✗ Negative EV - Do not bet")

    # Example 3: Expected Value
    print("\n3. Expected Value")
    print("-" * 60)
    bet_amount = 100
    ev = OddsUtilities.expected_value(bet_amount, your_prob, market_home)
    roi = OddsUtilities.expected_roi(your_prob, market_home)

    print(f"Bet: ${bet_amount}")
    print(f"Odds: {market_home}")
    print(f"Your Probability: {your_prob:.1%}")
    print(f"Expected Value: ${ev:.2f}")
    print(f"Expected ROI: {roi:.1%}")

    # Example 4: Odds Conversions
    print("\n4. Odds Conversions")
    print("-" * 60)
    american = -110
    decimal = OddsUtilities.american_to_decimal(american)
    implied = OddsUtilities.decimal_to_implied_probability(decimal)

    print(f"American: {american}")
    print(f"Decimal: {decimal:.2f}")
    print(f"Implied Probability: {implied:.1%}")
    print(f"Breakeven: {implied:.1%}")
