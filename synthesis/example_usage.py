"""
Example usage of NBA MCP Synthesis System
Demonstrates how to use the multi-model synthesis with MCP context
"""

import asyncio
import logging
from synthesis import synthesize_with_mcp_context, quick_synthesis

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def example_sql_optimization():
    """Example: SQL optimization with MCP context"""
    print("\n" + "=" * 80)
    print("Example 1: SQL Optimization")
    print("=" * 80)

    sql_query = """
    SELECT p.player_name, AVG(ps.points) as avg_points
    FROM player_stats ps
    JOIN players p ON ps.player_id = p.id
    WHERE ps.season = '2023-24'
    GROUP BY p.player_name
    ORDER BY avg_points DESC
    """

    result = await synthesize_with_mcp_context(
        user_input="Optimize this SQL query for better performance",
        selected_code=sql_query,
        query_type="sql_optimization",
        output_dir="synthesis_output",
    )

    print(f"\nStatus: {result['status']}")
    print(f"Models used: {', '.join(result['models_used'])}")
    print(f"Total cost: ${result['total_cost']:.4f}")
    print(f"\nOptimized solution:\n{result.get('final_code', 'N/A')}")


async def example_statistical_analysis():
    """Example: Statistical analysis request"""
    print("\n" + "=" * 80)
    print("Example 2: Statistical Analysis")
    print("=" * 80)

    result = await synthesize_with_mcp_context(
        user_input="Calculate the correlation between player height and average points per game, including statistical significance",
        query_type="statistical_analysis",
        output_dir="synthesis_output",
    )

    print(f"\nStatus: {result['status']}")
    print(f"Total tokens: {result['total_tokens']}")
    print(f"\nAnalysis:\n{result.get('final_explanation', 'N/A')[:500]}...")


async def example_etl_generation():
    """Example: ETL pipeline generation"""
    print("\n" + "=" * 80)
    print("Example 3: ETL Pipeline Generation")
    print("=" * 80)

    result = await synthesize_with_mcp_context(
        user_input="Generate an ETL pipeline to extract player stats from S3, transform them to calculate advanced metrics, and load into player_advanced_stats table",
        query_type="etl_generation",
        output_dir="synthesis_output",
    )

    print(f"\nStatus: {result['status']}")
    print(f"Execution time: {result['execution_time_seconds']:.2f}s")
    print(f"\nETL Code:\n{result.get('final_code', 'N/A')[:500]}...")


async def example_code_debugging():
    """Example: Code debugging with error context"""
    print("\n" + "=" * 80)
    print("Example 4: Code Debugging")
    print("=" * 80)

    buggy_code = """
    def calculate_win_percentage(games_data):
        wins = sum([1 for g in games_data if g['result'] == 'W'])
        total = len(games_data)
        return wins / total * 100
    """

    result = await synthesize_with_mcp_context(
        user_input="This function crashes with ZeroDivisionError when games_data is empty. Fix it and add proper error handling.",
        selected_code=buggy_code,
        query_type="debugging",
        output_dir="synthesis_output",
    )

    print(f"\nStatus: {result['status']}")
    print(f"\nFixed code:\n{result.get('final_code', 'N/A')}")


async def example_quick_synthesis():
    """Example: Quick synthesis for simple requests"""
    print("\n" + "=" * 80)
    print("Example 5: Quick Synthesis")
    print("=" * 80)

    solution = await quick_synthesis(
        prompt="Write a Python function to calculate player efficiency rating (PER) from basic stats"
    )

    print(f"\nSolution:\n{solution}")


async def example_auto_detect():
    """Example: Auto-detect query type"""
    print("\n" + "=" * 80)
    print("Example 6: Auto-detect Query Type")
    print("=" * 80)

    result = await synthesize_with_mcp_context(
        user_input="The SELECT query on game_logs table is taking too long. It has a WHERE clause on game_date and team_id.",
        # query_type not specified - will auto-detect
        output_dir="synthesis_output",
    )

    print(f"\nDetected query type: {result['query_type']}")
    print(f"Status: {result['status']}")


async def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("NBA MCP Synthesis System - Example Usage")
    print("=" * 80)

    # Run examples
    try:
        await example_sql_optimization()
        await example_statistical_analysis()
        await example_etl_generation()
        await example_code_debugging()
        await example_quick_synthesis()
        await example_auto_detect()

        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
