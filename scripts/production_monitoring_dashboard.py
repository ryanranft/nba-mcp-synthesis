#!/usr/bin/env python3
"""
Production Monitoring Dashboard

Real-time web dashboard for monitoring NBA betting system performance.
Built with Streamlit for rapid development and easy deployment.

Features:
- Real-time performance metrics (ROI, Sharpe ratio, win rate, CLV)
- Interactive charts (bankroll over time, P&L, bet distribution)
- Calibration quality monitoring
- Alert system for poor performance and calibration drift
- Recent bets tracking
- Auto-refresh capabilities

Usage:
------
    # Launch dashboard (default: localhost:8501)
    streamlit run scripts/production_monitoring_dashboard.py

    # Launch on specific port
    streamlit run scripts/production_monitoring_dashboard.py --server.port 8502

    # Launch with auto-refresh every 60 seconds
    streamlit run scripts/production_monitoring_dashboard.py -- --auto-refresh 60

Architecture:
-------------
    Dashboard (Streamlit)
        ├── Data Layer (SQLite databases)
        │   ├── Paper Trading DB (bets, bankroll)
        │   └── Calibration DB (predictions, outcomes)
        ├── Analytics Layer
        │   ├── Performance metrics
        │   ├── Risk metrics
        │   └── Calibration metrics
        └── Visualization Layer
            ├── KPI cards
            ├── Interactive charts (plotly)
            └── Alert indicators

Alert Thresholds:
-----------------
    🚨 CRITICAL (Red):
        - ROI < -10%
        - Win rate < 45%
        - Sharpe ratio < 0.5
        - Brier score > 0.20
        - Max drawdown > 30%

    ⚠️  WARNING (Yellow):
        - ROI < 0%
        - Win rate < 50%
        - Sharpe ratio < 1.0
        - Brier score > 0.15
        - Max drawdown > 20%

    ✅ HEALTHY (Green):
        - ROI > 5%
        - Win rate > 55%
        - Sharpe ratio > 1.5
        - Brier score < 0.10
        - Max drawdown < 15%
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.betting.paper_trading import (
    PaperTradingEngine,
    PaperBettingDatabase,
    BetStatus
)
from mcp_server.betting.probability_calibration import (
    SimulationCalibrator,
    CalibrationDatabase
)


# ============================================================================
# Configuration
# ============================================================================

PAPER_TRADING_DB_PATH = "data/paper_trades.db"
CALIBRATION_DB_PATH = "data/calibration.db"

# Alert thresholds
THRESHOLDS = {
    'roi': {'critical': -0.10, 'warning': 0.0, 'healthy': 0.05},
    'win_rate': {'critical': 0.45, 'warning': 0.50, 'healthy': 0.55},
    'sharpe_ratio': {'critical': 0.5, 'warning': 1.0, 'healthy': 1.5},
    'brier_score': {'critical': 0.20, 'warning': 0.15, 'healthy': 0.10},
    'max_drawdown': {'critical': 0.30, 'warning': 0.20, 'healthy': 0.15},
    'clv': {'critical': -0.05, 'warning': 0.0, 'healthy': 0.02}
}

# Streamlit page config
st.set_page_config(
    page_title="NBA Betting Monitor",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# Data Loading Functions
# ============================================================================

@st.cache_data(ttl=10)  # Cache for 10 seconds
def load_paper_trading_data() -> Tuple[Dict[str, Any], List[Any], List[Dict]]:
    """
    Load paper trading performance data

    Returns:
        Tuple of (performance_stats, all_bets, bankroll_history)
    """
    engine = PaperTradingEngine(
        starting_bankroll=10000,
        db_path=PAPER_TRADING_DB_PATH
    )

    stats = engine.get_performance_stats()
    all_bets = engine.db.get_all_bets()
    bankroll_history = engine.db.get_bankroll_history()

    return stats, all_bets, bankroll_history


@st.cache_data(ttl=10)
def load_calibration_data() -> Tuple[float, float, Optional[Any]]:
    """
    Load calibration quality metrics

    Returns:
        Tuple of (brier_score, log_loss, calibrator)
    """
    try:
        # SimulationCalibrator uses in-memory database, not SQLite
        # For now, return default values
        # TODO: Implement persistent calibration database
        return 0.15, 0.0, None
    except Exception as e:
        st.warning(f"Could not load calibration data: {e}")
        return 0.15, 0.0, None


def get_alert_level(metric: str, value: float) -> str:
    """
    Determine alert level for a metric

    Args:
        metric: Metric name (roi, win_rate, etc.)
        value: Metric value

    Returns:
        'critical', 'warning', or 'healthy'
    """
    if metric not in THRESHOLDS:
        return 'healthy'

    thresholds = THRESHOLDS[metric]

    # Handle metrics where lower is better (brier_score, max_drawdown)
    if metric in ['brier_score', 'max_drawdown']:
        if value >= thresholds['critical']:
            return 'critical'
        elif value >= thresholds['warning']:
            return 'warning'
        else:
            return 'healthy'
    else:
        # Higher is better (roi, win_rate, sharpe_ratio, clv)
        if value <= thresholds['critical']:
            return 'critical'
        elif value <= thresholds['warning']:
            return 'warning'
        else:
            return 'healthy'


def format_metric_with_alert(label: str, value: Any, metric_key: str, format_str: str = ".2f") -> None:
    """
    Display metric with color-coded alert level

    Args:
        label: Metric label
        value: Metric value
        metric_key: Key for threshold lookup
        format_str: Number format string
    """
    alert_level = get_alert_level(metric_key, value)

    # Color mapping
    colors = {
        'critical': '🔴',
        'warning': '🟡',
        'healthy': '🟢'
    }

    color_css = {
        'critical': 'color: #FF4444;',
        'warning': 'color: #FFB000;',
        'healthy': 'color: #00C851;'
    }

    icon = colors.get(alert_level, '⚪')
    css = color_css.get(alert_level, '')

    # Format value
    if isinstance(value, float):
        if format_str.endswith('%'):
            formatted_value = f"{value*100:.1f}%"
        else:
            formatted_value = f"{value:{format_str}}"
    else:
        formatted_value = str(value)

    st.markdown(
        f"{icon} **{label}:** <span style='{css}'>{formatted_value}</span>",
        unsafe_allow_html=True
    )


# ============================================================================
# Visualization Functions
# ============================================================================

def plot_bankroll_over_time(bankroll_history: List[Dict]) -> go.Figure:
    """
    Plot bankroll progression over time

    Args:
        bankroll_history: List of bankroll snapshots

    Returns:
        Plotly figure
    """
    if not bankroll_history:
        return go.Figure()

    df = pd.DataFrame(bankroll_history)

    fig = go.Figure()

    # Bankroll line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['bankroll'],
        mode='lines+markers',
        name='Bankroll',
        line=dict(color='#00C851', width=3),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>Bankroll: $%{y:,.2f}<extra></extra>'
    ))

    # Starting bankroll reference line
    starting_bankroll = df['bankroll'].iloc[0]
    fig.add_hline(
        y=starting_bankroll,
        line_dash="dash",
        line_color="gray",
        annotation_text="Starting Bankroll",
        annotation_position="right"
    )

    fig.update_layout(
        title="Bankroll Over Time",
        xaxis_title="Date",
        yaxis_title="Bankroll ($)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )

    return fig


def plot_cumulative_pl(all_bets: List[Any]) -> go.Figure:
    """
    Plot cumulative profit/loss over time

    Args:
        all_bets: List of all bets

    Returns:
        Plotly figure
    """
    settled_bets = [
        bet for bet in all_bets
        if bet.status in (BetStatus.WON, BetStatus.LOST, BetStatus.PUSHED) and bet.profit_loss is not None
    ]

    if not settled_bets:
        return go.Figure()

    # Sort by timestamp
    settled_bets = sorted(settled_bets, key=lambda x: x.timestamp)

    # Calculate cumulative P/L
    cumulative_pl = np.cumsum([bet.profit_loss for bet in settled_bets])
    timestamps = [bet.timestamp for bet in settled_bets]

    fig = go.Figure()

    # Cumulative P/L line
    fig.add_trace(go.Scatter(
        x=timestamps,
        y=cumulative_pl,
        mode='lines+markers',
        name='Cumulative P/L',
        fill='tozeroy',
        line=dict(color='#4285F4', width=3),
        marker=dict(size=6),
        hovertemplate='<b>%{x}</b><br>P/L: $%{y:,.2f}<extra></extra>'
    ))

    # Zero line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="Break Even",
        annotation_position="right"
    )

    fig.update_layout(
        title="Cumulative Profit/Loss",
        xaxis_title="Date",
        yaxis_title="Cumulative P/L ($)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )

    return fig


def plot_win_rate_rolling(all_bets: List[Any], window: int = 10) -> go.Figure:
    """
    Plot rolling win rate

    Args:
        all_bets: List of all bets
        window: Rolling window size

    Returns:
        Plotly figure
    """
    settled_bets = [
        bet for bet in all_bets
        if bet.status in (BetStatus.WON, BetStatus.LOST)
    ]

    if len(settled_bets) < window:
        return go.Figure()

    # Sort by timestamp
    settled_bets = sorted(settled_bets, key=lambda x: x.timestamp)

    # Calculate rolling win rate
    wins = [1 if bet.status == BetStatus.WON else 0 for bet in settled_bets]
    df = pd.DataFrame({
        'timestamp': [bet.timestamp for bet in settled_bets],
        'win': wins
    })

    df['rolling_win_rate'] = df['win'].rolling(window=window).mean()

    fig = go.Figure()

    # Rolling win rate
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['rolling_win_rate'] * 100,
        mode='lines',
        name=f'{window}-Bet Rolling Win Rate',
        line=dict(color='#FF6F00', width=3),
        hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<extra></extra>'
    ))

    # 50% reference line
    fig.add_hline(
        y=50,
        line_dash="dash",
        line_color="gray",
        annotation_text="50%",
        annotation_position="right"
    )

    fig.update_layout(
        title=f"Rolling Win Rate ({window} Bets)",
        xaxis_title="Date",
        yaxis_title="Win Rate (%)",
        hovermode='x unified',
        template='plotly_white',
        height=400
    )

    return fig


def plot_bet_distribution(all_bets: List[Any]) -> go.Figure:
    """
    Plot bet size distribution

    Args:
        all_bets: List of all bets

    Returns:
        Plotly figure
    """
    if not all_bets:
        return go.Figure()

    bet_amounts = [bet.amount for bet in all_bets]

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=bet_amounts,
        nbinsx=20,
        name='Bet Amount',
        marker=dict(color='#AB47BC'),
        hovertemplate='Bet Size: $%{x:,.2f}<br>Count: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title="Bet Size Distribution",
        xaxis_title="Bet Amount ($)",
        yaxis_title="Frequency",
        template='plotly_white',
        height=400
    )

    return fig


def plot_calibration_curve(calibrator: Any) -> go.Figure:
    """
    Plot calibration curve (predicted vs actual probabilities)

    Args:
        calibrator: SimulationCalibrator instance

    Returns:
        Plotly figure
    """
    if not calibrator or not calibrator.calibration_db:
        return go.Figure()

    records = calibrator.calibration_db.get_all_records()

    if len(records) < 10:
        return go.Figure()

    # Bin predictions
    df = pd.DataFrame([
        {
            'sim_prob': r.simulation_prob,
            'outcome': r.actual_outcome
        }
        for r in records
    ])

    # Create bins
    bins = np.linspace(0, 1, 11)
    df['bin'] = pd.cut(df['sim_prob'], bins=bins, labels=bins[:-1] + 0.05)

    # Calculate average actual outcome per bin
    calibration_data = df.groupby('bin', observed=True).agg({
        'sim_prob': 'mean',
        'outcome': 'mean'
    }).reset_index()

    fig = go.Figure()

    # Perfect calibration line
    fig.add_trace(go.Scatter(
        x=[0, 1],
        y=[0, 1],
        mode='lines',
        name='Perfect Calibration',
        line=dict(color='gray', dash='dash', width=2)
    ))

    # Actual calibration
    fig.add_trace(go.Scatter(
        x=calibration_data['sim_prob'],
        y=calibration_data['outcome'],
        mode='lines+markers',
        name='Actual Calibration',
        line=dict(color='#4285F4', width=3),
        marker=dict(size=10),
        hovertemplate='Predicted: %{x:.1%}<br>Actual: %{y:.1%}<extra></extra>'
    ))

    fig.update_layout(
        title="Calibration Curve",
        xaxis_title="Predicted Probability",
        yaxis_title="Actual Win Rate",
        hovermode='closest',
        template='plotly_white',
        height=400,
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1])
    )

    return fig


# ============================================================================
# Main Dashboard
# ============================================================================

def main():
    """Main dashboard application"""

    # Title
    st.title("🏀 NBA Betting System - Production Monitor")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Auto-refresh
        auto_refresh = st.checkbox("Auto-refresh", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Refresh interval (seconds)", 10, 300, 60)
            time.sleep(refresh_interval)
            st.rerun()

        st.markdown("---")

        # Data paths
        st.subheader("Data Sources")
        st.text(f"Paper Trading DB:\n{PAPER_TRADING_DB_PATH}")
        st.text(f"Calibration DB:\n{CALIBRATION_DB_PATH}")

        st.markdown("---")

        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            st.cache_data.clear()
            st.rerun()

    # Load data
    try:
        stats, all_bets, bankroll_history = load_paper_trading_data()
        brier_score, log_loss, calibrator = load_calibration_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

    # ========================================================================
    # Alert Summary
    # ========================================================================

    st.header("🚨 Alert Status")

    # Check all metrics for alerts
    alerts = []

    if stats['total_bets'] > 10:  # Only show alerts if we have enough data
        metrics_to_check = {
            'ROI': ('roi', stats['roi']),
            'Win Rate': ('win_rate', stats['win_rate']),
            'Sharpe Ratio': ('sharpe_ratio', stats['sharpe_ratio']),
            'Max Drawdown': ('max_drawdown', abs(stats['max_drawdown']) / stats['bankroll']),
            'CLV': ('clv', stats['avg_clv']),
            'Brier Score': ('brier_score', brier_score)
        }

        for label, (key, value) in metrics_to_check.items():
            alert_level = get_alert_level(key, value)
            if alert_level in ['critical', 'warning']:
                alerts.append(f"{label}: {alert_level.upper()}")

    if alerts:
        alert_msg = " | ".join(alerts)
        if 'CRITICAL' in alert_msg:
            st.error(f"⛔ CRITICAL ALERTS: {alert_msg}")
        else:
            st.warning(f"⚠️ WARNINGS: {alert_msg}")
    else:
        st.success("✅ All systems healthy")

    st.markdown("---")

    # ========================================================================
    # Key Performance Indicators
    # ========================================================================

    st.header("📊 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Current Bankroll",
            value=f"${stats['bankroll']:,.2f}",
            delta=f"${stats['total_profit_loss']:,.2f} ({stats['bankroll_change_pct']*100:.1f}%)"
        )
        format_metric_with_alert("ROI", stats['roi'], 'roi', '.1%')

    with col2:
        st.metric(
            label="Total Bets",
            value=f"{stats['total_bets']}",
            delta=f"{stats['total_won']}W / {stats['total_lost']}L"
        )
        format_metric_with_alert("Win Rate", stats['win_rate'], 'win_rate', '.1%')

    with col3:
        st.metric(
            label="Total Staked",
            value=f"${stats['total_staked']:,.2f}",
            delta=f"Avg: ${stats['avg_bet']:,.2f}"
        )
        format_metric_with_alert("Sharpe Ratio", stats['sharpe_ratio'], 'sharpe_ratio', '.2f')

    with col4:
        st.metric(
            label="Calibration (Brier)",
            value=f"{brier_score:.3f}",
            delta="Lower is better",
            delta_color="inverse"
        )
        format_metric_with_alert("CLV", stats['avg_clv'], 'clv', '.1%')

    st.markdown("---")

    # ========================================================================
    # Risk Metrics
    # ========================================================================

    st.header("📉 Risk Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        max_dd_pct = abs(stats['max_drawdown']) / stats['bankroll'] if stats['bankroll'] > 0 else 0
        format_metric_with_alert("Max Drawdown", max_dd_pct, 'max_drawdown', '.1%')

    with col2:
        st.markdown(f"**Avg Edge:** {stats['avg_edge']*100:.1f}%")

    with col3:
        st.markdown(f"**Current Streak:** {stats['current_streak']:+d}")

    st.markdown("---")

    # ========================================================================
    # Interactive Charts
    # ========================================================================

    st.header("📈 Performance Charts")

    # Row 1: Bankroll and Cumulative P/L
    col1, col2 = st.columns(2)

    with col1:
        fig_bankroll = plot_bankroll_over_time(bankroll_history)
        st.plotly_chart(fig_bankroll, use_container_width=True)

    with col2:
        fig_pl = plot_cumulative_pl(all_bets)
        st.plotly_chart(fig_pl, use_container_width=True)

    # Row 2: Win Rate and Bet Distribution
    col1, col2 = st.columns(2)

    with col1:
        fig_winrate = plot_win_rate_rolling(all_bets, window=10)
        st.plotly_chart(fig_winrate, use_container_width=True)

    with col2:
        fig_dist = plot_bet_distribution(all_bets)
        st.plotly_chart(fig_dist, use_container_width=True)

    st.markdown("---")

    # ========================================================================
    # Calibration Monitoring
    # ========================================================================

    st.header("🎯 Calibration Monitoring")

    col1, col2 = st.columns(2)

    with col1:
        fig_cal = plot_calibration_curve(calibrator)
        st.plotly_chart(fig_cal, use_container_width=True)

    with col2:
        st.subheader("Calibration Metrics")
        format_metric_with_alert("Brier Score", brier_score, 'brier_score', '.4f')
        st.markdown(f"**Log Loss:** {log_loss:.4f}")

        if calibrator and calibrator.calibration_db:
            num_records = len(calibrator.calibration_db.get_all_records())
            st.markdown(f"**Total Predictions:** {num_records}")

        st.markdown("---")
        st.markdown("""
        **Calibration Quality:**
        - Brier < 0.10: Excellent
        - Brier < 0.15: Good
        - Brier < 0.20: Acceptable
        - Brier > 0.20: Poor (don't bet!)
        """)

    st.markdown("---")

    # ========================================================================
    # Recent Bets
    # ========================================================================

    st.header("🎲 Recent Bets")

    # Show last 20 bets
    recent_bets = sorted(all_bets, key=lambda x: x.timestamp, reverse=True)[:20]

    if recent_bets:
        bet_data = []
        for bet in recent_bets:
            bet_data.append({
                'Date': bet.timestamp.strftime('%Y-%m-%d %H:%M'),
                'Game': bet.game_id,
                'Type': bet.bet_type.value,
                'Amount': f"${bet.amount:.2f}",
                'Odds': f"{bet.odds:.2f}",
                'Edge': f"{bet.edge*100:.1f}%",
                'Status': bet.status.value,
                'P/L': f"${bet.profit_loss:.2f}" if bet.profit_loss else "-",
                'CLV': f"{bet.clv*100:.1f}%" if bet.clv else "-"
            })

        df_bets = pd.DataFrame(bet_data)

        # Color-code by status
        def highlight_status(row):
            if row['Status'] == 'won':
                return ['background-color: #d4edda'] * len(row)
            elif row['Status'] == 'lost':
                return ['background-color: #f8d7da'] * len(row)
            else:
                return [''] * len(row)

        styled_df = df_bets.style.apply(highlight_status, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
    else:
        st.info("No bets recorded yet")

    st.markdown("---")

    # ========================================================================
    # Footer
    # ========================================================================

    st.markdown("---")
    st.markdown("""
    **Dashboard Controls:**
    - Use sidebar to enable auto-refresh
    - Click "Refresh Now" for manual updates
    - All charts are interactive (zoom, pan, hover)

    **Alert Thresholds:**
    - 🔴 Critical: Requires immediate attention
    - 🟡 Warning: Monitor closely
    - 🟢 Healthy: System performing well
    """)


if __name__ == "__main__":
    main()