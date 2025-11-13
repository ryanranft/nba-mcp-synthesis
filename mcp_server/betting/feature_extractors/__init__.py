"""
Feature Extractors for NBA Betting Predictions

This package contains specialized feature extractors that enhance the base
ensemble model with additional data sources from nba-simulator-aws.

Modules:
- rest_fatigue: Rest days, back-to-backs, schedule density
- lineup_features: Player availability, lineup chemistry
- line_movement: Betting line movement tracking
- pace_style: Team playing style matchups

Author: NBA MCP Synthesis Team
Date: 2025-01-05
"""

from .rest_fatigue import RestFatigueExtractor

__all__ = [
    "RestFatigueExtractor",
]
