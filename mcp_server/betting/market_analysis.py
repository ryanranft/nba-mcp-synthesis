"""
Market Analysis Module

Validates betting edges through market efficiency analysis:

1. **Closing Line Value (CLV)**: Are you consistently beating sharp money?
2. **Market Efficiency Tests**: Detect when markets are mispriced
3. **Cointegration Analysis**: Find arbitrage opportunities
4. **Line Movement Tracking**: Identify sharp vs public money

Key Insight:
-----------
Your simulation might say 90% win probability, but if Vegas closing line
disagrees (implying only 65%), you need to be careful. CLV helps validate
whether your edge is real or an artifact of model miscalibration.

Sharp bettors consistently beat the closing line. If your CLV is negative,
your edge is probably fake.

Closing Line Value (CLV):
------------------------
CLV measures whether you got better odds than sharp money:

    CLV = (closing_prob - bet_prob) / bet_prob

    Positive CLV = you beat sharp money (good sign!)
    Negative CLV = sharp money got better odds (bad sign!)

If you consistently have +CLV over 100+ bets, your edge is likely real.
If CLV < 0, your model is probably miscalibrated - do not trust it for Kelly!

Example:
-------
    tracker = ClosingLineValueTracker()

    # Place bet
    bet_odds = 2.00  # You bet at 2.00 (50% implied)

    # Line closes at 1.80 (55.5% implied)
    closing_odds = 1.80

    clv = tracker.calculate_clv(bet_odds, closing_odds)
    print(f"CLV: {clv:.1%}")  # +11.1% - sharp money agrees!

    # Track over time
    tracker.add_bet(bet_odds, closing_odds)
    avg_clv = tracker.average_clv()

    if avg_clv > 0.02:  # 2%+ average CLV
        print("Sharp bettor - trust your edge")
    else:
        print("Losing to closing line - recalibrate model")
"""

from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import warnings

try:
    from statsmodels.tsa.vector_ar.vecm import coint_johansen
    from statsmodels.tsa.stattools import coint
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    warnings.warn("statsmodels not available. Cointegration tests disabled.")


@dataclass
class BetRecord:
    """Record of a single bet for CLV tracking"""
    date: datetime
    game_id: str
    bet_odds: float           # Odds when you placed bet
    closing_odds: float        # Odds at close (sharp money line)
    bet_prob: float           # Implied probability at bet time
    closing_prob: float        # Implied probability at close
    clv: float                # Closing line value
    outcome: Optional[int] = None  # 1 = win, 0 = loss (filled later)
    profit: Optional[float] = None  # Profit/loss (filled later)


class ClosingLineValueTracker:
    """
    Tracks CLV (Closing Line Value) to validate edge

    CLV is the gold standard for measuring betting skill. If you consistently
    beat the closing line, your edge is real. If not, you're likely picking
    up noise, not signal.

    Key Metrics:
    - Average CLV > 2%: Sharp bettor (trust your edge)
    - Average CLV 0-2%: Marginal edge (be careful)
    - Average CLV < 0%: No edge (recalibrate model!)

    Example:
        tracker = ClosingLineValueTracker()

        # Add bet
        tracker.add_bet(
            date=datetime.now(),
            game_id="LAL_vs_GSW",
            bet_odds=2.00,
            closing_odds=1.80
        )

        # Check if sharp
        if tracker.is_sharp():
            print("You're beating sharp money!")
        else:
            print("Recalibrate your model")
    """

    def __init__(self):
        self.bets: List[BetRecord] = []

    def calculate_clv(self, bet_odds: float, closing_odds: float) -> float:
        """
        Calculate CLV for a single bet

        Args:
            bet_odds: Decimal odds when you placed bet
            closing_odds: Decimal odds at close

        Returns:
            CLV as decimal (e.g., 0.05 = 5% CLV)

        Interpretation:
            CLV > 0: You got better odds than sharp money ✓
            CLV < 0: Sharp money got better odds ✗

        Example:
            Bet at 2.00 (50% implied)
            Close at 1.80 (55.5% implied)
            CLV = (0.555 - 0.50) / 0.50 = 11.1%
        """
        bet_prob = 1 / bet_odds
        closing_prob = 1 / closing_odds

        clv = (closing_prob - bet_prob) / bet_prob
        return clv

    def add_bet(
        self,
        date: datetime,
        game_id: str,
        bet_odds: float,
        closing_odds: float,
        outcome: Optional[int] = None,
        bet_amount: Optional[float] = None,
    ):
        """
        Add a bet to the tracker

        Args:
            date: When bet was placed
            game_id: Game identifier
            bet_odds: Odds when bet was placed
            closing_odds: Odds at close
            outcome: Optional outcome (1=win, 0=loss)
            bet_amount: Optional bet amount for profit tracking
        """
        bet_prob = 1 / bet_odds
        closing_prob = 1 / closing_odds
        clv = self.calculate_clv(bet_odds, closing_odds)

        profit = None
        if outcome is not None and bet_amount is not None:
            if outcome == 1:
                profit = bet_amount * (bet_odds - 1)
            else:
                profit = -bet_amount

        record = BetRecord(
            date=date,
            game_id=game_id,
            bet_odds=bet_odds,
            closing_odds=closing_odds,
            bet_prob=bet_prob,
            closing_prob=closing_prob,
            clv=clv,
            outcome=outcome,
            profit=profit,
        )

        self.bets.append(record)

    def average_clv(self, recent_n: Optional[int] = None) -> float:
        """
        Calculate average CLV

        Args:
            recent_n: Only use last N bets (None = all bets)

        Returns:
            Average CLV

        Interpretation:
            > 2%: Sharp bettor - trust your edge
            0-2%: Marginal edge - be careful
            < 0%: No edge - recalibrate!
        """
        if not self.bets:
            return 0.0

        bets = self.bets[-recent_n:] if recent_n else self.bets
        return np.mean([b.clv for b in bets])

    def is_sharp(self, threshold: float = 0.02, min_bets: int = 50) -> bool:
        """
        Check if bettor is consistently sharp

        Args:
            threshold: Minimum average CLV to be considered sharp (default: 2%)
            min_bets: Minimum number of bets required

        Returns:
            True if sharp bettor, False otherwise
        """
        if len(self.bets) < min_bets:
            return False

        avg_clv = self.average_clv()
        return avg_clv > threshold

    def clv_over_time(self) -> List[float]:
        """Return CLV for each bet chronologically"""
        return [b.clv for b in self.bets]

    def cumulative_clv(self) -> List[float]:
        """Return cumulative average CLV over time"""
        if not self.bets:
            return []

        clvs = self.clv_over_time()
        cumulative = []
        for i in range(1, len(clvs) + 1):
            cumulative.append(np.mean(clvs[:i]))
        return cumulative

    def clv_by_threshold(self, threshold: float = 0.03) -> Dict[str, int]:
        """
        Count bets with CLV above/below threshold

        Args:
            threshold: CLV threshold

        Returns:
            {'above': count, 'below': count}
        """
        if not self.bets:
            return {'above': 0, 'below': 0}

        clvs = self.clv_over_time()
        return {
            'above': sum(1 for clv in clvs if clv > threshold),
            'below': sum(1 for clv in clvs if clv <= threshold),
        }

    def win_rate(self) -> float:
        """Calculate win rate of bets with outcomes"""
        bets_with_outcome = [b for b in self.bets if b.outcome is not None]
        if not bets_with_outcome:
            return np.nan

        return np.mean([b.outcome for b in bets_with_outcome])

    def roi(self) -> float:
        """Calculate return on investment"""
        bets_with_profit = [b for b in self.bets if b.profit is not None]
        if not bets_with_profit:
            return np.nan

        total_bet = sum(abs(b.profit / (b.bet_odds - 1)) if b.profit > 0 else abs(b.profit) for b in bets_with_profit)
        total_profit = sum(b.profit for b in bets_with_profit)

        if total_bet == 0:
            return np.nan

        return total_profit / total_bet

    def summary_statistics(self) -> Dict[str, Any]:
        """Return comprehensive summary"""
        if not self.bets:
            return {}

        return {
            'total_bets': len(self.bets),
            'average_clv': self.average_clv(),
            'recent_clv_50': self.average_clv(recent_n=50),
            'recent_clv_20': self.average_clv(recent_n=20),
            'is_sharp': self.is_sharp(),
            'win_rate': self.win_rate(),
            'roi': self.roi(),
            'clv_above_3pct': self.clv_by_threshold(0.03)['above'],
            'clv_below_0': self.clv_by_threshold(0.0)['below'],
        }


class MarketEfficiencyAnalyzer:
    """
    Detect market inefficiencies through statistical tests

    Efficient markets should exhibit certain properties:
    - Home and away odds should be cointegrated
    - Totals should cluster around historical means
    - Line movements should be random (no patterns)

    When these properties break down, inefficiencies exist that can be exploited.

    Key Tests:
    1. Cointegration: Do related markets move together?
    2. Mean Reversion: Are totals/spreads mean-reverting?
    3. Z-Score Analysis: Is current line unusual vs history?
    """

    @staticmethod
    def detect_mispricing(
        current_value: float,
        historical_mean: float,
        historical_std: float,
        threshold: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Detect if current value is unusual vs history

        Uses z-score to detect statistical anomalies.

        Args:
            current_value: Current market value (e.g., total, spread)
            historical_mean: Historical mean
            historical_std: Historical standard deviation
            threshold: Z-score threshold for mispricing (default: 2.0)

        Returns:
            Dict with mispricing info

        Example:
            Historical total: 215 ± 8 points
            Current total: 235 points
            Z-score: (235 - 215) / 8 = 2.5 (mispriced!)
        """
        z_score = (current_value - historical_mean) / historical_std

        is_mispriced = abs(z_score) > threshold

        return {
            'mispriced': is_mispriced,
            'z_score': z_score,
            'direction': 'over' if z_score > 0 else 'under',
            'confidence': 1 - (2 * (1 - 0.9772)) if abs(z_score) > 2 else 0,  # Rough p-value
            'current_value': current_value,
            'expected_value': historical_mean,
            'deviation': current_value - historical_mean,
        }

    @staticmethod
    def cointegration_test(
        series1: np.ndarray,
        series2: np.ndarray,
        significance: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Test if two price series are cointegrated

        Cointegration means series move together in long run.
        If home/away odds are NOT cointegrated, market is inefficient.

        Args:
            series1: First time series (e.g., home odds history)
            series2: Second time series (e.g., away odds history)
            significance: Significance level (default: 0.05)

        Returns:
            Dict with test results

        Example:
            Home odds: [1.90, 1.85, 1.95, 1.88, ...]
            Away odds: [2.00, 2.10, 1.95, 2.05, ...]

            If cointegrated: Market is efficient
            If not cointegrated: Potential inefficiency!
        """
        if not STATSMODELS_AVAILABLE:
            return {'error': 'statsmodels not available'}

        if len(series1) < 12:
            return {'error': 'Insufficient data (need 12+ observations)'}

        try:
            # Engle-Granger cointegration test
            score, pvalue, _ = coint(series1, series2)

            is_cointegrated = pvalue < significance

            return {
                'cointegrated': is_cointegrated,
                'test_statistic': score,
                'p_value': pvalue,
                'significance': significance,
                'interpretation': (
                    'Market efficient (prices move together)'
                    if is_cointegrated
                    else 'Potential inefficiency (prices diverging)'
                ),
            }
        except Exception as e:
            return {'error': f'Cointegration test failed: {str(e)}'}

    @staticmethod
    def johansen_cointegration(
        data: np.ndarray,
        det_order: int = 0,
        k_ar_diff: int = 1,
    ) -> Dict[str, Any]:
        """
        Johansen cointegration test for multiple series

        More powerful than pairwise Engle-Granger test.

        Args:
            data: Array of shape (n_observations, n_series)
            det_order: Deterministic trend order
            k_ar_diff: Lags for AR differencing

        Returns:
            Dict with test results
        """
        if not STATSMODELS_AVAILABLE:
            return {'error': 'statsmodels not available'}

        if data.shape[0] < 12:
            return {'error': 'Insufficient data'}

        try:
            result = coint_johansen(data, det_order=det_order, k_ar_diff=k_ar_diff)

            # Check trace statistic vs critical value at 95%
            trace_stat = result.trace_stat[0]
            crit_val = result.trace_stat_crit_vals[0, 1]  # 95% level

            is_cointegrated = trace_stat > crit_val

            return {
                'cointegrated': is_cointegrated,
                'trace_statistic': trace_stat,
                'critical_value_95pct': crit_val,
                'efficiency_score': trace_stat / crit_val,
                'interpretation': (
                    'Market efficient'
                    if is_cointegrated
                    else 'Potential inefficiency'
                ),
            }
        except Exception as e:
            return {'error': f'Johansen test failed: {str(e)}'}

    @staticmethod
    def line_movement_analysis(
        opening_odds: float,
        current_odds: float,
        closing_odds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Analyze line movement to identify sharp vs public money

        Sharp money moves lines early.
        Public money moves lines late.

        Args:
            opening_odds: Odds at opening
            current_odds: Current odds
            closing_odds: Optional closing odds

        Returns:
            Dict with movement analysis

        Example:
            Open: 2.00 → Current: 1.85 → Close: 1.80

            Line moved toward favorite (from 2.00 to 1.80)
            Early movement (open to current): Sharp money
            Late movement (current to close): Public money
        """
        opening_prob = 1 / opening_odds
        current_prob = 1 / current_odds

        early_movement = (current_prob - opening_prob) / opening_prob

        result = {
            'opening_odds': opening_odds,
            'current_odds': current_odds,
            'early_movement': early_movement,
            'direction': 'toward favorite' if early_movement > 0 else 'toward underdog',
            'magnitude': abs(early_movement),
        }

        if closing_odds is not None:
            closing_prob = 1 / closing_odds
            late_movement = (closing_prob - current_prob) / current_prob
            total_movement = (closing_prob - opening_prob) / opening_prob

            result.update({
                'closing_odds': closing_odds,
                'late_movement': late_movement,
                'total_movement': total_movement,
                'interpretation': (
                    'Sharp money dominated' if abs(early_movement) > abs(late_movement)
                    else 'Public money dominated'
                ),
            })

        return result


if __name__ == "__main__":
    # Example usage
    print("Market Analysis Examples")
    print("=" * 70)

    # Example 1: CLV Tracking
    print("\n1. Closing Line Value (CLV) Tracking")
    print("-" * 70)

    tracker = ClosingLineValueTracker()

    # Simulate 20 bets
    np.random.seed(42)
    for i in range(20):
        bet_odds = np.random.uniform(1.50, 3.00)
        # Sharp bettor: closing line moves in your favor
        closing_odds = bet_odds * np.random.uniform(0.90, 0.98)  # Line moves toward you

        tracker.add_bet(
            date=datetime.now(),
            game_id=f"GAME_{i}",
            bet_odds=bet_odds,
            closing_odds=closing_odds,
        )

    stats = tracker.summary_statistics()
    print(f"Total Bets: {stats['total_bets']}")
    print(f"Average CLV: {stats['average_clv']:.1%}")
    print(f"Recent CLV (50): {stats['recent_clv_50']:.1%}")
    print(f"Is Sharp: {stats['is_sharp']}")

    if tracker.is_sharp():
        print("✓ You're consistently beating sharp money - trust your edge!")
    else:
        print("✗ Not beating closing line - recalibrate model")

    # Example 2: Mispricing Detection
    print("\n2. Mispricing Detection")
    print("-" * 70)

    # Historical average total: 215 points, std: 8 points
    # Current total: 235 points (unusual!)
    mispricing = MarketEfficiencyAnalyzer.detect_mispricing(
        current_value=235,
        historical_mean=215,
        historical_std=8,
        threshold=2.0,
    )

    print(f"Current Total: {mispricing['current_value']}")
    print(f"Historical Mean: {mispricing['expected_value']}")
    print(f"Z-Score: {mispricing['z_score']:.2f}")
    print(f"Mispriced: {mispricing['mispriced']}")

    if mispricing['mispriced']:
        print(f"✓ Market inefficiency detected - consider betting {mispricing['direction']}")
    else:
        print("Market price appears fair")

    # Example 3: Line Movement Analysis
    print("\n3. Line Movement Analysis")
    print("-" * 70)

    movement = MarketEfficiencyAnalyzer.line_movement_analysis(
        opening_odds=2.00,
        current_odds=1.85,
        closing_odds=1.80,
    )

    print(f"Opening: {movement['opening_odds']}")
    print(f"Current: {movement['current_odds']}")
    print(f"Closing: {movement['closing_odds']}")
    print(f"Early Movement: {movement['early_movement']:.1%}")
    print(f"Late Movement: {movement['late_movement']:.1%}")
    print(f"Interpretation: {movement['interpretation']}")
