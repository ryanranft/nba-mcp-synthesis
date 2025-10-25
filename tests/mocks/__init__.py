"""
Mock services for testing NBA MCP data validation infrastructure.

Provides mock implementations of external dependencies to enable
unit testing without requiring actual services.

Phase 10A Week 2 - Agent 4 - Advanced Integrations
"""

__all__ = [
    # Great Expectations mocks
    "MockDataContext",
    "MockCheckpoint",
    "MockValidationResult",
    "MockExpectationSuite",
    # Data source mocks
    "MockPostgresConnection",
    "MockS3Client",
    "MockNBAApi",
    # Sample data generators
    "generate_sample_player_stats",
    "generate_sample_game_data",
    "generate_sample_team_data",
]
