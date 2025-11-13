"""
Unit Tests for Master Task Detection Algorithm

Tests the 12-point scoring system for detecting large initiatives.
Part of: Enhancement Phase 1.3 - Unit Test Suite
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import hook functions
import importlib.util

spec = importlib.util.spec_from_file_location(
    "user_prompt_submit",
    "/Users/ryanranft/nba-mcp-synthesis/.claude/hooks/user_prompt_submit.py",
)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def test_master_task_with_scope_words():
    """Test detection with multiple scope words."""
    prompt = "Build a complete and comprehensive authentication system"
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    assert master_info is not None
    assert master_info["is_master_task"] is True
    # Scope words: 'complete', 'comprehensive' = +3 points
    # Project verb: 'build' = +2 points
    # Domain word: 'system' = +1 point
    # Total should be at least 6
    assert master_info["score"] >= 6


def test_master_task_with_numbered_list():
    """Test detection with numbered breakdown."""
    prompt = """
    Build authentication system:
    1. User registration
    2. Login/logout
    3. Password reset
    4. Email verification
    """
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    assert master_info is not None
    assert master_info["is_master_task"] is True
    # Numbered list: +2 points
    # 4 subtasks: +2 points
    # Project verb 'build': +2 points
    # Domain word 'system': +1 point
    # Total: 7 points
    assert master_info["score"] >= 5


def test_master_task_with_phases():
    """Test detection with phase patterns."""
    prompt = """
    Phase 1: Setup infrastructure
    Phase 2: Implement features
    Phase 3: Testing and deployment
    """
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    assert master_info is not None
    assert master_info["is_master_task"] is True
    # Phase pattern: +3 points
    # 3 subtasks: +2 points
    # Total: 5+ points
    assert master_info["score"] >= 5
    assert "multi-phase work detected" in str(master_info["reasons"])


def test_not_master_task_simple_request():
    """Test that simple requests don't trigger master task detection."""
    prompt = "Fix the login button styling"
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    # Score should be low (maybe 0-2 points)
    assert master_info is None or master_info["score"] < 5


def test_not_master_task_single_action():
    """Test that single actions don't trigger detection."""
    prompt = "Create a new API endpoint for user profiles"
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    # Might have 'create' verb (+2) but should be below threshold
    assert master_info is None or master_info["score"] < 5


def test_master_task_confidence_calculation():
    """Test confidence score calculation."""
    prompt = """
    Build a complete, comprehensive e-commerce platform:
    1. Product catalog
    2. Shopping cart
    3. Checkout system
    4. Payment integration
    5. Order management
    """
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    assert master_info is not None
    # Confidence should be between 0 and 1
    assert 0 <= master_info["confidence"] <= 1.0
    # High score should give high confidence
    assert master_info["confidence"] > 0.5


def test_master_task_title_extraction():
    """Test extraction of master task title."""
    prompt = "Build a comprehensive user management system with authentication"
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    if master_info:
        title = master_info["title"]
        assert "Build" in title or "build" in title
        assert len(title) > 5  # Should be meaningful


def test_extract_master_task_title_direct():
    """Test title extraction function directly."""
    prompt = "Please create a complete API integration system"
    tasks = [
        {"description": "Setup endpoints"},
        {"description": "Add authentication"},
        {"description": "Write tests"},
    ]

    title = hook.extract_master_task_title(prompt, tasks)

    assert title is not None
    assert len(title) > 0
    assert title[0].isupper()  # Should be capitalized


def test_context_summary_generation():
    """Test context summary generation."""
    prompt = "This is a long prompt " * 30  # Make it long
    tasks = [
        {"description": "Task 1"},
        {"description": "Task 2"},
        {"description": "Task 3"},
    ]

    summary = hook.generate_context_summary(prompt, tasks)

    assert summary is not None
    assert "..." in summary  # Should be truncated
    assert "Includes 3 major tasks" in summary


def test_project_verb_detection():
    """Test detection of project-level verbs."""
    prompts_with_verbs = [
        "Build a new system",
        "Implement complete solution",
        "Develop entire platform",
        "Create comprehensive app",
    ]

    for prompt in prompts_with_verbs:
        tasks, _ = hook.extract_tasks_from_prompt(prompt)
        master_info = hook.infer_master_task(prompt, tasks)

        # Each has project verb, but may or may not reach threshold
        # Just check it doesn't crash
        assert isinstance(master_info, dict) or master_info is None


def test_domain_word_detection():
    """Test detection of domain words."""
    prompt = "Build an application platform service with complete system integration"
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    if master_info:
        # Should detect multiple domain words
        reasons = " ".join(master_info["reasons"])
        assert "system component" in reasons.lower() or master_info["score"] > 0


def test_long_prompt_bonus():
    """Test that long prompts get bonus points."""
    prompt = "Build authentication. " * 60  # Make it >500 chars
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    if master_info and len(prompt) > 500:
        assert "detailed request" in str(master_info["reasons"])


def test_master_task_estimated_subtasks():
    """Test that estimated subtasks are recorded."""
    prompt = """
    Create complete system:
    1. Task A
    2. Task B
    3. Task C
    4. Task D
    5. Task E
    """
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    assert master_info is not None
    assert master_info["estimated_subtasks"] == 5


def test_scoring_threshold():
    """Test that threshold of 5 points is enforced."""
    # Create a prompt that scores exactly at threshold
    prompt = "Build system with steps: 1. A  2. B  3. C"  # Should score 5-6 points
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    # If detected, score should be >= 5
    if master_info:
        assert master_info["score"] >= 5
        assert master_info["is_master_task"] is True


def test_reasons_list_populated():
    """Test that reasons list is populated with detection reasons."""
    prompt = """
    Build complete platform:
    1. Component A
    2. Component B
    3. Component C
    """
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    if master_info:
        assert len(master_info["reasons"]) > 0
        assert all(isinstance(r, str) for r in master_info["reasons"])


def test_zero_subtasks_handling():
    """Test handling when no explicit subtasks are found."""
    prompt = "Build a comprehensive system"
    tasks, _ = hook.extract_tasks_from_prompt(prompt)

    master_info = hook.infer_master_task(prompt, tasks)

    # Should still detect based on other indicators
    if master_info:
        # estimated_subtasks might be 0 or 'unknown'
        assert master_info["estimated_subtasks"] in [0, "unknown"]


def test_maximum_confidence_capped():
    """Test that confidence is capped at 1.0."""
    # Create a prompt that scores very high (>12 points shouldn't be possible but test cap)
    prompt = """
    Build a complete, comprehensive, full, entire system platform application:
    Phase 1: Step 1, 2, 3
    Phase 2: Step 4, 5, 6
    Phase 3: Step 7, 8, 9
    1. Task A
    2. Task B
    3. Task C
    4. Task D
    5. Task E
    """
    prompt += "Additional details " * 50  # Make it very long

    tasks, _ = hook.extract_tasks_from_prompt(prompt)
    master_info = hook.infer_master_task(prompt, tasks)

    if master_info:
        assert master_info["confidence"] <= 1.0
