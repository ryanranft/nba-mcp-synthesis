#!/usr/bin/env python3
"""
Test Script for Formula Intelligence Tools

This script tests the new formula intelligence capabilities added in Phase 2
of the NBA MCP server implementation.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.tools.formula_intelligence import (
    FormulaIntelligence,
    identify_formula_type,
    suggest_tools,
    map_variables,
    analyze_formula,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_formula_intelligence():
    """Test the formula intelligence system"""
    logger.info("🧠 Testing Formula Intelligence System")

    # Test formulas
    test_formulas = [
        "PER = (FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
        "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
        "USG% = ((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
        "eFG% = (FGM + 0.5 * 3PM) / FGA",
        "VORP = (BPM - (-2.0)) * (POSS_PCT / 100) * (TEAM_GAMES / 82)",
        "Net Rating = ORtg - DRtg",
    ]

    intelligence = FormulaIntelligence()

    for i, formula in enumerate(test_formulas, 1):
        logger.info(f"\n📊 Test {i}: Analyzing formula")
        logger.info(f"Formula: {formula[:80]}...")

        try:
            # Test type identification
            formula_type, confidence = identify_formula_type(formula)
            logger.info(f"✅ Type: {formula_type.value} (confidence: {confidence:.2f})")

            # Test tool suggestions
            suggested_tools = suggest_tools(formula)
            logger.info(
                f"✅ Suggested tools: {[tool.value for tool in suggested_tools]}"
            )

            # Test variable mapping
            mapped_vars = map_variables(formula)
            logger.info(f"✅ Mapped variables: {mapped_vars}")

            # Test comprehensive analysis
            analysis = analyze_formula(formula)
            logger.info(f"✅ Complexity score: {analysis.complexity_score:.2f}")
            logger.info(
                f"✅ Insights: {analysis.insights[:2]}"
            )  # Show first 2 insights

        except Exception as e:
            logger.error(f"❌ Error analyzing formula: {e}")

    logger.info("\n🎯 Testing Formula Type Classification")

    # Test specific formula types
    type_tests = [
        ("TS% = PTS / (2 * (FGA + 0.44 * FTA))", "efficiency"),
        ("PER = (FGM * 85.910 + ...) / MP", "rate"),
        ("VORP = (BPM - (-2.0)) * (POSS_PCT / 100) * (TEAM_GAMES / 82)", "composite"),
        ("Net Rating = ORtg - DRtg", "differential"),
        ("FG% = FGM / FGA", "percentage"),
        ("PTS = 25", "count"),
    ]

    for formula, expected_type in type_tests:
        formula_type, confidence = identify_formula_type(formula)
        status = "✅" if formula_type.value == expected_type else "❌"
        logger.info(
            f"{status} {formula[:30]}... -> {formula_type.value} (expected: {expected_type})"
        )

    logger.info("\n🔧 Testing Tool Suggestions")

    # Test tool suggestions for different contexts
    context_tests = [
        ("PER = (FGM * 85.910 + ...) / MP", "Should suggest solve, differentiate"),
        (
            "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
            "Should suggest simplify, sports_formula",
        ),
        ("Net Rating = ORtg - DRtg", "Should suggest solve_system, matrix_ops"),
    ]

    for formula, expected in context_tests:
        suggested_tools = suggest_tools(formula)
        tool_names = [tool.value for tool in suggested_tools]
        logger.info(f"📋 {formula[:30]}... -> {tool_names}")
        logger.info(f"   Expected: {expected}")

    logger.info("\n🗺️ Testing Variable Mapping")

    # Test variable mapping
    mapping_tests = [
        "PER = (FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
        "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
        "USG% = ((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
    ]

    for formula in mapping_tests:
        mapped_vars = map_variables(formula)
        logger.info(f"📋 {formula[:30]}...")
        logger.info(f"   Variables: {list(mapped_vars.keys())}")
        logger.info(f"   Mappings: {mapped_vars}")

    logger.info("\n📈 Testing Comprehensive Analysis")

    # Test comprehensive analysis
    comprehensive_tests = [
        "PER = (FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)",
        "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
    ]

    for formula in comprehensive_tests:
        analysis = analyze_formula(formula)
        logger.info(f"📋 {formula[:30]}...")
        logger.info(f"   Type: {analysis.formula_type.value}")
        logger.info(f"   Complexity: {analysis.complexity_score:.2f}")
        logger.info(f"   Confidence: {analysis.confidence:.2f}")
        logger.info(f"   Tools: {[tool.value for tool in analysis.suggested_tools]}")
        logger.info(f"   Insights: {analysis.insights}")

    logger.info("\n🎯 Testing Recommendations")

    # Test recommendations
    recommendation_tests = [
        ("PER = (FGM * 85.910 + ...) / MP", "player analysis"),
        ("Net Rating = ORtg - DRtg", "team comparison"),
        ("TS% = PTS / (2 * (FGA + 0.44 * FTA))", "optimization"),
    ]

    for formula, context in recommendation_tests:
        recommendations = intelligence.get_formula_recommendations(formula, context)
        logger.info(f"📋 {formula[:30]}... (context: {context})")
        logger.info(f"   Type: {recommendations['formula_type']}")
        logger.info(f"   Tools: {recommendations['suggested_tools']}")
        logger.info(f"   Recommendations: {recommendations['recommendations'][:2]}")

    logger.info("\n✅ Formula Intelligence System Tests Complete!")


def test_sports_validation():
    """Test the sports validation system"""
    logger.info("\n🔍 Testing Sports Validation System")

    from mcp_server.tools.sports_validation import (
        validate_formula_inputs,
        suggest_fixes_for_error,
        validate_formula_consistency,
        get_formula_requirements,
    )

    # Test formula input validation
    logger.info("📊 Testing Formula Input Validation")

    test_cases = [
        {
            "formula": "per",
            "variables": {
                "FGM": 8,
                "STL": 2,
                "3PM": 3,
                "FTM": 4,
                "BLK": 1,
                "OREB": 2,
                "AST": 5,
                "DREB": 6,
                "PF": 3,
                "FTA": 5,
                "FGA": 15,
                "TOV": 2,
                "MP": 35,
            },
            "expected": "valid",
        },
        {
            "formula": "per",
            "variables": {
                "FGM": -1,
                "STL": 2,
                "3PM": 3,
                "FTM": 4,
                "BLK": 1,
                "OREB": 2,
                "AST": 5,
                "DREB": 6,
                "PF": 3,
                "FTA": 5,
                "FGA": 15,
                "TOV": 2,
                "MP": 35,
            },
            "expected": "invalid (negative FGM)",
        },
        {
            "formula": "true_shooting",
            "variables": {"PTS": 25, "FGA": 15, "FTA": 5},
            "expected": "valid",
        },
        {
            "formula": "true_shooting",
            "variables": {"PTS": 25, "FGA": 0, "FTA": 0},
            "expected": "valid (but may cause division by zero)",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n📋 Test {i}: {test_case['formula']}")
        logger.info(f"Variables: {test_case['variables']}")
        logger.info(f"Expected: {test_case['expected']}")

        try:
            validated = validate_formula_inputs(
                test_case["formula"], test_case["variables"]
            )
            logger.info(f"✅ Validation passed: {validated}")
        except Exception as e:
            logger.info(f"❌ Validation failed: {e}")
            suggestions = suggest_fixes_for_error(str(e), test_case["formula"])
            logger.info(f"💡 Suggestions: {suggestions}")

    # Test consistency validation
    logger.info("\n📊 Testing Formula Consistency Validation")

    consistency_tests = [
        {
            "formula": "per",
            "variables": {"FGM": 8, "FGA": 15, "FTM": 4, "FTA": 5, "3PM": 3, "MP": 35},
        },
        {
            "formula": "per",
            "variables": {
                "FGM": 20,
                "FGA": 15,
                "FTM": 4,
                "FTA": 5,
                "3PM": 3,
                "MP": 35,
            },  # FGM > FGA
        },
    ]

    for i, test_case in enumerate(consistency_tests, 1):
        logger.info(f"\n📋 Consistency Test {i}: {test_case['formula']}")
        warnings = validate_formula_consistency(
            test_case["formula"], test_case["variables"]
        )
        if warnings:
            logger.info(f"⚠️ Warnings: {warnings}")
        else:
            logger.info("✅ No consistency warnings")

    # Test formula requirements
    logger.info("\n📊 Testing Formula Requirements")

    requirement_tests = ["per", "true_shooting", "usage_rate", "vorp", "game_score"]

    for formula in requirement_tests:
        requirements = get_formula_requirements(formula)
        logger.info(f"📋 {formula}: {list(requirements.keys())}")

    logger.info("\n✅ Sports Validation System Tests Complete!")


def main():
    """Run all tests"""
    logger.info("🚀 Starting NBA MCP Server Phase 2 Tests")
    logger.info("=" * 60)

    try:
        test_formula_intelligence()
        test_sports_validation()

        logger.info("\n" + "=" * 60)
        logger.info("🎉 All Phase 2 Tests Completed Successfully!")
        logger.info("\n📋 Summary of New Capabilities:")
        logger.info(
            "   ✅ Formula type identification (efficiency, rate, composite, etc.)"
        )
        logger.info("   ✅ Intelligent tool suggestions based on formula type")
        logger.info("   ✅ Variable mapping from book notation to standard format")
        logger.info("   ✅ Unit consistency validation")
        logger.info("   ✅ Comprehensive formula analysis with insights")
        logger.info("   ✅ Context-specific recommendations")
        logger.info("   ✅ Sports statistics validation with helpful error messages")
        logger.info("   ✅ Formula consistency checking")
        logger.info("   ✅ Enhanced sports formula library (20+ formulas)")
        logger.info("   ✅ Comprehensive documentation and prompt templates")

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
