#!/usr/bin/env python3
"""
Intelligent Plan Editor - CRUD operations for implementation plans.

This module provides intelligent editing capabilities for implementation plan files,
including ADD, MODIFY, DELETE, and MERGE operations with automatic backup and validation.

Features:
- ADD new plans/sections with automatic numbering
- MODIFY existing plans with conflict detection
- DELETE obsolete plans with dependency checks
- MERGE duplicate plans intelligently
- Automatic backup creation before any modification
- Plan structure validation and consistency checking
- Integration with Phase Status Manager
- Diff generation for review

Author: AI Development Team
Created: October 29, 2025
"""

import json
import logging
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class PlanSection:
    """Represents a section in an implementation plan."""

    id: str  # Unique identifier (e.g., "day_4_task_13")
    title: str  # Section title
    content: str  # Full content of the section
    line_start: int  # Starting line number
    line_end: int  # Ending line number
    level: int  # Header level (1-6)
    parent_id: Optional[str] = None  # Parent section ID
    dependencies: List[str] = field(default_factory=list)  # Dependent section IDs
    metadata: Dict = field(default_factory=dict)  # Additional metadata


@dataclass
class PlanModification:
    """Represents a modification to a plan."""

    operation: str  # ADD, MODIFY, DELETE, MERGE
    section_id: str  # Section being modified
    old_content: Optional[str] = None  # Original content (for MODIFY/DELETE)
    new_content: Optional[str] = None  # New content (for ADD/MODIFY)
    rationale: str = ""  # Explanation for the modification
    confidence: float = 0.0  # Confidence score (0-1)
    source: str = "manual"  # Source of modification (manual, ai, merge)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    backup_path: Optional[str] = None  # Path to backup file
    metadata: Dict = field(default_factory=dict)  # Additional metadata


@dataclass
class ValidationResult:
    """Result of plan validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class IntelligentPlanEditor:
    """
    Intelligent editor for implementation plan files.

    Provides CRUD operations with automatic backup, validation, and conflict detection.
    Maintains plan structure consistency and tracks all modifications.
    """

    def __init__(
        self,
        plan_path: Path,
        backup_dir: Path = Path("workflow_state/plan_backups"),
        modifications_log: Path = Path("workflow_state/plan_modifications.json"),
    ):
        """
        Initialize the Intelligent Plan Editor.

        Args:
            plan_path: Path to the implementation plan file
            backup_dir: Directory for storing backups
            modifications_log: Path to modifications log file
        """
        self.plan_path = Path(plan_path)
        self.backup_dir = Path(backup_dir)
        self.modifications_log = Path(modifications_log)

        # Create directories if they don't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.modifications_log.parent.mkdir(parents=True, exist_ok=True)

        # Initialize modifications log
        if not self.modifications_log.exists():
            self.modifications_log.write_text(json.dumps([], indent=2))

        # Cache for parsed plan structure
        self._plan_sections: Optional[List[PlanSection]] = None
        self._plan_content: Optional[str] = None
        self._last_parsed: Optional[float] = None

        logger.info(f"Initialized IntelligentPlanEditor for: {self.plan_path}")

    def _load_plan(self, force_reload: bool = False) -> str:
        """Load plan content from file."""
        # Check if we need to reload
        current_mtime = self.plan_path.stat().st_mtime
        if (
            force_reload
            or self._plan_content is None
            or self._last_parsed != current_mtime
        ):
            self._plan_content = self.plan_path.read_text(encoding="utf-8")
            self._last_parsed = current_mtime
            self._plan_sections = None  # Clear cached sections
            logger.debug(f"Loaded plan from {self.plan_path}")

        return self._plan_content

    def _save_plan(self, content: str) -> None:
        """Save plan content to file."""
        self.plan_path.write_text(content, encoding="utf-8")
        self._plan_content = content
        self._last_parsed = self.plan_path.stat().st_mtime
        self._plan_sections = None  # Clear cached sections
        logger.debug(f"Saved plan to {self.plan_path}")

    def _create_backup(self) -> Path:
        """Create a timestamped backup of the current plan."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_name = f"{self.plan_path.stem}_{timestamp}.backup.md"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(self.plan_path, backup_path)
        logger.info(f"✅ Created backup: {backup_path}")

        return backup_path

    def _log_modification(self, modification: PlanModification) -> None:
        """Log a modification to the modifications log."""
        modifications = json.loads(self.modifications_log.read_text())
        modifications.append(
            {
                "operation": modification.operation,
                "section_id": modification.section_id,
                "rationale": modification.rationale,
                "confidence": modification.confidence,
                "source": modification.source,
                "timestamp": modification.timestamp,
                "backup_path": (
                    str(modification.backup_path) if modification.backup_path else None
                ),
            }
        )

        self.modifications_log.write_text(json.dumps(modifications, indent=2))
        logger.debug(
            f"Logged modification: {modification.operation} on {modification.section_id}"
        )

    def parse_plan_structure(self, force_reload: bool = False) -> List[PlanSection]:
        """
        Parse the plan file into structured sections.

        Args:
            force_reload: Force reload from disk even if cached

        Returns:
            List of PlanSection objects representing the plan structure
        """
        # Return cached if available
        if not force_reload and self._plan_sections is not None:
            return self._plan_sections

        content = self._load_plan(force_reload)
        lines = content.split("\n")
        sections = []

        # Regex for markdown headers
        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        # Track current section
        current_section = None
        section_content_lines = []
        parent_stack = []  # Stack of (level, section_id)

        for line_num, line in enumerate(lines, start=1):
            match = header_pattern.match(line)

            if match:
                # Save previous section if it exists
                if current_section is not None:
                    current_section.content = "\n".join(section_content_lines)
                    current_section.line_end = line_num - 1
                    sections.append(current_section)

                # Start new section
                level = len(match.group(1))
                title = match.group(2).strip()

                # Generate section ID
                section_id = self._generate_section_id(title, line_num)

                # Determine parent
                parent_id = None
                while parent_stack and parent_stack[-1][0] >= level:
                    parent_stack.pop()
                if parent_stack:
                    parent_id = parent_stack[-1][1]

                current_section = PlanSection(
                    id=section_id,
                    title=title,
                    content="",
                    line_start=line_num,
                    line_end=line_num,
                    level=level,
                    parent_id=parent_id,
                )

                parent_stack.append((level, section_id))
                section_content_lines = [line]

            else:
                # Add to current section content
                if current_section is not None:
                    section_content_lines.append(line)

        # Save last section
        if current_section is not None:
            current_section.content = "\n".join(section_content_lines)
            current_section.line_end = len(lines)
            sections.append(current_section)

        self._plan_sections = sections
        logger.info(f"Parsed {len(sections)} sections from plan")

        return sections

    def _generate_section_id(self, title: str, line_num: int) -> str:
        """Generate a unique section ID from title and line number."""
        # Clean title for ID
        clean_title = re.sub(r"[^\w\s-]", "", title.lower())
        clean_title = re.sub(r"[-\s]+", "_", clean_title)
        clean_title = clean_title[:50]  # Limit length

        return f"{clean_title}_L{line_num}"

    def find_section_by_id(self, section_id: str) -> Optional[PlanSection]:
        """Find a section by its ID."""
        sections = self.parse_plan_structure()

        for section in sections:
            if section.id == section_id:
                return section

        return None

    def find_sections_by_title(
        self, title: str, exact: bool = False
    ) -> List[PlanSection]:
        """
        Find sections by title (partial or exact match).

        Args:
            title: Title to search for
            exact: If True, only exact matches are returned

        Returns:
            List of matching PlanSection objects
        """
        sections = self.parse_plan_structure()
        matches = []

        for section in sections:
            if exact:
                if section.title == title:
                    matches.append(section)
            else:
                if title.lower() in section.title.lower():
                    matches.append(section)

        return matches

    def validate_plan_structure(self) -> ValidationResult:
        """
        Validate the plan structure for consistency and completeness.

        Returns:
            ValidationResult with any errors, warnings, or suggestions
        """
        sections = self.parse_plan_structure()
        result = ValidationResult(is_valid=True)

        # Check for duplicate section IDs (shouldn't happen but good to check)
        section_ids = [s.id for s in sections]
        duplicates = set([sid for sid in section_ids if section_ids.count(sid) > 1])
        if duplicates:
            result.is_valid = False
            result.errors.append(f"Duplicate section IDs found: {duplicates}")

        # Check header level consistency (no skipped levels)
        for i, section in enumerate(sections):
            if i > 0:
                prev_level = sections[i - 1].level
                if section.level > prev_level + 1:
                    result.warnings.append(
                        f"Header level jump at line {section.line_start}: "
                        f"from level {prev_level} to {section.level}"
                    )

        # Check for orphaned dependencies
        valid_ids = set(section_ids)
        for section in sections:
            for dep_id in section.dependencies:
                if dep_id not in valid_ids:
                    result.warnings.append(
                        f"Section '{section.id}' depends on non-existent section '{dep_id}'"
                    )

        # Check for sections with no content
        for section in sections:
            if len(section.content.strip()) < 50:  # Very short sections
                result.suggestions.append(
                    f"Section '{section.title}' at line {section.line_start} has minimal content"
                )

        return result

    def add_new_plan(
        self,
        title: str,
        content: str,
        position: str = "end",
        level: int = 2,
        parent_section_id: Optional[str] = None,
        rationale: str = "",
        confidence: float = 1.0,
        source: str = "manual",
    ) -> PlanModification:
        """
        Add a new plan section to the document.

        Args:
            title: Title of the new section
            content: Content of the new section
            position: Where to add ("end", "start", or "after:section_id")
            level: Header level (1-6)
            parent_section_id: ID of parent section (optional)
            rationale: Explanation for adding this section
            confidence: Confidence score (0-1)
            source: Source of modification (manual, ai, merge)

        Returns:
            PlanModification object describing the change
        """
        logger.info(f"Adding new plan section: '{title}'")

        # Create backup
        backup_path = self._create_backup()

        # Load current content
        current_content = self._load_plan(force_reload=True)
        lines = current_content.split("\n")

        # Generate section ID (temporary, will be updated after insertion)
        section_id = self._generate_section_id(title, 0)

        # Format new section
        header = "#" * level + " " + title
        new_section_lines = [header, ""] + content.strip().split("\n") + [""]
        new_section_text = "\n".join(new_section_lines)

        # Determine insertion point
        insert_index = 0

        if position == "end":
            insert_index = len(lines)

        elif position == "start":
            # Find first header
            for i, line in enumerate(lines):
                if line.startswith("#"):
                    insert_index = i
                    break

        elif position.startswith("after:"):
            # Insert after specified section
            target_id = position.split(":", 1)[1]
            target_section = self.find_section_by_id(target_id)

            if target_section:
                insert_index = target_section.line_end
            else:
                logger.warning(
                    f"Target section '{target_id}' not found, appending to end"
                )
                insert_index = len(lines)

        elif parent_section_id:
            # Insert as child of parent section
            parent = self.find_section_by_id(parent_section_id)
            if parent:
                # Find end of parent's immediate children
                insert_index = parent.line_end
            else:
                logger.warning(
                    f"Parent section '{parent_section_id}' not found, appending to end"
                )
                insert_index = len(lines)

        # Insert the new section
        lines.insert(insert_index, new_section_text)

        # Save modified content
        modified_content = "\n".join(lines)
        self._save_plan(modified_content)

        # Create modification record
        modification = PlanModification(
            operation="ADD",
            section_id=section_id,
            old_content=None,
            new_content=new_section_text,
            rationale=rationale,
            confidence=confidence,
            source=source,
            backup_path=str(backup_path),
        )

        # Log modification
        self._log_modification(modification)

        logger.info(f"✅ Added new section '{title}' at line {insert_index}")

        return modification

    def modify_existing_plan(
        self,
        section_id: str,
        new_content: Optional[str] = None,
        new_title: Optional[str] = None,
        append_content: Optional[str] = None,
        prepend_content: Optional[str] = None,
        rationale: str = "",
        confidence: float = 1.0,
        source: str = "manual",
    ) -> PlanModification:
        """
        Modify an existing plan section.

        Args:
            section_id: ID of the section to modify
            new_content: Complete new content (replaces existing)
            new_title: New title for the section
            append_content: Content to append to existing
            prepend_content: Content to prepend to existing
            rationale: Explanation for the modification
            confidence: Confidence score (0-1)
            source: Source of modification (manual, ai, merge)

        Returns:
            PlanModification object describing the change
        """
        logger.info(f"Modifying plan section: {section_id}")

        # Find the target section
        section = self.find_section_by_id(section_id)
        if not section:
            raise ValueError(f"Section '{section_id}' not found")

        # Create backup
        backup_path = self._create_backup()

        # Load current content
        current_content = self._load_plan(force_reload=True)
        lines = current_content.split("\n")

        # Save old content for the modification record
        old_content = "\n".join(lines[section.line_start - 1 : section.line_end])

        # Build new section content
        section_lines = lines[section.line_start - 1 : section.line_end]

        # Modify title if requested
        if new_title:
            # First line should be the header
            header_match = re.match(r"^(#{1,6})\s+(.+)$", section_lines[0])
            if header_match:
                section_lines[0] = header_match.group(1) + " " + new_title

        # Modify content if requested
        if new_content is not None:
            # Replace everything except the header
            header = section_lines[0]
            section_lines = [header, ""] + new_content.strip().split("\n")

        elif append_content:
            # Append to existing content
            section_lines.extend([""] + append_content.strip().split("\n"))

        elif prepend_content:
            # Prepend after header
            header = section_lines[0]
            rest = section_lines[1:]
            section_lines = (
                [header, ""] + prepend_content.strip().split("\n") + [""] + rest
            )

        # Replace section in full content
        new_section_text = "\n".join(section_lines)
        lines[section.line_start - 1 : section.line_end] = [new_section_text]

        # Save modified content
        modified_content = "\n".join(lines)
        self._save_plan(modified_content)

        # Create modification record
        modification = PlanModification(
            operation="MODIFY",
            section_id=section_id,
            old_content=old_content,
            new_content=new_section_text,
            rationale=rationale,
            confidence=confidence,
            source=source,
            backup_path=str(backup_path),
        )

        # Log modification
        self._log_modification(modification)

        logger.info(f"✅ Modified section '{section.title}'")

        return modification

    def delete_obsolete_plan(
        self,
        section_id: str,
        cascade: bool = False,
        archive: bool = True,
        rationale: str = "",
        confidence: float = 1.0,
        source: str = "manual",
    ) -> PlanModification:
        """
        Delete an obsolete plan section.

        Args:
            section_id: ID of the section to delete
            cascade: If True, also delete all child sections
            archive: If True, save deleted content to archive
            rationale: Explanation for deletion
            confidence: Confidence score (0-1)
            source: Source of modification (manual, ai, merge)

        Returns:
            PlanModification object describing the change
        """
        logger.info(f"Deleting plan section: {section_id}")

        # Find the target section
        section = self.find_section_by_id(section_id)
        if not section:
            raise ValueError(f"Section '{section_id}' not found")

        # Check for dependent sections
        sections = self.parse_plan_structure()
        dependents = [s for s in sections if section_id in s.dependencies]

        if dependents and not cascade:
            dependent_titles = [s.title for s in dependents]
            logger.warning(
                f"Section '{section.title}' has {len(dependents)} dependent sections: "
                f"{dependent_titles[:3]}{'...' if len(dependents) > 3 else ''}"
            )

        # Find all sections to delete (section + children if cascade)
        sections_to_delete = [section]

        if cascade:
            # Find all descendants
            def find_descendants(parent_id: str) -> List[PlanSection]:
                children = [s for s in sections if s.parent_id == parent_id]
                descendants = list(children)
                for child in children:
                    descendants.extend(find_descendants(child.id))
                return descendants

            descendants = find_descendants(section_id)
            sections_to_delete.extend(descendants)
            logger.info(f"Cascade delete: removing {len(sections_to_delete)} sections")

        # Create backup
        backup_path = self._create_backup()

        # Load current content
        current_content = self._load_plan(force_reload=True)
        lines = current_content.split("\n")

        # Archive deleted content if requested
        archive_path = None
        if archive:
            archive_dir = Path("workflow_state/plan_archives")
            archive_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            archive_name = f"deleted_{section_id}_{timestamp}.md"
            archive_path = archive_dir / archive_name

            archived_content = []
            for sec in sections_to_delete:
                archived_content.append(f"# Deleted Section: {sec.title}")
                archived_content.append(f"ID: {sec.id}")
                archived_content.append(f"Deleted: {datetime.now().isoformat()}")
                archived_content.append("")
                archived_content.append(
                    "\n".join(lines[sec.line_start - 1 : sec.line_end])
                )
                archived_content.append("\n" + "=" * 80 + "\n")

            archive_path.write_text("\n".join(archived_content))
            logger.info(f"Archived deleted content to: {archive_path}")

        # Save old content for modification record (just the main section)
        old_content = "\n".join(lines[section.line_start - 1 : section.line_end])

        # Sort sections to delete by line number (reverse order to avoid index shifting)
        sections_to_delete.sort(key=lambda s: s.line_start, reverse=True)

        # Delete sections
        for sec in sections_to_delete:
            # Remove the section
            del lines[sec.line_start - 1 : sec.line_end]

        # Save modified content
        modified_content = "\n".join(lines)
        self._save_plan(modified_content)

        # Create modification record
        modification = PlanModification(
            operation="DELETE",
            section_id=section_id,
            old_content=old_content,
            new_content=None,
            rationale=rationale,
            confidence=confidence,
            source=source,
            backup_path=str(backup_path),
        )

        # Add archive path to metadata
        if archive_path:
            modification.metadata = {
                "archive_path": str(archive_path),
                "cascade": cascade,
            }

        # Log modification
        self._log_modification(modification)

        logger.info(
            f"✅ Deleted section '{section.title}'{' (cascade)' if cascade else ''}"
        )

        return modification

    def merge_duplicate_plans(
        self,
        section_id_1: str,
        section_id_2: str,
        keep_section: str = "first",
        merge_strategy: str = "union",
        rationale: str = "",
        confidence: float = 1.0,
        source: str = "manual",
    ) -> PlanModification:
        """
        Merge two duplicate or similar plan sections.

        Args:
            section_id_1: ID of first section
            section_id_2: ID of second section
            keep_section: Which section to keep ("first", "second", or "new")
            merge_strategy: How to merge content ("union", "first", "second", "smart")
            rationale: Explanation for merge
            confidence: Confidence score (0-1)
            source: Source of modification (manual, ai, merge)

        Returns:
            PlanModification object describing the change
        """
        logger.info(f"Merging sections: {section_id_1} + {section_id_2}")

        # Find both sections
        section1 = self.find_section_by_id(section_id_1)
        section2 = self.find_section_by_id(section_id_2)

        if not section1:
            raise ValueError(f"Section '{section_id_1}' not found")
        if not section2:
            raise ValueError(f"Section '{section_id_2}' not found")

        # Create backup
        backup_path = self._create_backup()

        # Determine merged title
        if keep_section == "first":
            merged_title = section1.title
        elif keep_section == "second":
            merged_title = section2.title
        else:  # "new" or default
            # Create combined title
            if section1.title == section2.title:
                merged_title = section1.title
            else:
                merged_title = f"{section1.title} / {section2.title}"

        # Determine merged content based on strategy
        content1 = section1.content.split("\n")[1:]  # Skip header
        content2 = section2.content.split("\n")[1:]  # Skip header

        if merge_strategy == "union":
            # Combine all unique content
            merged_content_lines = content1.copy()

            # Add content from section2 that's not in section1
            for line in content2:
                line_stripped = line.strip()
                if line_stripped and not any(line_stripped in l for l in content1):
                    merged_content_lines.append(line)

        elif merge_strategy == "first":
            merged_content_lines = content1

        elif merge_strategy == "second":
            merged_content_lines = content2

        elif merge_strategy == "smart":
            # Smart merge: keep longer, more detailed content
            merged_content_lines = []

            # Combine and deduplicate
            all_lines = content1 + content2
            seen = set()

            for line in all_lines:
                line_stripped = line.strip()
                if line_stripped and line_stripped not in seen:
                    merged_content_lines.append(line)
                    seen.add(line_stripped)
                elif not line_stripped:
                    # Keep empty lines for formatting
                    merged_content_lines.append(line)

        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")

        merged_content = "\n".join(merged_content_lines)

        # Determine which section to keep and which to delete
        if keep_section == "first":
            keep_id = section_id_1
            delete_id = section_id_2
        elif keep_section == "second":
            keep_id = section_id_2
            delete_id = section_id_1
        else:  # "new"
            # Keep the first, delete the second
            keep_id = section_id_1
            delete_id = section_id_2

        # Modify the kept section with merged content
        self.modify_existing_plan(
            section_id=keep_id,
            new_title=(
                merged_title
                if merged_title != self.find_section_by_id(keep_id).title
                else None
            ),
            new_content=merged_content,
            rationale=f"Merged with {delete_id}: {rationale}",
            confidence=confidence,
            source=source,
        )

        # Refetch section to delete after modification (IDs may have changed due to line number shifts)
        sections_after_modify = self.parse_plan_structure(force_reload=True)
        delete_section = self.find_section_by_id(delete_id)

        if not delete_section:
            # If we can't find by ID (line numbers changed), try by title
            section2_matches = [
                s for s in sections_after_modify if s.title == section2.title
            ]
            if section2_matches:
                delete_section = section2_matches[0]
                delete_id = delete_section.id

        # Delete the other section if found
        if delete_section:
            delete_mod = self.delete_obsolete_plan(
                section_id=delete_id,
                archive=True,
                rationale=f"Merged into {keep_id}: {rationale}",
                confidence=confidence,
                source=source,
            )
        else:
            logger.warning(f"Could not find section to delete after merge: {delete_id}")

        # Create modification record
        modification = PlanModification(
            operation="MERGE",
            section_id=f"{section_id_1}+{section_id_2}",
            old_content=f"Section 1:\n{section1.content}\n\nSection 2:\n{section2.content}",
            new_content=merged_content,
            rationale=rationale,
            confidence=confidence,
            source=source,
            backup_path=str(backup_path),
        )

        modification.metadata = {
            "merged_sections": [section_id_1, section_id_2],
            "kept_section": keep_id,
            "deleted_section": delete_id,
            "merge_strategy": merge_strategy,
        }

        # Log modification
        self._log_modification(modification)

        logger.info(
            f"✅ Merged '{section1.title}' + '{section2.title}' into '{merged_title}'"
        )

        return modification

    def find_duplicate_sections(
        self, similarity_threshold: float = 0.8
    ) -> List[Tuple[PlanSection, PlanSection, float]]:
        """
        Find potential duplicate sections based on title similarity.

        Args:
            similarity_threshold: Minimum similarity score (0-1) to consider duplicates

        Returns:
            List of tuples (section1, section2, similarity_score)
        """
        from difflib import SequenceMatcher

        sections = self.parse_plan_structure()
        duplicates = []

        for i, sec1 in enumerate(sections):
            for sec2 in sections[i + 1 :]:
                # Calculate title similarity
                similarity = SequenceMatcher(
                    None, sec1.title.lower(), sec2.title.lower()
                ).ratio()

                if similarity >= similarity_threshold:
                    duplicates.append((sec1, sec2, similarity))

        # Sort by similarity (highest first)
        duplicates.sort(key=lambda x: x[2], reverse=True)

        return duplicates

    def get_modification_history(
        self,
        section_id: Optional[str] = None,
        operation: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        Get modification history, optionally filtered.

        Args:
            section_id: Filter by section ID
            operation: Filter by operation type (ADD, MODIFY, DELETE, MERGE)
            limit: Maximum number of results to return

        Returns:
            List of modification records
        """
        modifications = json.loads(self.modifications_log.read_text())

        # Apply filters
        if section_id:
            modifications = [m for m in modifications if m["section_id"] == section_id]

        if operation:
            modifications = [m for m in modifications if m["operation"] == operation]

        # Apply limit
        if limit:
            modifications = modifications[-limit:]

        return modifications

    def restore_from_backup(self, backup_path: Path) -> None:
        """
        Restore plan from a backup file.

        Args:
            backup_path: Path to the backup file
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        logger.warning(f"Restoring plan from backup: {backup_path}")

        # Create a backup of the current state before restoring
        pre_restore_backup = self._create_backup()
        logger.info(f"Created pre-restore backup: {pre_restore_backup}")

        # Restore from backup
        shutil.copy2(backup_path, self.plan_path)

        # Clear cache
        self._plan_content = None
        self._plan_sections = None
        self._last_parsed = None

        logger.info(f"✅ Restored plan from {backup_path}")

    def generate_diff(self, old_content: str, new_content: str) -> str:
        """
        Generate a simple diff between old and new content.

        Args:
            old_content: Original content
            new_content: Modified content

        Returns:
            Diff string showing changes
        """
        old_lines = old_content.split("\n")
        new_lines = new_content.split("\n")

        diff_lines = []
        diff_lines.append("--- Original")
        diff_lines.append("+++ Modified")
        diff_lines.append("")

        # Simple line-by-line diff
        max_lines = max(len(old_lines), len(new_lines))

        for i in range(max_lines):
            old_line = old_lines[i] if i < len(old_lines) else ""
            new_line = new_lines[i] if i < len(new_lines) else ""

            if old_line != new_line:
                if old_line:
                    diff_lines.append(f"- {old_line}")
                if new_line:
                    diff_lines.append(f"+ {new_line}")

        return "\n".join(diff_lines)

    def get_statistics(self) -> Dict:
        """Get statistics about the plan and modifications."""
        sections = self.parse_plan_structure()
        modifications = self.get_modification_history()

        stats = {
            "total_sections": len(sections),
            "sections_by_level": {},
            "total_modifications": len(modifications),
            "modifications_by_operation": {},
            "modifications_by_source": {},
            "latest_modification": (
                modifications[-1]["timestamp"] if modifications else None
            ),
            "backup_count": len(list(self.backup_dir.glob("*.backup.md"))),
        }

        # Count sections by level
        for section in sections:
            level = section.level
            stats["sections_by_level"][level] = (
                stats["sections_by_level"].get(level, 0) + 1
            )

        # Count modifications by operation
        for mod in modifications:
            op = mod["operation"]
            stats["modifications_by_operation"][op] = (
                stats["modifications_by_operation"].get(op, 0) + 1
            )

        # Count modifications by source
        for mod in modifications:
            source = mod["source"]
            stats["modifications_by_source"][source] = (
                stats["modifications_by_source"].get(source, 0) + 1
            )

        return stats


def main():
    """CLI interface for IntelligentPlanEditor."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Intelligent Plan Editor - CRUD operations for implementation plans"
    )
    parser.add_argument(
        "plan_path", type=Path, help="Path to the implementation plan file"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Parse command
    parse_parser = subparsers.add_parser(
        "parse", help="Parse and display plan structure"
    )
    parse_parser.add_argument(
        "--validate", action="store_true", help="Validate plan structure"
    )

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new section")
    add_parser.add_argument("--title", required=True, help="Section title")
    add_parser.add_argument("--content", required=True, help="Section content")
    add_parser.add_argument(
        "--position", default="end", help="Position (end, start, after:section_id)"
    )
    add_parser.add_argument("--level", type=int, default=2, help="Header level (1-6)")
    add_parser.add_argument("--rationale", default="", help="Reason for adding")

    # Modify command
    modify_parser = subparsers.add_parser("modify", help="Modify an existing section")
    modify_parser.add_argument(
        "--section-id", required=True, help="Section ID to modify"
    )
    modify_parser.add_argument("--new-title", help="New title")
    modify_parser.add_argument("--new-content", help="New content (replaces existing)")
    modify_parser.add_argument("--append", help="Content to append")
    modify_parser.add_argument("--prepend", help="Content to prepend")
    modify_parser.add_argument(
        "--rationale", default="", help="Reason for modification"
    )

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a section")
    delete_parser.add_argument(
        "--section-id", required=True, help="Section ID to delete"
    )
    delete_parser.add_argument(
        "--cascade", action="store_true", help="Delete children too"
    )
    delete_parser.add_argument(
        "--no-archive", action="store_true", help="Skip archiving"
    )
    delete_parser.add_argument("--rationale", default="", help="Reason for deletion")

    # Merge command
    merge_parser = subparsers.add_parser("merge", help="Merge two sections")
    merge_parser.add_argument("--section-id-1", required=True, help="First section ID")
    merge_parser.add_argument("--section-id-2", required=True, help="Second section ID")
    merge_parser.add_argument(
        "--keep",
        default="first",
        choices=["first", "second", "new"],
        help="Which section to keep",
    )
    merge_parser.add_argument(
        "--strategy",
        default="union",
        choices=["union", "first", "second", "smart"],
        help="Merge strategy",
    )
    merge_parser.add_argument("--rationale", default="", help="Reason for merge")

    # Find duplicates command
    find_dupes_parser = subparsers.add_parser(
        "find-duplicates", help="Find duplicate sections"
    )
    find_dupes_parser.add_argument(
        "--threshold", type=float, default=0.8, help="Similarity threshold (0-1)"
    )

    # History command
    history_parser = subparsers.add_parser("history", help="View modification history")
    history_parser.add_argument("--section-id", help="Filter by section ID")
    history_parser.add_argument(
        "--operation", help="Filter by operation (ADD, MODIFY, etc.)"
    )
    history_parser.add_argument("--limit", type=int, help="Maximum results")

    # Stats command
    subparsers.add_parser("stats", help="Display plan statistics")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("backup_path", type=Path, help="Path to backup file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize editor
    editor = IntelligentPlanEditor(args.plan_path)

    # Execute command
    if args.command == "parse":
        sections = editor.parse_plan_structure()

        print(f"\n📄 Plan Structure: {args.plan_path}")
        print(f"{'='*80}\n")

        for section in sections:
            indent = "  " * (section.level - 1)
            print(f"{indent}{'#' * section.level} {section.title}")
            print(f"{indent}   ID: {section.id}")
            print(f"{indent}   Lines: {section.line_start}-{section.line_end}")
            if section.parent_id:
                print(f"{indent}   Parent: {section.parent_id}")
            print()

        if args.validate:
            print(f"\n🔍 Validation Results:")
            print(f"{'='*80}\n")

            result = editor.validate_plan_structure()

            if result.is_valid:
                print("✅ Plan structure is valid")
            else:
                print("❌ Plan structure has errors:")
                for error in result.errors:
                    print(f"  - {error}")

            if result.warnings:
                print("\n⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")

            if result.suggestions:
                print("\n💡 Suggestions:")
                for suggestion in result.suggestions:
                    print(f"  - {suggestion}")

    elif args.command == "add":
        modification = editor.add_new_plan(
            title=args.title,
            content=args.content,
            position=args.position,
            level=args.level,
            rationale=args.rationale,
        )

        print(f"\n✅ Added new section: {args.title}")
        print(f"   Backup: {modification.backup_path}")

    elif args.command == "modify":
        modification = editor.modify_existing_plan(
            section_id=args.section_id,
            new_title=args.new_title,
            new_content=args.new_content,
            append_content=args.append,
            prepend_content=args.prepend,
            rationale=args.rationale,
        )

        print(f"\n✅ Modified section: {args.section_id}")
        print(f"   Backup: {modification.backup_path}")

        # Show diff
        if modification.old_content and modification.new_content:
            print(f"\n📝 Changes:")
            print(
                editor.generate_diff(modification.old_content, modification.new_content)
            )

    elif args.command == "delete":
        modification = editor.delete_obsolete_plan(
            section_id=args.section_id,
            cascade=args.cascade,
            archive=not args.no_archive,
            rationale=args.rationale,
        )

        print(f"\n✅ Deleted section: {args.section_id}")
        print(f"   Backup: {modification.backup_path}")

        if modification.metadata and "archive_path" in modification.metadata:
            print(f"   Archive: {modification.metadata['archive_path']}")

        if modification.metadata and modification.metadata.get("cascade"):
            print(f"   Cascade: deleted children sections too")

    elif args.command == "merge":
        modification = editor.merge_duplicate_plans(
            section_id_1=args.section_id_1,
            section_id_2=args.section_id_2,
            keep_section=args.keep,
            merge_strategy=args.strategy,
            rationale=args.rationale,
        )

        print(f"\n✅ Merged sections: {args.section_id_1} + {args.section_id_2}")
        print(f"   Backup: {modification.backup_path}")

        if modification.metadata:
            print(f"   Kept: {modification.metadata['kept_section']}")
            print(f"   Deleted: {modification.metadata['deleted_section']}")
            print(f"   Strategy: {modification.metadata['merge_strategy']}")

    elif args.command == "find-duplicates":
        duplicates = editor.find_duplicate_sections(args.threshold)

        print(f"\n🔍 Potential Duplicate Sections")
        print(f"{'='*80}\n")

        if duplicates:
            print(
                f"Found {len(duplicates)} potential duplicates (similarity >= {args.threshold:.0%}):\n"
            )

            for sec1, sec2, similarity in duplicates:
                print(f"Similarity: {similarity:.1%}")
                print(f"  Section 1: {sec1.title}")
                print(f"    ID: {sec1.id}")
                print(f"    Lines: {sec1.line_start}-{sec1.line_end}")
                print(f"  Section 2: {sec2.title}")
                print(f"    ID: {sec2.id}")
                print(f"    Lines: {sec2.line_start}-{sec2.line_end}")
                print()
        else:
            print(f"No duplicates found with similarity >= {args.threshold:.0%}")

    elif args.command == "history":
        modifications = editor.get_modification_history(
            section_id=args.section_id, operation=args.operation, limit=args.limit
        )

        print(f"\n📜 Modification History")
        print(f"{'='*80}\n")

        for mod in modifications:
            print(f"Operation: {mod['operation']}")
            print(f"Section: {mod['section_id']}")
            print(f"Source: {mod['source']}")
            print(f"Timestamp: {mod['timestamp']}")
            if mod["rationale"]:
                print(f"Rationale: {mod['rationale']}")
            print(f"Backup: {mod['backup_path']}")
            print()

    elif args.command == "stats":
        stats = editor.get_statistics()

        print(f"\n📊 Plan Statistics")
        print(f"{'='*80}\n")

        print(f"Total Sections: {stats['total_sections']}")
        print(f"Sections by Level:")
        for level, count in sorted(stats["sections_by_level"].items()):
            print(f"  Level {level}: {count}")

        print(f"\nTotal Modifications: {stats['total_modifications']}")
        if stats["modifications_by_operation"]:
            print(f"By Operation:")
            for op, count in stats["modifications_by_operation"].items():
                print(f"  {op}: {count}")

        if stats["modifications_by_source"]:
            print(f"By Source:")
            for source, count in stats["modifications_by_source"].items():
                print(f"  {source}: {count}")

        print(f"\nBackups: {stats['backup_count']}")
        if stats["latest_modification"]:
            print(f"Latest Modification: {stats['latest_modification']}")

    elif args.command == "restore":
        editor.restore_from_backup(args.backup_path)
        print(f"\n✅ Restored plan from: {args.backup_path}")


if __name__ == "__main__":
    main()
