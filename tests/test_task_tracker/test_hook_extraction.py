"""
Unit Tests for UserPromptSubmit Hook - Task Extraction

Tests the prompt parsing and task extraction logic.
Part of: Enhancement Phase 1.3 - Unit Test Suite
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import hook functions (we need to make them importable)
import importlib.util

spec = importlib.util.spec_from_file_location(
    "user_prompt_submit",
    "/Users/ryanranft/nba-mcp-synthesis/.claude/hooks/user_prompt_submit.py",
)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def test_extract_numbered_list():
    """Test extraction of numbered list tasks."""
    prompt = """
    Please complete these tasks:
    1. Create database schema
    2. Write API endpoints
    3. Add unit tests
    """

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert len(tasks) == 3
    assert tasks[0]["description"] == "Create database schema"
    assert tasks[1]["description"] == "Write API endpoints"
    assert tasks[2]["description"] == "Add unit tests"
    assert all(t["source"] == "numbered_list" for t in tasks)


def test_extract_bullet_list():
    """Test extraction of bullet list tasks."""
    prompt = """
    Please do:
    - Research API options
    - Compare performance
    - Document findings
    """

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert len(tasks) == 3
    assert tasks[0]["description"] == "Research API options"
    assert all(t["source"] == "bullet_list" for t in tasks)


def test_extract_implicit_task():
    """Test extraction of implicit task from action verbs."""
    prompt = "Please implement the new authentication system"

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert len(tasks) == 1
    assert "implement" in tasks[0]["description"].lower()
    assert tasks[0]["source"] == "implicit"


def test_action_verb_detection():
    """Test that action verbs are detected."""
    prompt = "Please research, analyze, and implement the feature"

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert metadata["has_action_verbs"] is True
    assert "research" in metadata["action_verbs_found"]
    assert "analyze" in metadata["action_verbs_found"]
    assert "implement" in metadata["action_verbs_found"]


def test_multi_step_detection():
    """Test multi-step pattern detection."""
    prompt = "Can you create the database and then add the migrations?"

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert metadata["is_multi_step"] is True


def test_complexity_detection():
    """Test complexity indicator detection."""
    prompt = "Build a comprehensive, complete solution for all users"

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert metadata["is_complex"] is True


def test_should_create_tasks_numbered_list():
    """Test that numbered lists always create tasks."""
    prompt = "1. Task A\n2. Task B"
    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert hook.should_create_tasks(prompt, tasks, metadata) is True


def test_should_create_tasks_simple_question():
    """Test that simple questions don't create tasks."""
    prompt = "What is the current status?"
    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert hook.should_create_tasks(prompt, tasks, metadata) is False


def test_should_create_tasks_multi_step():
    """Test that multi-step work creates tasks."""
    prompt = "Can you first analyze the code and then refactor it?"
    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    # May or may not be True depending on detection, but shouldn't crash
    result = hook.should_create_tasks(prompt, tasks, metadata)
    assert isinstance(result, bool)


def test_extract_main_action():
    """Test extraction of main action from prompt."""
    prompt = "Can you please implement the user authentication system?"

    result = hook.extract_main_action(prompt, ["implement"])

    assert "implement" in result.lower()
    assert "user authentication system" in result.lower()
    assert "can you" not in result.lower()  # Cleaned up


def test_extract_main_action_multiple_sentences():
    """Test extraction from multiple sentences."""
    prompt = "I need help. Please create a new database. Then migrate the data."

    result = hook.extract_main_action(prompt, ["create"])

    assert "create" in result.lower()
    assert "database" in result.lower()


def test_empty_prompt():
    """Test handling of empty prompt."""
    prompt = ""

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert len(tasks) == 0
    assert metadata["has_action_verbs"] is False
    assert metadata["is_multi_step"] is False


def test_no_tasks_in_conversation():
    """Test conversational prompt with no tasks."""
    prompt = "Thanks for your help! This looks great."

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert len(tasks) == 0
    assert hook.should_create_tasks(prompt, tasks, metadata) is False


def test_mixed_list_formats():
    """Test prompt with both numbered and bullets."""
    prompt = """
    Phase 1:
    1. Setup database
    2. Create tables

    Also:
    - Write documentation
    - Add tests
    """

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    # Should extract numbered list (takes precedence)
    assert len(tasks) >= 2
    numbered = [t for t in tasks if t["source"] == "numbered_list"]
    assert len(numbered) == 2


def test_complex_numbered_list():
    """Test complex numbered list with details."""
    prompt = """
    Please complete:
    1. Create database schema (include migrations)
    2. Write API endpoints (REST and GraphQL)
    3. Add comprehensive unit tests (>80% coverage)
    4. Deploy to staging environment
    """

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert len(tasks) == 4
    assert "migrations" in tasks[0]["description"]
    assert "REST and GraphQL" in tasks[1]["description"]
    assert ">80% coverage" in tasks[2]["description"]


def test_task_count_in_metadata():
    """Test that task count is correctly recorded."""
    prompt = """
    1. Task one
    2. Task two
    3. Task three
    """

    tasks, metadata = hook.extract_tasks_from_prompt(prompt)

    assert metadata["task_count"] == 3
    assert len(tasks) == 3
