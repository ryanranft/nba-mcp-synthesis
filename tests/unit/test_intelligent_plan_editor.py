#!/usr/bin/env python3
"""
Unit tests for IntelligentPlanEditor.

Tests all CRUD operations, validation, backup creation, and modification tracking.
"""

import json
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.intelligent_plan_editor import (
    IntelligentPlanEditor,
    PlanSection,
    PlanModification,
    ValidationResult,
)


class TestIntelligentPlanEditor(unittest.TestCase):
    """Test suite for IntelligentPlanEditor."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create test plan file
        self.plan_path = self.temp_path / "test_plan.md"
        self.plan_content = """# Test Implementation Plan

## Overview

This is a test plan for validating the Intelligent Plan Editor.

## Phase 1: Setup

### Task 1.1: Initialize Project

Initialize the project with basic structure.

### Task 1.2: Install Dependencies

Install required dependencies.

## Phase 2: Development

### Task 2.1: Implement Features

Implement core features.

## Phase 3: Testing

Test all features thoroughly.
"""
        self.plan_path.write_text(self.plan_content)

        # Create backup directory
        self.backup_dir = self.temp_path / "backups"
        self.modifications_log = self.temp_path / "modifications.json"

        # Initialize editor
        self.editor = IntelligentPlanEditor(
            self.plan_path, self.backup_dir, self.modifications_log
        )

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test editor initialization."""
        self.assertTrue(self.plan_path.exists())
        self.assertTrue(self.backup_dir.exists())
        self.assertTrue(self.modifications_log.exists())

        # Check modifications log is initialized as empty array
        modifications = json.loads(self.modifications_log.read_text())
        self.assertEqual(modifications, [])

    def test_load_plan(self):
        """Test loading plan content."""
        content = self.editor._load_plan()
        self.assertEqual(content, self.plan_content)

        # Test caching
        content2 = self.editor._load_plan()
        self.assertIs(content, content2)  # Should be same object (cached)

        # Test force reload
        content3 = self.editor._load_plan(force_reload=True)
        self.assertEqual(content3, self.plan_content)

    def test_parse_plan_structure(self):
        """Test parsing plan into sections."""
        sections = self.editor.parse_plan_structure()

        # Should have 8 sections (1 H1 title, 1 H2 overview, 3 H2 phases, 3 H3 tasks)
        self.assertEqual(len(sections), 8)

        # Check first section
        self.assertEqual(sections[0].title, "Test Implementation Plan")
        self.assertEqual(sections[0].level, 1)
        self.assertIsNone(sections[0].parent_id)

        # Check hierarchical structure
        overview = [s for s in sections if s.title == "Overview"][0]
        self.assertEqual(overview.level, 2)
        self.assertIsNotNone(overview.parent_id)

        # Check task hierarchy
        phase1 = [s for s in sections if s.title == "Phase 1: Setup"][0]
        task1_1 = [s for s in sections if s.title == "Task 1.1: Initialize Project"][0]
        self.assertEqual(task1_1.parent_id, phase1.id)

    def test_find_section_by_id(self):
        """Test finding sections by ID."""
        sections = self.editor.parse_plan_structure()

        # Find first section
        section = self.editor.find_section_by_id(sections[0].id)
        self.assertIsNotNone(section)
        self.assertEqual(section.title, "Test Implementation Plan")

        # Find non-existent section
        section = self.editor.find_section_by_id("nonexistent_id")
        self.assertIsNone(section)

    def test_find_sections_by_title(self):
        """Test finding sections by title."""
        # Exact match
        sections = self.editor.find_sections_by_title("Overview", exact=True)
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0].title, "Overview")

        # Partial match
        sections = self.editor.find_sections_by_title("Task", exact=False)
        self.assertEqual(len(sections), 3)  # Task 1.1, 1.2, 2.1

        # Case insensitive
        sections = self.editor.find_sections_by_title("phase", exact=False)
        self.assertEqual(len(sections), 3)  # Phase 1, 2, 3

    def test_validate_plan_structure(self):
        """Test plan structure validation."""
        result = self.editor.validate_plan_structure()

        # Should be valid
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

        # May have some suggestions
        self.assertIsInstance(result.suggestions, list)

    def test_validate_invalid_structure(self):
        """Test validation with invalid structure."""
        # Create plan with level jump (skip level 2, go straight to 3)
        invalid_plan = self.temp_path / "invalid_plan.md"
        invalid_plan.write_text(
            """# Title

### Skipped Level

Content here.
"""
        )

        invalid_editor = IntelligentPlanEditor(
            invalid_plan, self.backup_dir, self.modifications_log
        )

        result = invalid_editor.validate_plan_structure()

        # Should have warnings about level jump
        self.assertTrue(len(result.warnings) > 0)
        self.assertTrue(any("level jump" in w.lower() for w in result.warnings))

    def test_create_backup(self):
        """Test backup creation."""
        # Create backup
        backup_path = self.editor._create_backup()

        # Verify backup exists
        self.assertTrue(backup_path.exists())

        # Verify backup content matches original
        backup_content = backup_path.read_text()
        self.assertEqual(backup_content, self.plan_content)

        # Verify backup naming
        self.assertTrue(backup_path.name.startswith("test_plan_"))
        self.assertTrue(backup_path.name.endswith(".backup.md"))

    def test_add_new_plan_at_end(self):
        """Test adding a new section at the end."""
        modification = self.editor.add_new_plan(
            title="Phase 4: Deployment",
            content="Deploy the application to production.",
            position="end",
            level=2,
            rationale="Adding deployment phase",
        )

        # Verify modification record
        self.assertEqual(modification.operation, "ADD")
        self.assertIsNotNone(modification.new_content)
        self.assertIsNone(modification.old_content)
        self.assertEqual(modification.rationale, "Adding deployment phase")

        # Verify section was added
        sections = self.editor.parse_plan_structure(force_reload=True)
        new_section = [s for s in sections if "Deployment" in s.title]
        self.assertEqual(len(new_section), 1)
        self.assertEqual(new_section[0].level, 2)

        # Verify backup was created
        self.assertTrue(Path(modification.backup_path).exists())

        # Verify modification was logged
        modifications = self.editor.get_modification_history()
        self.assertEqual(len(modifications), 1)
        self.assertEqual(modifications[0]["operation"], "ADD")

    def test_add_new_plan_at_start(self):
        """Test adding a new section at the start."""
        modification = self.editor.add_new_plan(
            title="Preface",
            content="Introduction to the plan.",
            position="start",
            level=2,
            rationale="Adding preface",
        )

        # Verify section was added near start
        content = self.editor._load_plan(force_reload=True)
        lines = content.split("\n")

        # Find the preface
        preface_index = None
        for i, line in enumerate(lines):
            if "Preface" in line:
                preface_index = i
                break

        self.assertIsNotNone(preface_index)
        # Should be before Overview (around line 4-5)
        self.assertLess(preface_index, 10)

    def test_add_new_plan_after_section(self):
        """Test adding a new section after a specific section."""
        sections = self.editor.parse_plan_structure()
        phase1 = [s for s in sections if s.title == "Phase 1: Setup"][0]

        modification = self.editor.add_new_plan(
            title="Phase 1.5: Configuration",
            content="Configure the application.",
            position=f"after:{phase1.id}",
            level=2,
            rationale="Adding configuration phase",
        )

        # Verify section was added after Phase 1
        sections = self.editor.parse_plan_structure(force_reload=True)
        phase1_5 = [s for s in sections if "Configuration" in s.title]
        self.assertEqual(len(phase1_5), 1)

        # Should be after Phase 1 but before Phase 2
        phase1_new = [s for s in sections if s.title == "Phase 1: Setup"][0]
        phase2 = [s for s in sections if s.title == "Phase 2: Development"][0]

        self.assertGreater(phase1_5[0].line_start, phase1_new.line_end)
        self.assertLess(phase1_5[0].line_start, phase2.line_start)

    def test_modify_existing_plan_content(self):
        """Test modifying section content."""
        sections = self.editor.parse_plan_structure()
        overview = [s for s in sections if s.title == "Overview"][0]

        new_content = "This is the updated overview with new information."

        modification = self.editor.modify_existing_plan(
            section_id=overview.id,
            new_content=new_content,
            rationale="Updating overview content",
        )

        # Verify modification
        self.assertEqual(modification.operation, "MODIFY")
        self.assertIsNotNone(modification.old_content)
        self.assertIsNotNone(modification.new_content)

        # Verify content was updated
        updated_section = self.editor.find_section_by_id(overview.id)
        self.assertIn(new_content, updated_section.content)

        # Verify backup was created
        self.assertTrue(Path(modification.backup_path).exists())

    def test_modify_existing_plan_title(self):
        """Test modifying section title."""
        sections = self.editor.parse_plan_structure()
        phase3 = [s for s in sections if s.title == "Phase 3: Testing"][0]

        modification = self.editor.modify_existing_plan(
            section_id=phase3.id,
            new_title="Phase 3: Quality Assurance",
            rationale="Renaming phase",
        )

        # Verify title was updated
        sections = self.editor.parse_plan_structure(force_reload=True)
        renamed = [s for s in sections if "Quality Assurance" in s.title]
        self.assertEqual(len(renamed), 1)

        # Old title should not exist
        old_title = [s for s in sections if s.title == "Phase 3: Testing"]
        self.assertEqual(len(old_title), 0)

    def test_modify_append_content(self):
        """Test appending content to a section."""
        sections = self.editor.parse_plan_structure()
        overview = [s for s in sections if s.title == "Overview"][0]

        original_content = overview.content
        append_text = "\n\nThis is additional information appended to the overview."

        modification = self.editor.modify_existing_plan(
            section_id=overview.id,
            append_content=append_text,
            rationale="Appending to overview",
        )

        # Verify content was appended
        updated_section = self.editor.find_section_by_id(overview.id)
        self.assertIn("additional information", updated_section.content)

        # Original content should still be there
        self.assertIn("test plan", updated_section.content.lower())

    def test_modify_prepend_content(self):
        """Test prepending content to a section."""
        sections = self.editor.parse_plan_structure()
        overview = [s for s in sections if s.title == "Overview"][0]

        prepend_text = "**Important Note:** This plan is subject to change.\n"

        modification = self.editor.modify_existing_plan(
            section_id=overview.id,
            prepend_content=prepend_text,
            rationale="Adding note to overview",
        )

        # Verify content was prepended
        updated_section = self.editor.find_section_by_id(overview.id)
        content_lines = updated_section.content.split("\n")

        # Should find the prepended text early in the content (after header)
        found_prepend = False
        for line in content_lines[:5]:  # Check first 5 lines
            if "Important Note" in line:
                found_prepend = True
                break

        self.assertTrue(found_prepend)

    def test_modify_nonexistent_section(self):
        """Test modifying a section that doesn't exist."""
        with self.assertRaises(ValueError) as context:
            self.editor.modify_existing_plan(
                section_id="nonexistent_section_id", new_content="New content"
            )

        self.assertIn("not found", str(context.exception).lower())

    def test_modification_history(self):
        """Test retrieving modification history."""
        # Add a section
        self.editor.add_new_plan(
            title="New Section 1", content="Content 1", position="end", level=2
        )

        # Modify a section
        sections = self.editor.parse_plan_structure()
        section = sections[0]
        self.editor.modify_existing_plan(
            section_id=section.id, new_content="Modified content"
        )

        # Add another section
        self.editor.add_new_plan(
            title="New Section 2", content="Content 2", position="end", level=2
        )

        # Get all modifications
        history = self.editor.get_modification_history()
        self.assertEqual(len(history), 3)

        # Filter by operation
        adds = self.editor.get_modification_history(operation="ADD")
        self.assertEqual(len(adds), 2)

        modifies = self.editor.get_modification_history(operation="MODIFY")
        self.assertEqual(len(modifies), 1)

        # Filter by section
        section_history = self.editor.get_modification_history(section_id=section.id)
        self.assertEqual(len(section_history), 1)
        self.assertEqual(section_history[0]["operation"], "MODIFY")

        # Limit results
        limited = self.editor.get_modification_history(limit=2)
        self.assertEqual(len(limited), 2)

    def test_restore_from_backup(self):
        """Test restoring plan from backup."""
        # Get original content
        original_content = self.editor._load_plan()

        # Create backup
        backup_path = self.editor._create_backup()

        # Modify the plan
        self.editor.add_new_plan(
            title="Temporary Section",
            content="This will be removed",
            position="end",
            level=2,
        )

        # Verify modification
        modified_content = self.editor._load_plan(force_reload=True)
        self.assertNotEqual(modified_content, original_content)
        self.assertIn("Temporary Section", modified_content)

        # Restore from backup
        self.editor.restore_from_backup(backup_path)

        # Verify restoration
        restored_content = self.editor._load_plan(force_reload=True)
        self.assertEqual(restored_content, original_content)
        self.assertNotIn("Temporary Section", restored_content)

    def test_restore_from_nonexistent_backup(self):
        """Test restoring from a backup that doesn't exist."""
        nonexistent = self.temp_path / "nonexistent_backup.md"

        with self.assertRaises(FileNotFoundError):
            self.editor.restore_from_backup(nonexistent)

    def test_generate_diff(self):
        """Test diff generation."""
        old_content = "Line 1\nLine 2\nLine 3"
        new_content = "Line 1\nLine 2 modified\nLine 3\nLine 4"

        diff = self.editor.generate_diff(old_content, new_content)

        # Verify diff contains markers
        self.assertIn("---", diff)
        self.assertIn("+++", diff)
        self.assertIn("- Line 2", diff)
        self.assertIn("+ Line 2 modified", diff)
        self.assertIn("+ Line 4", diff)

    def test_get_statistics(self):
        """Test statistics generation."""
        # Add some modifications
        self.editor.add_new_plan(
            title="New Section", content="Content", position="end", level=2
        )

        sections = self.editor.parse_plan_structure()
        self.editor.modify_existing_plan(
            section_id=sections[0].id, new_content="Modified"
        )

        # Get statistics
        stats = self.editor.get_statistics()

        # Verify statistics structure
        self.assertIn("total_sections", stats)
        self.assertIn("sections_by_level", stats)
        self.assertIn("total_modifications", stats)
        self.assertIn("modifications_by_operation", stats)
        self.assertIn("modifications_by_source", stats)
        self.assertIn("backup_count", stats)

        # Verify values
        self.assertGreater(stats["total_sections"], 0)
        self.assertEqual(stats["total_modifications"], 2)
        self.assertEqual(stats["modifications_by_operation"]["ADD"], 1)
        self.assertEqual(stats["modifications_by_operation"]["MODIFY"], 1)
        self.assertGreater(stats["backup_count"], 0)

    def test_confidence_and_source_tracking(self):
        """Test confidence scores and source tracking."""
        # Add with AI source and confidence
        modification = self.editor.add_new_plan(
            title="AI Generated Section",
            content="Content generated by AI",
            position="end",
            level=2,
            confidence=0.85,
            source="ai",
        )

        # Verify in modification record
        self.assertEqual(modification.confidence, 0.85)
        self.assertEqual(modification.source, "ai")

        # Verify in log
        history = self.editor.get_modification_history()
        last_mod = history[-1]
        self.assertEqual(last_mod["confidence"], 0.85)
        self.assertEqual(last_mod["source"], "ai")

    def test_section_id_generation(self):
        """Test section ID generation."""
        # Test various titles
        test_cases = [
            ("Simple Title", 10),
            ("Title with Numbers 123", 20),
            ("Title-with-Dashes", 30),
            ("Title_with_Underscores", 40),
            ("Title with Special!@#$%Characters", 50),
        ]

        for title, line_num in test_cases:
            section_id = self.editor._generate_section_id(title, line_num)

            # Should only contain alphanumeric, underscores, and line number
            self.assertRegex(section_id, r"^[a-z0-9_]+_L\d+$")
            self.assertIn(f"_L{line_num}", section_id)

    def test_multiple_backups(self):
        """Test that multiple operations create multiple backups."""
        # Perform multiple operations
        for i in range(3):
            self.editor.add_new_plan(
                title=f"Section {i}", content=f"Content {i}", position="end", level=2
            )

        # Check backup count
        backups = list(self.backup_dir.glob("*.backup.md"))
        self.assertEqual(len(backups), 3)

    def test_cache_invalidation(self):
        """Test that cache is invalidated after modifications."""
        # Parse plan
        sections1 = self.editor.parse_plan_structure()
        count1 = len(sections1)

        # Add a section
        self.editor.add_new_plan(
            title="New Section", content="Content", position="end", level=2
        )

        # Parse again (should reflect changes)
        sections2 = self.editor.parse_plan_structure()
        count2 = len(sections2)

        self.assertEqual(count2, count1 + 1)

    def test_empty_plan(self):
        """Test handling of an empty plan file."""
        empty_plan = self.temp_path / "empty_plan.md"
        empty_plan.write_text("")

        empty_editor = IntelligentPlanEditor(
            empty_plan, self.backup_dir, self.modifications_log
        )

        sections = empty_editor.parse_plan_structure()
        self.assertEqual(len(sections), 0)

        # Should still be able to add to empty plan
        modification = empty_editor.add_new_plan(
            title="First Section", content="First content", position="end", level=1
        )

        self.assertEqual(modification.operation, "ADD")

        sections = empty_editor.parse_plan_structure(force_reload=True)
        self.assertEqual(len(sections), 1)

    def test_delete_section(self):
        """Test deleting a section."""
        sections = self.editor.parse_plan_structure()
        section_to_delete = [s for s in sections if s.title == "Overview"][0]

        modification = self.editor.delete_obsolete_plan(
            section_id=section_to_delete.id, rationale="No longer needed"
        )

        # Verify modification record
        self.assertEqual(modification.operation, "DELETE")
        self.assertIsNotNone(modification.old_content)
        self.assertIsNone(modification.new_content)

        # Verify section was deleted
        sections_after = self.editor.parse_plan_structure(force_reload=True)
        deleted = [s for s in sections_after if s.title == "Overview"]
        self.assertEqual(len(deleted), 0)

        # Verify section count decreased
        self.assertEqual(len(sections_after), len(sections) - 1)

        # Verify backup and archive created
        self.assertTrue(Path(modification.backup_path).exists())
        if modification.metadata and "archive_path" in modification.metadata:
            self.assertTrue(Path(modification.metadata["archive_path"]).exists())

    def test_delete_with_cascade(self):
        """Test cascading deletion of section and its children."""
        sections = self.editor.parse_plan_structure()
        phase1 = [s for s in sections if s.title == "Phase 1: Setup"][0]

        # Count children before deletion
        children_before = [s for s in sections if s.parent_id == phase1.id]
        self.assertGreater(len(children_before), 0)  # Should have children

        modification = self.editor.delete_obsolete_plan(
            section_id=phase1.id, cascade=True, rationale="Removing entire phase"
        )

        # Verify cascade flag in metadata
        self.assertTrue(modification.metadata.get("cascade"))

        # Verify phase and children are deleted
        sections_after = self.editor.parse_plan_structure(force_reload=True)
        phase1_after = [s for s in sections_after if s.title == "Phase 1: Setup"]
        self.assertEqual(len(phase1_after), 0)

        # Verify children are also deleted
        for child in children_before:
            child_after = [s for s in sections_after if s.id == child.id]
            self.assertEqual(len(child_after), 0)

    def test_delete_nonexistent_section(self):
        """Test deleting a section that doesn't exist."""
        with self.assertRaises(ValueError) as context:
            self.editor.delete_obsolete_plan(section_id="nonexistent_id")

        self.assertIn("not found", str(context.exception).lower())

    def test_merge_sections(self):
        """Test merging two sections."""
        # Create two similar sections to merge
        mod1 = self.editor.add_new_plan(
            title="Feature A",
            content="This is feature A content.",
            position="end",
            level=2,
        )

        mod2 = self.editor.add_new_plan(
            title="Feature A Duplicate",
            content="This is also feature A content with more details.",
            position="end",
            level=2,
        )

        # Get section IDs from the plan
        sections = self.editor.parse_plan_structure(force_reload=True)
        feature_a = [
            s for s in sections if "Feature A" in s.title and "Duplicate" not in s.title
        ][0]
        feature_a_dup = [s for s in sections if "Feature A Duplicate" in s.title][0]

        # Merge the sections
        modification = self.editor.merge_duplicate_plans(
            section_id_1=feature_a.id,
            section_id_2=feature_a_dup.id,
            keep_section="first",
            merge_strategy="union",
            rationale="Merging duplicates",
        )

        # Verify modification
        self.assertEqual(modification.operation, "MERGE")
        self.assertIn("merged_sections", modification.metadata)
        self.assertIn("kept_section", modification.metadata)

        # Verify one section is gone
        sections_after = self.editor.parse_plan_structure(force_reload=True)
        feature_a_count = len([s for s in sections_after if "Feature A" in s.title])
        self.assertEqual(feature_a_count, 1)  # Only one left

    def test_merge_with_first_strategy(self):
        """Test merging with 'first' strategy (keep only first content)."""
        # Create two sections
        self.editor.add_new_plan(
            title="Test Section 1",
            content="Content from section 1.",
            position="end",
            level=2,
        )

        self.editor.add_new_plan(
            title="Test Section 2",
            content="Content from section 2.",
            position="end",
            level=2,
        )

        sections = self.editor.parse_plan_structure(force_reload=True)
        sec1 = [s for s in sections if s.title == "Test Section 1"][0]
        sec2 = [s for s in sections if s.title == "Test Section 2"][0]

        self.editor.merge_duplicate_plans(
            section_id_1=sec1.id,
            section_id_2=sec2.id,
            merge_strategy="first",
            rationale="Testing first strategy",
        )

        # Verify merged content contains first section's content
        sections_after = self.editor.parse_plan_structure(force_reload=True)
        merged = [s for s in sections_after if s.title == "Test Section 1"][0]
        self.assertIn("Content from section 1", merged.content)

    def test_merge_with_smart_strategy(self):
        """Test merging with 'smart' strategy (deduplicate)."""
        self.editor.add_new_plan(
            title="Test Section A",
            content="Shared line\nUnique line A",
            position="end",
            level=2,
        )

        self.editor.add_new_plan(
            title="Test Section B",
            content="Shared line\nUnique line B",
            position="end",
            level=2,
        )

        sections = self.editor.parse_plan_structure(force_reload=True)
        secA = [s for s in sections if s.title == "Test Section A"][0]
        secB = [s for s in sections if s.title == "Test Section B"][0]

        self.editor.merge_duplicate_plans(
            section_id_1=secA.id,
            section_id_2=secB.id,
            merge_strategy="smart",
            rationale="Testing smart strategy",
        )

        # Verify merged content has both unique lines but shared line appears once
        sections_after = self.editor.parse_plan_structure(force_reload=True)
        merged = [s for s in sections_after if s.title == "Test Section A"][0]

        # Should contain both unique lines
        self.assertIn("Unique line A", merged.content)
        self.assertIn("Unique line B", merged.content)

    def test_find_duplicate_sections(self):
        """Test finding duplicate sections by title similarity."""
        # Create some sections with similar titles
        self.editor.add_new_plan(
            title="Phase 1: Setup", content="Setup phase", position="end", level=2
        )

        self.editor.add_new_plan(
            title="Phase 1: SetUp",  # Similar title (different case)
            content="Also setup phase",
            position="end",
            level=2,
        )

        # Find duplicates
        duplicates = self.editor.find_duplicate_sections(similarity_threshold=0.8)

        # Should find at least the two similar sections we created
        # (may find others depending on test plan content)
        self.assertGreater(len(duplicates), 0)

        # Check structure of results
        for sec1, sec2, similarity in duplicates:
            self.assertIsInstance(similarity, float)
            self.assertGreaterEqual(similarity, 0.8)
            self.assertLessEqual(similarity, 1.0)

    def test_delete_creates_archive(self):
        """Test that deletion creates an archive file."""
        sections = self.editor.parse_plan_structure()
        section_to_delete = sections[1]  # Delete second section

        modification = self.editor.delete_obsolete_plan(
            section_id=section_to_delete.id, archive=True, rationale="Testing archive"
        )

        # Verify archive was created
        self.assertIn("archive_path", modification.metadata)
        archive_path = Path(modification.metadata["archive_path"])
        self.assertTrue(archive_path.exists())

        # Verify archive contains deleted content
        archive_content = archive_path.read_text()
        self.assertIn(section_to_delete.title, archive_content)
        self.assertIn("Deleted Section:", archive_content)

    def test_delete_without_archive(self):
        """Test deletion without archiving."""
        sections = self.editor.parse_plan_structure()
        section_to_delete = sections[1]

        modification = self.editor.delete_obsolete_plan(
            section_id=section_to_delete.id,
            archive=False,
            rationale="No archive needed",
        )

        # Verify no archive was created
        self.assertNotIn("archive_path", modification.metadata)

    def test_merge_nonexistent_sections(self):
        """Test merging sections that don't exist."""
        with self.assertRaises(ValueError):
            self.editor.merge_duplicate_plans(
                section_id_1="nonexistent_1", section_id_2="nonexistent_2"
            )

    def test_all_crud_operations_create_backups(self):
        """Test that all CRUD operations create backups."""
        initial_backup_count = len(list(self.backup_dir.glob("*.backup.md")))

        sections = self.editor.parse_plan_structure()

        # ADD
        mod_add = self.editor.add_new_plan(
            title="Test Add", content="Test content", position="end", level=2
        )
        self.assertIsNotNone(mod_add.backup_path)
        self.assertTrue(Path(mod_add.backup_path).exists())

        # MODIFY
        mod_modify = self.editor.modify_existing_plan(
            section_id=sections[0].id, append_content="\nModified"
        )
        self.assertIsNotNone(mod_modify.backup_path)
        self.assertTrue(Path(mod_modify.backup_path).exists())

        # DELETE
        sections_updated = self.editor.parse_plan_structure(force_reload=True)
        mod_delete = self.editor.delete_obsolete_plan(
            section_id=sections_updated[-1].id  # Delete last section
        )
        self.assertIsNotNone(mod_delete.backup_path)
        self.assertTrue(Path(mod_delete.backup_path).exists())

        # Verify backup count increased by 3
        final_backup_count = len(list(self.backup_dir.glob("*.backup.md")))
        self.assertEqual(final_backup_count, initial_backup_count + 3)

    def test_merge_updates_modification_history(self):
        """Test that merge operations are logged in modification history."""
        # Create two sections to merge
        self.editor.add_new_plan(
            title="Merge Test 1", content="Content 1", position="end", level=2
        )

        self.editor.add_new_plan(
            title="Merge Test 2", content="Content 2", position="end", level=2
        )

        sections = self.editor.parse_plan_structure(force_reload=True)
        merge1 = [s for s in sections if s.title == "Merge Test 1"][0]
        merge2 = [s for s in sections if s.title == "Merge Test 2"][0]

        # Perform merge
        self.editor.merge_duplicate_plans(
            section_id_1=merge1.id,
            section_id_2=merge2.id,
            rationale="Testing merge history",
        )

        # Check history
        history = self.editor.get_modification_history()

        # Should have MERGE, MODIFY (for kept section), and DELETE (for removed section)
        merge_ops = [m for m in history if m["operation"] == "MERGE"]
        self.assertGreater(len(merge_ops), 0)

        # Check the merge operation has correct metadata
        last_merge = merge_ops[-1]
        self.assertEqual(last_merge["rationale"], "Testing merge history")


if __name__ == "__main__":
    unittest.main()
