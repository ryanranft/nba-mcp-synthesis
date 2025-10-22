#!/usr/bin/env python3
"""
Categorize MCP Tools

Analyzes all tools in mcp_server/tools/ and suggests categorization.
"""

import json
from pathlib import Path
from collections import defaultdict

# Tool categorization based on function names and patterns
CATEGORIES = {
    "data": [
        "query_database", "list_tables", "get_table_schema",
        "database", "sql", "query"
    ],
    "books": [
        "list_books", "read_book", "search_books",
        "get_epub", "read_epub", "epub",
        "get_pdf", "read_pdf", "search_pdf", "pdf"
    ],
    "nba": [
        "list_games", "list_players",
        "player_efficiency", "true_shooting", "usage_rate",
        "offensive_rating", "defensive_rating", "pace",
        "four_factors", "turnover_percentage", "rebound_percentage",
        "assist_percentage", "steal_percentage", "block_percentage",
        "win_shares", "box_plus_minus", "nba_"
    ],
    "math": [
        "math_add", "math_subtract", "math_multiply", "math_divide",
        "math_sum", "math_round", "math_modulo"
    ],
    "statistics": [
        "stats_mean", "stats_median", "stats_mode",
        "stats_min_max", "stats_variance", "stats_summary",
        "stats_correlation", "stats_covariance",
        "stats_percent_change", "stats_growth_rate", "stats_volatility",
        "moving_average", "exponential_moving_average", "trend_detection"
    ],
    "algebra": [
        "algebra_solve", "algebra_simplify", "algebra_differentiate",
        "algebra_integrate", "algebra_matrix", "algebra_system",
        "algebra_latex", "algebra_sports_formula",
        "formula_identify", "formula_suggest"
    ],
    "ml_clustering": [
        "ml_kmeans", "ml_hierarchical", "ml_euclidean", "ml_cosine"
    ],
    "ml_classification": [
        "ml_knn", "ml_naive_bayes", "ml_decision_tree",
        "ml_random_forest", "ml_logistic"
    ],
    "ml_anomaly": [
        "ml_zscore", "ml_isolation_forest", "ml_local_outlier"
    ],
    "ml_preprocessing": [
        "ml_normalize", "ml_feature_importance"
    ],
    "ml_evaluation": [
        "ml_accuracy", "ml_precision_recall", "ml_confusion_matrix",
        "ml_roc_auc", "ml_classification_report", "ml_log_loss",
        "ml_mse_rmse_mae", "ml_r2_score", "ml_mape"
    ],
    "ml_validation": [
        "ml_k_fold", "ml_stratified_k_fold", "ml_cross_validate",
        "ml_compare_models", "ml_paired_ttest", "ml_grid_search"
    ],
    "ml_regression": [
        "stats_linear_regression", "stats_predict"
    ],
    "s3": [
        "list_s3_files", "s3_"
    ]
}

def categorize_tool(tool_name: str) -> str:
    """Categorize a tool based on its name."""
    tool_lower = tool_name.lower()

    for category, patterns in CATEGORIES.items():
        for pattern in patterns:
            if pattern in tool_lower:
                return category

    return "uncategorized"

def main():
    """Main categorization function."""
    tools_dir = Path("mcp_server/tools")

    if not tools_dir.exists():
        print(f"❌ Directory not found: {tools_dir}")
        return

    # Get all Python files
    tool_files = sorted([f for f in tools_dir.glob("*.py") if f.name != "__init__.py"])

    print(f"📊 Categorizing {len(tool_files)} tool files...")
    print()

    # Categorize all tools
    by_category = defaultdict(list)
    for tool_file in tool_files:
        category = categorize_tool(tool_file.stem)
        by_category[category].append(tool_file.stem)

    # Print summary
    print("=" * 70)
    print("MCP TOOLS CATEGORIZATION")
    print("=" * 70)
    print()

    print(f"Total Tools: {len(tool_files)}")
    print()

    print("Distribution by Category:")
    print("-" * 70)
    for category in sorted(by_category.keys()):
        tools = by_category[category]
        percentage = (len(tools) / len(tool_files)) * 100
        print(f"  {category:20s}: {len(tools):3d} ({percentage:5.1f}%)")
    print()

    # Show details for each category
    print("=" * 70)
    print("CATEGORY DETAILS")
    print("=" * 70)
    print()

    for category in sorted(by_category.keys()):
        tools = sorted(by_category[category])
        print(f"{category.upper()} ({len(tools)} tools)")
        print("-" * 70)
        for tool in tools:
            print(f"  - {tool}")
        print()

    # Suggested directory structure
    print("=" * 70)
    print("SUGGESTED DIRECTORY STRUCTURE")
    print("=" * 70)
    print()
    print("mcp_server/tools/")
    for category in sorted(by_category.keys()):
        if category == "uncategorized":
            continue
        tools = by_category[category]
        print(f"├── {category}/")
        for i, tool in enumerate(sorted(tools)):
            prefix = "└──" if i == len(tools) - 1 else "├──"
            print(f"│   {prefix} {tool}.py")

    if by_category["uncategorized"]:
        print("├── uncategorized/ (needs review)")
        for i, tool in enumerate(sorted(by_category["uncategorized"])):
            prefix = "└──" if i == len(by_category["uncategorized"]) - 1 else "├──"
            print(f"│   {prefix} {tool}.py")

    print()

    # Save results
    output_file = Path("TOOL_CATEGORIZATION_RESULTS.json")
    with open(output_file, 'w') as f:
        json.dump({
            "total": len(tool_files),
            "by_category": {k: len(v) for k, v in by_category.items()},
            "details": {k: sorted(v) for k, v in by_category.items()}
        }, f, indent=2)

    print(f"📄 Detailed results saved to: {output_file}")
    print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    categorized = len(tool_files) - len(by_category["uncategorized"])
    percentage = (categorized / len(tool_files)) * 100
    print(f"Categorized: {categorized}/{len(tool_files)} ({percentage:.1f}%)")
    print(f"Uncategorized: {len(by_category['uncategorized'])}")
    print(f"Categories: {len(by_category) - (1 if 'uncategorized' in by_category else 0)}")
    print("=" * 70)

if __name__ == "__main__":
    main()




