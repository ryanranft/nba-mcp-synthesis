"""
File Tools for MCP Server
Provides tools for reading and searching project files
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import fnmatch
from datetime import datetime

logger = logging.getLogger(__name__)


class FileTools:
    """Tools for project file operations"""

    def __init__(self, project_root: str):
        """
        Initialize file tools with project root.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root).resolve()

        if not self.project_root.exists():
            logger.warning(f"Project root does not exist: {project_root}")

    def _validate_path(
        self, file_path: str
    ) -> tuple[bool, Optional[Path], Optional[str]]:
        """
        Validate file path to prevent path traversal attacks.

        Args:
            file_path: Path to validate

        Returns:
            Tuple of (is_valid, resolved_path, error_message)
        """
        try:
            # Convert to absolute path
            if os.path.isabs(file_path):
                path = Path(file_path).resolve()
            else:
                path = (self.project_root / file_path).resolve()

            # Check if path is within project root
            try:
                path.relative_to(self.project_root)
            except ValueError:
                return False, None, f"Path outside project root: {file_path}"

            return True, path, None

        except Exception as e:
            return False, None, f"Invalid path: {str(e)}"

    async def read_project_file(
        self, file_path: str, max_lines: int = 500
    ) -> Dict[str, Any]:
        """
        Read a file from the project directory.

        Args:
            file_path: Path to file (relative to project root or absolute)
            max_lines: Maximum number of lines to read (default: 500)

        Returns:
            Dict with file content or error
        """
        try:
            # Validate path
            is_valid, path, error = self._validate_path(file_path)
            if not is_valid:
                logger.warning(f"Invalid path access attempt: {file_path}")
                return {"success": False, "error": error, "file_path": file_path}

            # Check if file exists
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "file_path": str(path),
                }

            # Check if it's a file (not directory)
            if not path.is_file():
                return {
                    "success": False,
                    "error": f"Not a file: {file_path}",
                    "file_path": str(path),
                }

            # Get file stats
            stats = path.stat()
            file_size = stats.st_size

            # Read file content
            logger.info(f"Reading file: {path} (max_lines={max_lines})")

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip("\n"))

                content = "\n".join(lines)
                total_lines = i + 1

            # Check if file was truncated
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                actual_lines = sum(1 for _ in f)

            truncated = actual_lines > max_lines

            return {
                "success": True,
                "file_path": str(path),
                "relative_path": str(path.relative_to(self.project_root)),
                "content": content,
                "lines_read": total_lines,
                "total_lines": actual_lines,
                "truncated": truncated,
                "file_size": file_size,
                "extension": path.suffix,
            }

        except Exception as e:
            logger.error(f"Error reading file: {e}", exc_info=True)
            return {"success": False, "error": str(e), "file_path": file_path}

    async def search_project_files(
        self,
        pattern: str,
        file_types: List[str] = [".py", ".sql"],
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for files in the project directory.

        Args:
            pattern: Glob pattern to search for (e.g., "*test*", "config*")
            file_types: List of file extensions to include (default: [".py", ".sql"])
            max_results: Maximum number of results to return (default: 50)

        Returns:
            Dict with list of matching files or error
        """
        try:
            logger.info(f"Searching for files: pattern='{pattern}', types={file_types}")

            matching_files = []

            # Walk through project directory
            for root, dirs, files in os.walk(self.project_root):
                # Skip hidden directories and common excludes
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["__pycache__", "node_modules", "venv", ".git"]
                ]

                for file in files:
                    # Check if file matches pattern
                    if fnmatch.fnmatch(file, pattern):
                        # Check file type
                        file_ext = Path(file).suffix
                        if not file_types or file_ext in file_types:
                            file_path = Path(root) / file
                            stats = file_path.stat()

                            matching_files.append(
                                {
                                    "path": str(file_path),
                                    "relative_path": str(
                                        file_path.relative_to(self.project_root)
                                    ),
                                    "name": file,
                                    "size": stats.st_size,
                                    "modified": datetime.fromtimestamp(
                                        stats.st_mtime
                                    ).isoformat(),
                                    "extension": file_ext,
                                }
                            )

                            # Stop if max results reached
                            if len(matching_files) >= max_results:
                                break

                if len(matching_files) >= max_results:
                    break

            logger.info(f"Found {len(matching_files)} matching files")

            return {
                "success": True,
                "pattern": pattern,
                "file_types": file_types,
                "file_count": len(matching_files),
                "files": matching_files,
                "truncated": len(matching_files) >= max_results,
            }

        except Exception as e:
            logger.error(f"Error searching files: {e}", exc_info=True)
            return {"success": False, "error": str(e), "pattern": pattern}

    async def get_file_summary(self, file_path: str) -> Dict[str, Any]:
        """
        Get metadata and summary information about a file.

        Args:
            file_path: Path to file (relative to project root or absolute)

        Returns:
            Dict with file metadata or error
        """
        try:
            # Validate path
            is_valid, path, error = self._validate_path(file_path)
            if not is_valid:
                return {"success": False, "error": error, "file_path": file_path}

            # Check if file exists
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "file_path": str(path),
                }

            # Check if it's a file
            if not path.is_file():
                return {
                    "success": False,
                    "error": f"Not a file: {file_path}",
                    "file_path": str(path),
                }

            # Get file stats
            stats = path.stat()

            # Count lines for text files
            line_count = None
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    line_count = sum(1 for _ in f)
            except:
                pass  # Not a text file or unreadable

            return {
                "success": True,
                "file_path": str(path),
                "relative_path": str(path.relative_to(self.project_root)),
                "name": path.name,
                "extension": path.suffix,
                "size": stats.st_size,
                "size_mb": round(stats.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stats.st_atime).isoformat(),
                "line_count": line_count,
                "is_text": line_count is not None,
            }

        except Exception as e:
            logger.error(f"Error getting file summary: {e}", exc_info=True)
            return {"success": False, "error": str(e), "file_path": file_path}

    async def list_directory(
        self, dir_path: str = "", recursive: bool = False, max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        List contents of a directory in the project.

        Args:
            dir_path: Directory path (relative to project root, default: root)
            recursive: Whether to list recursively (default: False)
            max_depth: Maximum depth for recursive listing (default: 2)

        Returns:
            Dict with directory listing or error
        """
        try:
            # Validate path
            is_valid, path, error = self._validate_path(dir_path if dir_path else ".")
            if not is_valid:
                return {"success": False, "error": error, "dir_path": dir_path}

            # Check if directory exists
            if not path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {dir_path}",
                    "dir_path": str(path),
                }

            # Check if it's a directory
            if not path.is_dir():
                return {
                    "success": False,
                    "error": f"Not a directory: {dir_path}",
                    "dir_path": str(path),
                }

            logger.info(f"Listing directory: {path} (recursive={recursive})")

            files = []
            directories = []

            if recursive:
                # Recursive listing with depth limit
                for root, dirs, filenames in os.walk(path):
                    # Calculate current depth
                    depth = len(Path(root).relative_to(path).parts)
                    if depth >= max_depth:
                        dirs.clear()  # Don't descend further
                        continue

                    # Skip hidden directories
                    dirs[:] = [
                        d
                        for d in dirs
                        if not d.startswith(".")
                        and d not in ["__pycache__", "node_modules", "venv", ".git"]
                    ]

                    for d in dirs:
                        dir_full_path = Path(root) / d
                        directories.append(
                            {
                                "path": str(dir_full_path),
                                "relative_path": str(
                                    dir_full_path.relative_to(self.project_root)
                                ),
                                "name": d,
                                "depth": depth + 1,
                            }
                        )

                    for f in filenames:
                        if not f.startswith("."):
                            file_full_path = Path(root) / f
                            stats = file_full_path.stat()
                            files.append(
                                {
                                    "path": str(file_full_path),
                                    "relative_path": str(
                                        file_full_path.relative_to(self.project_root)
                                    ),
                                    "name": f,
                                    "size": stats.st_size,
                                    "extension": Path(f).suffix,
                                    "depth": depth + 1,
                                }
                            )
            else:
                # Non-recursive listing
                for item in path.iterdir():
                    if item.name.startswith("."):
                        continue

                    if item.is_dir():
                        directories.append(
                            {
                                "path": str(item),
                                "relative_path": str(
                                    item.relative_to(self.project_root)
                                ),
                                "name": item.name,
                            }
                        )
                    else:
                        stats = item.stat()
                        files.append(
                            {
                                "path": str(item),
                                "relative_path": str(
                                    item.relative_to(self.project_root)
                                ),
                                "name": item.name,
                                "size": stats.st_size,
                                "extension": item.suffix,
                            }
                        )

            return {
                "success": True,
                "directory": str(path),
                "relative_directory": str(path.relative_to(self.project_root)),
                "file_count": len(files),
                "directory_count": len(directories),
                "files": files,
                "directories": directories,
                "recursive": recursive,
            }

        except Exception as e:
            logger.error(f"Error listing directory: {e}", exc_info=True)
            return {"success": False, "error": str(e), "dir_path": dir_path}
