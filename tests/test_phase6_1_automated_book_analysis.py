#!/usr/bin/env python3
"""
Test Suite for Phase 6.1: Automated Book Analysis Pipeline

Tests all components of the book analysis system including:
- Automated formula extraction from books
- Formula categorization and analysis
- Formula validation
- Database building and search capabilities
"""

import pytest
from mcp_server.tools import automated_book_analysis as aba
from mcp_server.tools.automated_book_analysis import (
    FormulaCategory,
    FormulaComplexity,
    ExtractedFormula,
)


@pytest.mark.asyncio
async def test_automated_book_analysis_module_instantiation():
    """Test the automated book analysis module imports and basic functionality."""
    # Test class instantiation
    analyzer = aba.AutomatedBookAnalyzer()

    assert analyzer is not None, "Should instantiate AutomatedBookAnalyzer"
    assert analyzer.formula_patterns is not None, "Should have formula patterns"
    assert analyzer.category_keywords is not None, "Should have category keywords"
    assert (
        analyzer.complexity_indicators is not None
    ), "Should have complexity indicators"


@pytest.mark.asyncio
async def test_formula_category_enum():
    """Test that formula category enum is accessible."""
    assert FormulaCategory.EFFICIENCY is not None, "Should have EFFICIENCY category"
    assert hasattr(FormulaCategory, "EFFICIENCY"), "Should have EFFICIENCY attribute"


@pytest.mark.asyncio
async def test_formula_complexity_enum():
    """Test that formula complexity enum is accessible."""
    assert FormulaComplexity.SIMPLE is not None, "Should have SIMPLE complexity"
    assert hasattr(FormulaComplexity, "SIMPLE"), "Should have SIMPLE attribute"


@pytest.mark.asyncio
async def test_formula_extraction_from_text():
    """Test automated formula extraction functionality."""
    analyzer = aba.AutomatedBookAnalyzer()

    # Test formula extraction with mock data
    mock_page_texts = [
        "Player Efficiency Rating = (PTS + REB + AST + STL + BLK - FGA - FTA - TOV) / MP * 100",
        "True Shooting Percentage = PTS / (2 * (FGA + 0.44 * FTA))",
        "Usage Rate = ((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
    ]

    formulas = analyzer._extract_formulas_from_text(
        page_texts=mock_page_texts,
        book_title="Test Book",
        book_author="Test Author",
        confidence_threshold=0.3,
    )

    assert len(formulas) > 0, "Should extract at least one formula"

    # Test confidence scoring
    for formula in formulas:
        assert formula.confidence_score >= 0.0, "Confidence should be >= 0"
        assert formula.confidence_score <= 1.0, "Confidence should be <= 1"


@pytest.mark.asyncio
async def test_formula_categorization():
    """Test formula categorization functionality."""
    analyzer = aba.AutomatedBookAnalyzer()

    # Create test formulas
    test_formulas = [
        ExtractedFormula(
            formula_id="test_1",
            formula_text="Player Efficiency Rating = (PTS + REB + AST) / MP",
            confidence_score=0.9,
        ),
        ExtractedFormula(
            formula_id="test_2",
            formula_text="Field Goal Percentage = FGM / FGA * 100",
            confidence_score=0.8,
        ),
        ExtractedFormula(
            formula_id="test_3",
            formula_text="Defensive Rating = Points Allowed / Possessions * 100",
            confidence_score=0.7,
        ),
    ]

    categorized_formulas = analyzer._categorize_formulas(test_formulas)

    # Test categorization
    assert len(categorized_formulas) == 3, "Should categorize all formulas"

    for formula in categorized_formulas:
        assert isinstance(
            formula.category, FormulaCategory
        ), "Should have valid category"
        assert isinstance(
            formula.complexity, FormulaComplexity
        ), "Should have valid complexity"
        assert formula.description is not None, "Should have description"


@pytest.mark.asyncio
async def test_formula_validation():
    """Test formula validation functionality."""
    # Test validation with mock formulas
    mock_formulas = [
        {
            "formula_id": "valid_1",
            "formula_text": "PER = (PTS + REB + AST) / MP",
            "formula_sympy": "PER",
            "confidence_score": 0.9,
        },
        {
            "formula_id": "invalid_1",
            "formula_text": "",
            "formula_sympy": None,
            "confidence_score": 0.0,
        },
        {
            "formula_id": "warning_1",
            "formula_text": "Complex Formula = sqrt(x^2 + y^2)",
            "formula_sympy": None,
            "confidence_score": 0.6,
        },
    ]

    result = aba.validate_extracted_formulas(mock_formulas)

    assert result["status"] == "success", "Validation should succeed"
    assert "validation_results" in result, "Should have validation results"
    assert "validation_statistics" in result, "Should have validation statistics"

    stats = result["validation_statistics"]
    assert stats["valid_formulas"] >= 0, "Should count valid formulas"
    assert stats["invalid_formulas"] >= 0, "Should count invalid formulas"
    assert stats["warning_formulas"] >= 0, "Should count warning formulas"


@pytest.mark.asyncio
async def test_analysis_statistics_calculation():
    """Test that statistics are calculated correctly."""
    analyzer = aba.AutomatedBookAnalyzer()

    test_formulas = [
        ExtractedFormula(
            formula_id="test_1",
            formula_text="Test 1",
            confidence_score=0.9,
        ),
        ExtractedFormula(
            formula_id="test_2",
            formula_text="Test 2",
            confidence_score=0.8,
        ),
    ]

    categorized_formulas = analyzer._categorize_formulas(test_formulas)
    stats = analyzer._calculate_analysis_statistics(categorized_formulas)

    assert "by_category" in stats, "Should have category stats"
    assert "by_complexity" in stats, "Should have complexity stats"
    assert "average_confidence" in stats, "Should have average confidence"


@pytest.mark.asyncio
async def test_integration_workflow():
    """Test the complete integration workflow: extract -> categorize -> validate."""
    analyzer = aba.AutomatedBookAnalyzer()

    # Mock page texts
    mock_page_texts = [
        "Player Efficiency Rating = (PTS + REB + AST + STL + BLK - FGA - FTA - TOV) / MP * 100",
        "True Shooting Percentage = PTS / (2 * (FGA + 0.44 * FTA))",
        "Usage Rate = ((FGA + 0.44 * FTA + TOV) * (TM_MP / 5)) / (MP * (TM_FGA + 0.44 * TM_FTA + TM_TOV)) * 100",
    ]

    # Step 1: Extract formulas
    formulas = analyzer._extract_formulas_from_text(
        page_texts=mock_page_texts,
        book_title="Integration Test Book",
        book_author="Test Author",
        confidence_threshold=0.3,
    )

    assert len(formulas) > 0, "Should extract formulas"

    # Step 2: Categorize formulas
    categorized_formulas = analyzer._categorize_formulas(formulas)

    assert len(categorized_formulas) == len(formulas), "Should categorize all formulas"

    # Step 3: Validate formulas
    formula_dicts = [aba.asdict(formula) for formula in categorized_formulas]
    validation_result = aba.validate_extracted_formulas(formula_dicts)

    assert validation_result["status"] == "success", "Validation should succeed"

    # Step 4: Verify statistics
    stats = analyzer._calculate_analysis_statistics(categorized_formulas)
    total_formulas = sum(stats["by_category"].values())

    assert total_formulas > 0, "Should have formulas in statistics"
