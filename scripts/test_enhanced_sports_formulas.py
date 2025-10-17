"""
Test script for Enhanced Sports Formula Library

Author: NBA MCP Server Team
Date: October 13, 2025
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP, Context
from mcp_server.fastmcp_server import mcp as nba_mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Mock Context for testing
class MockContext(Context):
    def __init__(self):
        super().__init__(agent_id="test_agent", conversation_id="test_conv")
        self._logs = []

    async def info(self, message: str):
        self._logs.append(f"INFO: {message}")
        logger.info(message)

    async def error(self, message: str):
        self._logs.append(f"ERROR: {message}")
        logger.error(message)

    async def warn(self, message: str):
        self._logs.append(f"WARN: {message}")
        logger.warning(message)

    async def debug(self, message: str):
        self._logs.append(f"DEBUG: {message}")
        logger.debug(message)


async def test_enhanced_sports_formulas():
    """
    Test the enhanced sports formula library with new advanced metrics.
    """
    logger.info("Starting tests for Enhanced Sports Formula Library...")
    ctx = MockContext()

    try:
        # Test 1: Advanced Player Metrics - VORP
        logger.info("\n--- Testing VORP (Value Over Replacement Player) ---")
        vorp_params = {
            "formula_name": "vorp",
            "BPM": 5.2,
            "POSS_PCT": 25.0,
            "TEAM_GAMES": 82,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": vorp_params}
        )
        result = result_tuple[1]
        logger.info(f"VORP calculation: {result.get('result', 'N/A')}")

        # Test 2: Win Shares per 48
        logger.info("\n--- Testing Win Shares per 48 ---")
        ws_per_48_params = {
            "formula_name": "ws_per_48",
            "WS": 8.5,
            "TEAM_GAMES": 82,
            "MP": 2500,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": ws_per_48_params}
        )
        result = result_tuple[1]
        logger.info(f"WS/48 calculation: {result.get('result', 'N/A')}")

        # Test 3: BPM Components
        logger.info("\n--- Testing Offensive BPM ---")
        obpm_params = {
            "formula_name": "bpm_offensive",
            "Raw_OBPM": 3.5,
            "Pace_Adjustment": 1.02,
            "League_Avg_OBPM": 0.0,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": obpm_params}
        )
        result = result_tuple[1]
        logger.info(f"Offensive BPM calculation: {result.get('result', 'N/A')}")

        # Test 4: Shooting Analytics - Corner 3PT%
        logger.info("\n--- Testing Corner 3-Point Percentage ---")
        corner_3pt_params = {
            "formula_name": "corner_3pt_pct",
            "Corner_3PM": 45,
            "Corner_3PA": 100,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": corner_3pt_params}
        )
        result = result_tuple[1]
        logger.info(f"Corner 3PT% calculation: {result.get('result', 'N/A')}")

        # Test 5: Defensive Metrics - Defensive Win Shares
        logger.info("\n--- Testing Defensive Win Shares ---")
        dws_params = {
            "formula_name": "defensive_win_shares",
            "DRtg": 105.5,
            "MP": 2500,
            "TEAM_PACE": 98.5,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": dws_params}
        )
        result = result_tuple[1]
        logger.info(f"Defensive Win Shares calculation: {result.get('result', 'N/A')}")

        # Test 6: Team Metrics - Net Rating
        logger.info("\n--- Testing Net Rating ---")
        net_rating_params = {"formula_name": "net_rating", "ORtg": 115.2, "DRtg": 108.7}
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": net_rating_params}
        )
        result = result_tuple[1]
        logger.info(f"Net Rating calculation: {result.get('result', 'N/A')}")

        # Test 7: Situational Metrics - Clutch Performance
        logger.info("\n--- Testing Clutch Performance ---")
        clutch_params = {
            "formula_name": "clutch_performance",
            "Clutch_PTS": 45,
            "Clutch_AST": 8,
            "Clutch_REB": 12,
            "Clutch_MIN": 25,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": clutch_params}
        )
        result = result_tuple[1]
        logger.info(f"Clutch Performance calculation: {result.get('result', 'N/A')}")

        # Test 8: Percentage Metrics - Assist Percentage
        logger.info("\n--- Testing Assist Percentage ---")
        ast_pct_params = {
            "formula_name": "assist_percentage",
            "AST": 450,
            "TM_MP": 19680,
            "MP": 2500,
            "TM_FGM": 3200,
            "Player_FGM": 400,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": ast_pct_params}
        )
        result = result_tuple[1]
        logger.info(f"Assist Percentage calculation: {result.get('result', 'N/A')}")

        # Test 9: Advanced Analytics - Pace Adjusted Stats
        logger.info("\n--- Testing Pace Adjusted Statistics ---")
        pace_adj_params = {
            "formula_name": "pace_adjusted_stats",
            "Stat": 25.5,
            "League_Avg_Pace": 100.0,
            "Team_Pace": 98.5,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": pace_adj_params}
        )
        result = result_tuple[1]
        logger.info(f"Pace Adjusted Stats calculation: {result.get('result', 'N/A')}")

        # Test 10: Impact Metrics - Defensive Impact
        logger.info("\n--- Testing Defensive Impact ---")
        def_impact_params = {
            "formula_name": "defensive_impact",
            "Team_DRtg_Off": 110.5,
            "Team_DRtg_On": 105.2,
            "MP": 2500,
            "TEAM_MP": 19680,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": def_impact_params}
        )
        result = result_tuple[1]
        logger.info(f"Defensive Impact calculation: {result.get('result', 'N/A')}")

        # Test 11: Rebounding Metrics - Defensive Rebound Percentage
        logger.info("\n--- Testing Defensive Rebound Percentage ---")
        drb_pct_params = {
            "formula_name": "defensive_rebound_percentage",
            "DREB": 350,
            "TM_MP": 19680,
            "MP": 2500,
            "TM_DREB": 2800,
            "OPP_OREB": 850,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": drb_pct_params}
        )
        result = result_tuple[1]
        logger.info(
            f"Defensive Rebound Percentage calculation: {result.get('result', 'N/A')}"
        )

        # Test 12: Efficiency Metrics - Shooting Efficiency Differential
        logger.info("\n--- Testing Shooting Efficiency Differential ---")
        shooting_diff_params = {
            "formula_name": "shooting_efficiency_differential",
            "Player_eFG%": 0.575,
            "League_Avg_eFG%": 0.525,
        }
        result_tuple = await nba_mcp_server.call_tool(
            "algebra_sports_formula", {"params": shooting_diff_params}
        )
        result = result_tuple[1]
        logger.info(
            f"Shooting Efficiency Differential calculation: {result.get('result', 'N/A')}"
        )

        logger.info(
            "\n✅ All Enhanced Sports Formula Library Tests Completed Successfully!"
        )

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_enhanced_sports_formulas())
