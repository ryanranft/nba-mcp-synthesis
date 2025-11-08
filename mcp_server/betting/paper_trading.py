"""
Paper Trading Module

Simulates real betting without risking actual money. Essential for validating
betting systems before production deployment.

Features:
- Simulated bankroll management
- Bet placement and outcome recording
- Performance tracking (ROI, Sharpe ratio, win rate)
- CLV (Closing Line Value) tracking
- SQLite persistence for bet history
- Integration with BettingDecisionEngine

Key Workflow:
-----------
1. Initialize paper trading engine with starting bankroll
2. Make betting decisions via BettingDecisionEngine
3. Record paper bets with simulated execution
4. Update outcomes when games complete
5. Track performance over time
6. Validate system before real money deployment

Example:
-------
    from mcp_server.betting.paper_trading import PaperTradingEngine
    from mcp_server.betting.betting_decision import BettingDecisionEngine

    # Initialize paper trading
    paper_engine = PaperTradingEngine(
        starting_bankroll=10000,
        db_path="data/paper_trades.db"
    )

    # Make betting decision
    betting_engine = BettingDecisionEngine(...)
    decision = betting_engine.decide(
        sim_prob=0.65,
        odds=1.90,
        away_odds=2.00,
        bankroll=paper_engine.current_bankroll,
        game_id="LAL_vs_GSW_20250105"
    )

    # Record paper bet if recommended
    if decision['should_bet']:
        bet = paper_engine.place_bet(
            game_id=decision['game_id'],
            bet_type='home',  # or 'away'
            amount=decision['bet_amount'],
            odds=decision['odds'],
            sim_prob=decision['sim_prob'],
            edge=decision['edge']
        )
        print(f"Paper bet placed: ${bet.amount:.2f} at odds {bet.odds}")

    # Later: record outcome
    paper_engine.settle_bet(
        bet_id=bet.bet_id,
        outcome='win',  # or 'loss'
        closing_odds=2.00  # For CLV calculation
    )

    # View performance
    stats = paper_engine.get_performance_stats()
    print(f"ROI: {stats['roi']:.1%}")
    print(f"Win rate: {stats['win_rate']:.1%}")
    print(f"CLV: {stats['avg_clv']:.2%}")
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from enum import Enum
import sqlite3
import json
import numpy as np
from pathlib import Path


class BetStatus(str, Enum):
    """Status of a paper bet"""
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    PUSHED = "pushed"  # Tie/refund
    CANCELLED = "cancelled"


class BetType(str, Enum):
    """Type of bet (home or away)"""
    HOME = "home"
    AWAY = "away"


@dataclass
class PaperBet:
    """
    Represents a single paper bet

    Tracks all metadata needed for performance analysis and CLV tracking.
    """
    bet_id: str
    timestamp: datetime
    game_id: str
    bet_type: BetType
    amount: float
    odds: float  # Decimal odds (e.g., 1.90)
    sim_prob: float  # Probability from simulation
    edge: float  # Calculated edge
    status: BetStatus = BetStatus.PENDING

    # Outcome tracking
    outcome: Optional[str] = None  # 'win', 'loss', 'push'
    payout: Optional[float] = None  # Actual payout amount
    profit_loss: Optional[float] = None  # Net profit/loss

    # CLV tracking
    closing_odds: Optional[float] = None  # Closing line odds
    clv: Optional[float] = None  # Closing line value

    # Metadata
    kelly_fraction: Optional[float] = None  # Fraction of Kelly used
    bankroll_at_bet: Optional[float] = None  # Bankroll when bet placed
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        d['bet_type'] = self.bet_type.value
        d['status'] = self.status.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'PaperBet':
        """Create from dictionary"""
        d['timestamp'] = datetime.fromisoformat(d['timestamp'])
        d['bet_type'] = BetType(d['bet_type'])
        d['status'] = BetStatus(d['status'])
        return cls(**d)


class PaperBettingDatabase:
    """
    SQLite database for paper trading persistence

    Schema:
    -------
    bets table:
    - bet_id (TEXT PRIMARY KEY)
    - timestamp (TEXT)
    - game_id (TEXT)
    - bet_type (TEXT)
    - amount (REAL)
    - odds (REAL)
    - sim_prob (REAL)
    - edge (REAL)
    - status (TEXT)
    - outcome (TEXT)
    - payout (REAL)
    - profit_loss (REAL)
    - closing_odds (REAL)
    - clv (REAL)
    - kelly_fraction (REAL)
    - bankroll_at_bet (REAL)
    - notes (TEXT)

    bankroll_history table:
    - timestamp (TEXT)
    - bankroll (REAL)
    - total_bets (INTEGER)
    - total_won (INTEGER)
    - total_lost (INTEGER)
    - total_profit_loss (REAL)
    """

    def __init__(self, db_path: str = "data/paper_trades.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Bets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                bet_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                game_id TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                amount REAL NOT NULL,
                odds REAL NOT NULL,
                sim_prob REAL NOT NULL,
                edge REAL NOT NULL,
                status TEXT NOT NULL,
                outcome TEXT,
                payout REAL,
                profit_loss REAL,
                closing_odds REAL,
                clv REAL,
                kelly_fraction REAL,
                bankroll_at_bet REAL,
                notes TEXT
            )
        """)

        # Bankroll history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bankroll_history (
                timestamp TEXT PRIMARY KEY,
                bankroll REAL NOT NULL,
                total_bets INTEGER NOT NULL,
                total_won INTEGER NOT NULL,
                total_lost INTEGER NOT NULL,
                total_profit_loss REAL NOT NULL
            )
        """)

        # Indices for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bets_timestamp ON bets(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bets_game_id ON bets(game_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(status)")

        conn.commit()
        conn.close()

    def save_bet(self, bet: PaperBet):
        """Save or update a bet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO bets VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            bet.bet_id,
            bet.timestamp.isoformat(),
            bet.game_id,
            bet.bet_type.value,
            bet.amount,
            bet.odds,
            bet.sim_prob,
            bet.edge,
            bet.status.value,
            bet.outcome,
            bet.payout,
            bet.profit_loss,
            bet.closing_odds,
            bet.clv,
            bet.kelly_fraction,
            bet.bankroll_at_bet,
            bet.notes
        ))

        conn.commit()
        conn.close()

    def get_bet(self, bet_id: str) -> Optional[PaperBet]:
        """Retrieve a bet by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM bets WHERE bet_id = ?", (bet_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_bet(row)
        return None

    def get_all_bets(self, status: Optional[BetStatus] = None) -> List[PaperBet]:
        """Get all bets, optionally filtered by status"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute("SELECT * FROM bets WHERE status = ? ORDER BY timestamp DESC", (status.value,))
        else:
            cursor.execute("SELECT * FROM bets ORDER BY timestamp DESC")

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_bet(row) for row in rows]

    def get_pending_bets(self) -> List[PaperBet]:
        """Get all pending bets"""
        return self.get_all_bets(status=BetStatus.PENDING)

    def save_bankroll_snapshot(self, bankroll: float, total_bets: int,
                                 total_won: int, total_lost: int, total_pl: float):
        """Save a bankroll snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO bankroll_history VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            bankroll,
            total_bets,
            total_won,
            total_lost,
            total_pl
        ))

        conn.commit()
        conn.close()

    def get_bankroll_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent bankroll history"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM bankroll_history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def _row_to_bet(self, row: sqlite3.Row) -> PaperBet:
        """Convert database row to PaperBet"""
        return PaperBet(
            bet_id=row['bet_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            game_id=row['game_id'],
            bet_type=BetType(row['bet_type']),
            amount=row['amount'],
            odds=row['odds'],
            sim_prob=row['sim_prob'],
            edge=row['edge'],
            status=BetStatus(row['status']),
            outcome=row['outcome'],
            payout=row['payout'],
            profit_loss=row['profit_loss'],
            closing_odds=row['closing_odds'],
            clv=row['clv'],
            kelly_fraction=row['kelly_fraction'],
            bankroll_at_bet=row['bankroll_at_bet'],
            notes=row['notes']
        )


class PaperTradingEngine:
    """
    Paper trading engine for simulated betting

    Manages simulated bankroll, bet placement, outcome recording,
    and performance tracking without risking real money.
    """

    def __init__(
        self,
        starting_bankroll: float = 10000.0,
        db_path: str = "data/paper_trades.db",
        max_bet_pct: float = 0.10,  # Max 10% of bankroll per bet
        min_bet: float = 10.0
    ):
        """
        Initialize paper trading engine

        Args:
            starting_bankroll: Starting bankroll in dollars
            db_path: Path to SQLite database
            max_bet_pct: Maximum bet as % of bankroll (safety limit)
            min_bet: Minimum bet size in dollars
        """
        self.starting_bankroll = starting_bankroll
        self.current_bankroll = starting_bankroll
        self.db = PaperBettingDatabase(db_path)
        self.max_bet_pct = max_bet_pct
        self.min_bet = min_bet

        # Load existing bets to restore bankroll state
        self._restore_bankroll_state()

    def _restore_bankroll_state(self):
        """Restore bankroll from database"""
        settled_bets = [
            bet for bet in self.db.get_all_bets()
            if bet.status in (BetStatus.WON, BetStatus.LOST, BetStatus.PUSHED)
        ]

        if settled_bets:
            total_pl = sum(bet.profit_loss for bet in settled_bets if bet.profit_loss)
            self.current_bankroll = self.starting_bankroll + total_pl

    def place_bet(
        self,
        game_id: str,
        bet_type: Literal['home', 'away'],
        amount: float,
        odds: float,
        sim_prob: float,
        edge: float,
        kelly_fraction: Optional[float] = None,
        notes: Optional[str] = None
    ) -> PaperBet:
        """
        Place a paper bet

        Args:
            game_id: Unique game identifier
            bet_type: 'home' or 'away'
            amount: Bet amount in dollars
            odds: Decimal odds (e.g., 1.90)
            sim_prob: Simulation probability
            edge: Calculated edge
            kelly_fraction: Kelly fraction used
            notes: Optional notes

        Returns:
            PaperBet object

        Raises:
            ValueError: If bet amount exceeds limits
        """
        # Validate bet amount
        max_bet = self.current_bankroll * self.max_bet_pct
        if amount > max_bet:
            raise ValueError(f"Bet amount ${amount:.2f} exceeds max ${max_bet:.2f} ({self.max_bet_pct:.0%} of bankroll)")

        if amount < self.min_bet:
            raise ValueError(f"Bet amount ${amount:.2f} below minimum ${self.min_bet:.2f}")

        if amount > self.current_bankroll:
            raise ValueError(f"Bet amount ${amount:.2f} exceeds current bankroll ${self.current_bankroll:.2f}")

        # Create bet
        bet_id = f"{game_id}_{bet_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        bet = PaperBet(
            bet_id=bet_id,
            timestamp=datetime.now(),
            game_id=game_id,
            bet_type=BetType(bet_type),
            amount=amount,
            odds=odds,
            sim_prob=sim_prob,
            edge=edge,
            status=BetStatus.PENDING,
            kelly_fraction=kelly_fraction,
            bankroll_at_bet=self.current_bankroll,
            notes=notes
        )

        # Save to database
        self.db.save_bet(bet)

        # Update bankroll (deduct stake)
        # Note: We don't deduct immediately in paper trading since it's simulated
        # Real bankroll tracking happens when bet settles

        return bet

    def settle_bet(
        self,
        bet_id: str,
        outcome: Literal['win', 'loss', 'push'],
        closing_odds: Optional[float] = None
    ) -> PaperBet:
        """
        Settle a paper bet and update bankroll

        Args:
            bet_id: Bet identifier
            outcome: 'win', 'loss', or 'push'
            closing_odds: Closing line odds for CLV calculation

        Returns:
            Updated PaperBet object

        Raises:
            ValueError: If bet not found or already settled
        """
        # Load bet
        bet = self.db.get_bet(bet_id)
        if not bet:
            raise ValueError(f"Bet {bet_id} not found")

        if bet.status != BetStatus.PENDING:
            raise ValueError(f"Bet {bet_id} already settled with status {bet.status}")

        # Calculate payout and profit/loss
        if outcome == 'win':
            bet.status = BetStatus.WON
            bet.payout = bet.amount * bet.odds
            bet.profit_loss = bet.payout - bet.amount
        elif outcome == 'loss':
            bet.status = BetStatus.LOST
            bet.payout = 0
            bet.profit_loss = -bet.amount
        elif outcome == 'push':
            bet.status = BetStatus.PUSHED
            bet.payout = bet.amount
            bet.profit_loss = 0
        else:
            raise ValueError(f"Invalid outcome: {outcome}")

        bet.outcome = outcome

        # Calculate CLV if closing odds provided
        if closing_odds:
            bet.closing_odds = closing_odds
            # CLV = (closing_implied_prob - opening_implied_prob) / opening_implied_prob
            opening_implied = 1 / bet.odds
            closing_implied = 1 / closing_odds
            bet.clv = (closing_implied - opening_implied) / opening_implied

        # Update bankroll
        self.current_bankroll += bet.profit_loss

        # Save updated bet
        self.db.save_bet(bet)

        # Save bankroll snapshot
        stats = self.get_performance_stats()
        self.db.save_bankroll_snapshot(
            bankroll=self.current_bankroll,
            total_bets=stats['total_bets'],
            total_won=stats['total_won'],
            total_lost=stats['total_lost'],
            total_pl=stats['total_profit_loss']
        )

        return bet

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Calculate comprehensive performance statistics

        Returns:
            Dictionary with performance metrics:
            - roi: Return on investment
            - win_rate: Winning bet percentage
            - total_profit_loss: Net profit/loss
            - avg_bet: Average bet size
            - avg_odds: Average odds
            - avg_edge: Average edge
            - avg_clv: Average closing line value
            - sharpe_ratio: Risk-adjusted return
            - max_drawdown: Maximum drawdown from peak
            - current_streak: Current win/loss streak
        """
        all_bets = self.db.get_all_bets()
        settled_bets = [
            bet for bet in all_bets
            if bet.status in (BetStatus.WON, BetStatus.LOST, BetStatus.PUSHED)
        ]

        if not settled_bets:
            return {
                'total_bets': 0,
                'total_won': 0,
                'total_lost': 0,
                'total_pushed': 0,
                'win_rate': 0,
                'roi': 0,
                'total_profit_loss': 0,
                'total_staked': 0,
                'avg_bet': 0,
                'avg_odds': 0,
                'avg_edge': 0,
                'avg_clv': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'current_streak': 0,
                'bankroll': self.current_bankroll,
                'bankroll_change_pct': 0
            }

        # Basic stats
        total_won = sum(1 for bet in settled_bets if bet.status == BetStatus.WON)
        total_lost = sum(1 for bet in settled_bets if bet.status == BetStatus.LOST)
        total_pushed = sum(1 for bet in settled_bets if bet.status == BetStatus.PUSHED)

        win_rate = total_won / len(settled_bets) if settled_bets else 0

        total_pl = sum(bet.profit_loss for bet in settled_bets if bet.profit_loss)
        total_staked = sum(bet.amount for bet in settled_bets)
        roi = total_pl / total_staked if total_staked > 0 else 0

        avg_bet = np.mean([bet.amount for bet in settled_bets])
        avg_odds = np.mean([bet.odds for bet in settled_bets])
        avg_edge = np.mean([bet.edge for bet in settled_bets])

        # CLV stats
        clv_bets = [bet for bet in settled_bets if bet.clv is not None]
        avg_clv = np.mean([bet.clv for bet in clv_bets]) if clv_bets else 0

        # Sharpe ratio (risk-adjusted return)
        returns = [bet.profit_loss / bet.amount for bet in settled_bets if bet.amount > 0]
        if len(returns) > 1:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0

        # Max drawdown
        cumulative_pls = np.cumsum([bet.profit_loss for bet in settled_bets if bet.profit_loss])
        if len(cumulative_pls) > 0:
            running_max = np.maximum.accumulate(cumulative_pls)
            drawdowns = cumulative_pls - running_max
            max_drawdown = np.min(drawdowns) if len(drawdowns) > 0 else 0
        else:
            max_drawdown = 0

        # Current streak
        current_streak = 0
        if settled_bets:
            for bet in reversed(settled_bets):
                if bet.status == BetStatus.WON:
                    current_streak += 1
                elif bet.status == BetStatus.LOST:
                    current_streak -= 1
                    break
                else:  # PUSHED
                    break

        return {
            'total_bets': len(settled_bets),
            'total_won': total_won,
            'total_lost': total_lost,
            'total_pushed': total_pushed,
            'win_rate': win_rate,
            'roi': roi,
            'total_profit_loss': total_pl,
            'total_staked': total_staked,
            'avg_bet': avg_bet,
            'avg_odds': avg_odds,
            'avg_edge': avg_edge,
            'avg_clv': avg_clv,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'current_streak': current_streak,
            'bankroll': self.current_bankroll,
            'bankroll_change_pct': (self.current_bankroll - self.starting_bankroll) / self.starting_bankroll
        }
