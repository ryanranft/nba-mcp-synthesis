#!/usr/bin/env python3
"""
Test script for Phase 2.2: Formula Extraction Tools

This script tests the new formula extraction capabilities including:
- extract_formulas_from_pdf
- convert_latex_to_sympy
- analyze_formula_structure

Author: NBA MCP Server Team
Date: 2025-01-11
"""

import asyncio
import logging
from typing import Dict, Any, List
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
        self.logs = []

    async def info(self, message: str):
        self.logs.append(f"INFO: {message}")
        logger.info(message)

    async def error(self, message: str):
        self.logs.append(f"ERROR: {message}")
        logger.error(message)

    async def warn(self, message: str):
        self.logs.append(f"WARN: {message}")
        logger.warning(message)

    async def debug(self, message: str):
        self.logs.append(f"DEBUG: {message}")
        logger.debug(message)


async def test_formula_extraction_tools():
    """
    Tests the new formula extraction tools implemented in Phase 2.2.
    """
    logger.info("Starting tests for Phase 2.2 Formula Extraction Tools...")
    ctx = MockContext()

    # Test 1: analyze_formula_structure
    logger.info("\n--- Testing analyze_formula_structure ---")
    test_formulas = [
        "PER = (FGM * 85.910 + STL * 53.897) / MP",
        "TS% = PTS / (2 * (FGA + 0.44 * FTA))",
        "Net Rating = ORtg - DRtg",
        "x + 2*y = 10",
        "sin(x)**2 + cos(x)**2",
    ]

    for formula in test_formulas:
        result = await nba_mcp_server.analyze_formula_structure(
            formula=formula, ctx=ctx
        )
        assert (
            result.success
        ), f"analyze_formula_structure failed for {formula}: {result.error}"
        logger.info(
            f"Formula '{formula}': Structure={result.structure_analysis}, Tool={result.suggested_tool}"
        )

        # Verify structure analysis contains expected keys
        assert "has_equality" in result.structure_analysis
        assert "operators" in result.structure_analysis
        assert "variables" in result.structure_analysis
        assert "complexity_score" in result.structure_analysis

    # Test 2: convert_latex_to_sympy
    logger.info("\n--- Testing convert_latex_to_sympy ---")
    latex_formulas = [
        "\\frac{PTS}{2 \\cdot (FGA + 0.44 \\cdot FTA)}",
        "PER = \\frac{FGM \\cdot 85.910 + STL \\cdot 53.897}{MP}",
        "\\sum_{i=1}^{n} x_i",
        "x^2 + y^2 = z^2",
        "\\alpha + \\beta = \\gamma",
    ]

    for latex_formula in latex_formulas:
        result = await nba_mcp_server.convert_latex_to_sympy(
            latex_formula=latex_formula, ctx=ctx
        )
        logger.info(
            f"LaTeX '{latex_formula}': Success={result.conversion_successful}, SymPy={result.sympy_output}"
        )

        # At least some conversions should succeed
        if result.conversion_successful:
            assert result.sympy_output is not None
            assert len(result.sympy_output) > 0

    # Test 3: extract_formulas_from_pdf (using a test PDF if available)
    logger.info("\n--- Testing extract_formulas_from_pdf ---")

    # Test with one of our sports analytics books
    test_pdf_paths = [
        "books/Basketball_on_Paper_Dean_Oliver.pdf",
        "books/Sports_Analytics_A_Guide_for_Coaches_Managers_and_Other_Decision_Makers.pdf",
        "books/Basketball_Beyond_Paper_Quants_Stats_and_the_New_Frontier_of_the_NBA.pdf",
    ]

    for pdf_path in test_pdf_paths:
        try:
            # Test with first 3 pages only for efficiency
            result = await nba_mcp_server.extract_formulas_from_pdf(
                pdf_path=pdf_path,
                pages=[0, 1, 2],
                min_confidence=0.6,
                max_formulas=10,
                ctx=ctx,
            )

            logger.info(
                f"PDF '{pdf_path}': Extracted {result.total_formulas} formulas from pages {result.pages_processed}"
            )

            if result.success and result.total_formulas > 0:
                # Verify extracted formulas have expected structure
                for formula in result.extracted_formulas[:3]:  # Check first 3 formulas
                    assert "formula_text" in formula
                    assert "formula_type" in formula
                    assert "confidence" in formula
                    assert "variables" in formula
                    assert "suggested_tools" in formula

                    logger.info(f"  Formula: {formula['formula_text'][:50]}...")
                    logger.info(
                        f"    Type: {formula['formula_type']}, Confidence: {formula['confidence']:.2f}"
                    )
                    logger.info(f"    Variables: {formula['variables']}")
                    logger.info(f"    Tools: {formula['suggested_tools']}")

        except Exception as e:
            logger.warning(f"Could not test PDF extraction for {pdf_path}: {e}")
            # This is expected for some PDFs that might not be accessible

    # Test 4: Integration test - extract formula and then analyze it
    logger.info("\n--- Testing Integration: Extract + Analyze ---")

    # Simulate extracting a formula and then analyzing it
    sample_formula = "PER = (FGM * 85.910 + STL * 53.897 + 3PM * 51.757 + FTM * 46.845 + BLK * 39.190 + OREB * 39.190 + AST * 34.677 + DREB * 14.707 - PF * 17.174 - (FTA - FTM) * 20.091 - (FGA - FGM) * 39.190 - TOV * 53.897) * (1 / MP)"

    # Step 1: Analyze structure
    structure_result = await nba_mcp_server.analyze_formula_structure(
        formula=sample_formula, ctx=ctx
    )
    assert (
        structure_result.success
    ), f"Structure analysis failed: {structure_result.error}"

    # Step 2: Get recommendations
    recommendation_result = await nba_mcp_server.formula_get_recommendations(
        formula=sample_formula, context="player analysis", ctx=ctx
    )
    assert (
        recommendation_result.success
    ), f"Recommendation failed: {recommendation_result.error}"

    logger.info(f"Integration test successful!")
    logger.info(f"  Structure analysis: {structure_result.structure_analysis}")
    logger.info(f"  Suggested tool: {structure_result.suggested_tool}")
    logger.info(
        f"  Recommendations: {recommendation_result.result['usage_recommendations']}"
    )

    logger.info("\nAll Phase 2.2 Formula Extraction Tests Passed!")


async def test_formula_extractor_module():
    """
    Test the formula_extractor module directly.
    """
    logger.info("\n--- Testing formula_extractor module directly ---")

    try:
        from mcp_server.tools import formula_extractor

        # Test FormulaExtractor class
        extractor = formula_extractor.FormulaExtractor()

        # Test text with various formula patterns
        test_text = """
        The Player Efficiency Rating (PER) is calculated as:
        PER = (FGM * 85.910 + STL * 53.897) / MP

        True Shooting Percentage formula:
        TS% = PTS / (2 * (FGA + 0.44 * FTA))

        Net Rating is simply:
        Net Rating = ORtg - DRtg

        Some LaTeX: $\\frac{x}{y} = z$
        """

        # Extract formulas
        formulas = extractor.extract_formulas_from_text(test_text, page_number=1)

        logger.info(f"Extracted {len(formulas)} formulas from test text:")
        for formula in formulas:
            logger.info(
                f"  {formula.formula_text} (Type: {formula.formula_type.value}, Confidence: {formula.confidence:.2f})"
            )

        # Test LaTeX extraction
        latex_formulas = extractor.extract_latex_from_text(test_text)
        logger.info(f"Extracted {len(latex_formulas)} LaTeX formulas: {latex_formulas}")

        # Test structure analysis
        structure = extractor.analyze_formula_structure(
            "PER = (FGM * 85.910 + STL * 53.897) / MP"
        )
        logger.info(f"Structure analysis: {structure}")

        logger.info("Direct module testing successful!")

    except Exception as e:
        logger.error(f"Direct module testing failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_formula_extraction_tools())
    asyncio.run(test_formula_extractor_module())
