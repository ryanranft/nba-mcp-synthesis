#!/usr/bin/env python3
"""
Enhanced Project Code Analyzer

Deeply analyzes project codebases to provide comprehensive context for AI book analysis.
Supports smart sampling from large directories and multi-project configurations.

Features:
- Full file tree generation (with exclusions)
- Smart sampling: randomly reads 20 files from directories with >20 files
- Architecture extraction (classes, functions, imports)
- Recent git commit analysis
- Completion status assessment

Author: NBA MCP Synthesis System
Version: 1.0
Date: 2025-10-21
"""

import os
import sys
import json
import random
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EnhancedProjectScanner:
    """
    Advanced project scanner that builds comprehensive codebase context.

    Capabilities:
    - Full directory tree with smart exclusions
    - Random sampling from large directories (20 files)
    - Complete file content extraction
    - Architecture analysis (classes, functions, imports)
    - Git history integration
    - Project completion assessment
    """

    def __init__(self, config_path: str):
        """
        Initialize scanner with project configuration.

        Args:
            config_path: Path to project config JSON file
        """
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.project_path = Path(self.config['project_path'])
        self.exclude_dirs = set(self.config['exclude_dirs'])
        self.sampling_config = self.config['sampling_config']

        logger.info(f"🔍 Initialized scanner for: {self.config['project_name']}")
        logger.info(f"📂 Project path: {self.project_path}")

    def scan_project_deeply(self) -> Dict:
        """
        Perform deep project analysis.

        Returns:
            Comprehensive project context dictionary
        """
        logger.info("🚀 Starting deep project scan...")

        context = {
            'project_info': self._get_project_info(),
            'file_tree': self._build_file_tree(),
            'sampled_files': self._sample_and_read_files(),
            'architecture': self._extract_architecture(),
            'recent_commits': self._get_recent_commits(),
            'completion_status': self._assess_completion(),
            'statistics': self._gather_statistics(),
            'data_inventory': self._scan_data_inventory()
        }

        logger.info("✅ Deep scan complete!")
        return context

    def _get_project_info(self) -> Dict:
        """Extract basic project information from config."""
        return {
            'id': self.config['project_id'],
            'name': self.config['project_name'],
            'sport': self.config['sport'],
            'league': self.config.get('league', 'N/A'),
            'goals': self.config['project_goals'],
            'phase': self.config['current_phase'],
            'technologies': self.config['key_technologies']
        }

    def _build_file_tree(self) -> str:
        """
        Build comprehensive file tree string (excluding specified directories).

        Returns:
            Formatted tree string
        """
        logger.info("📋 Building file tree...")

        tree_lines = []

        def add_tree_line(path: Path, prefix: str = "", is_last: bool = True):
            """Recursively build tree structure."""
            if path.name in self.exclude_dirs:
                return

            connector = "└── " if is_last else "├── "
            tree_lines.append(f"{prefix}{connector}{path.name}")

            if path.is_dir():
                try:
                    children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name))
                    children = [c for c in children if c.name not in self.exclude_dirs]

                    for i, child in enumerate(children):
                        is_last_child = i == len(children) - 1
                        extension = "    " if is_last else "│   "
                        add_tree_line(child, prefix + extension, is_last_child)
                except PermissionError:
                    pass

        tree_lines.append(f"{self.project_path.name}/")
        for item in sorted(self.project_path.iterdir(), key=lambda p: (not p.is_dir(), p.name)):
            if item.name not in self.exclude_dirs:
                add_tree_line(item, "", item == list(self.project_path.iterdir())[-1])

        tree_str = "\n".join(tree_lines[:500])  # Limit to 500 lines for token efficiency
        if len(tree_lines) > 500:
            tree_str += f"\n... ({len(tree_lines) - 500} more items truncated)"

        logger.info(f"  ✅ Tree built: {len(tree_lines)} items")
        return tree_str

    def _sample_and_read_files(self) -> Dict:
        """
        Smart file sampling: randomly read 20 files from directories with >20 files.

        Returns:
            Dictionary mapping file paths to their complete contents
        """
        logger.info("📖 Sampling and reading files...")

        sampled = {}
        file_types = self.sampling_config['file_types']
        sample_size = self.sampling_config['sample_size']
        threshold = self.sampling_config['large_dir_threshold']
        priority_dirs = set(self.sampling_config['priority_dirs'])

        # Group files by directory
        dir_files = defaultdict(list)

        for pattern in file_types:
            for file_path in self.project_path.rglob(pattern):
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in self.exclude_dirs):
                    continue

                dir_path = file_path.parent
                dir_files[dir_path].append(file_path)

        # Process each directory
        for dir_path, files in dir_files.items():
            dir_name = dir_path.relative_to(self.project_path)
            is_priority = any(priority in str(dir_name) for priority in priority_dirs)

            if len(files) > threshold:
                # Large directory: randomly sample
                selected = random.sample(files, min(sample_size, len(files)))
                logger.info(f"  📂 {dir_name}: Sampled {len(selected)}/{len(files)} files")
            else:
                # Small directory: read all
                selected = files
                logger.info(f"  📂 {dir_name}: Reading all {len(selected)} files")

            # Read selected files
            for file_path in selected:
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    sampled[str(file_path.relative_to(self.project_path))] = {
                        'content': content,
                        'size_bytes': file_path.stat().st_size,
                        'lines': len(content.splitlines()),
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        'priority': is_priority
                    }
                except Exception as e:
                    logger.warning(f"  ⚠️  Could not read {file_path}: {e}")

        logger.info(f"  ✅ Read {len(sampled)} files completely")
        return sampled

    def _extract_architecture(self) -> Dict:
        """
        Extract architectural information from sampled files.

        Returns:
            Architecture summary (classes, functions, imports)
        """
        logger.info("🏗️  Extracting architecture...")

        arch = {
            'classes': [],
            'functions': [],
            'imports': defaultdict(int),
            'modules': []
        }

        # This is a simplified extraction - you could use AST for more precision
        for file_path, file_data in getattr(self, '_sampled_files_cache', {}).items():
            if not file_path.endswith('.py'):
                continue

            content = file_data['content']
            lines = content.splitlines()

            for line in lines:
                line = line.strip()

                # Extract class definitions
                if line.startswith('class '):
                    class_name = line.split('class ')[1].split('(')[0].split(':')[0].strip()
                    arch['classes'].append({
                        'name': class_name,
                        'file': file_path
                    })

                # Extract function definitions
                elif line.startswith('def '):
                    func_name = line.split('def ')[1].split('(')[0].strip()
                    arch['functions'].append({
                        'name': func_name,
                        'file': file_path
                    })

                # Extract imports
                elif line.startswith('import ') or line.startswith('from '):
                    if 'import ' in line:
                        module = line.split('import ')[1].split(' ')[0].split('.')[0]
                        arch['imports'][module] += 1

        logger.info(f"  ✅ Found {len(arch['classes'])} classes, {len(arch['functions'])} functions")
        return dict(arch)

    def _get_recent_commits(self, limit: int = 20) -> List[Dict]:
        """
        Get recent git commits.

        Args:
            limit: Number of commits to retrieve

        Returns:
            List of commit dictionaries
        """
        logger.info(f"📝 Retrieving last {limit} commits...")

        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--pretty=format:%H|%an|%ae|%ad|%s'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                logger.warning("  ⚠️  Not a git repository or git not available")
                return []

            commits = []
            for line in result.stdout.splitlines():
                if not line:
                    continue
                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        'hash': parts[0][:8],
                        'author': parts[1],
                        'date': parts[3],
                        'message': parts[4]
                    })

            logger.info(f"  ✅ Retrieved {len(commits)} commits")
            return commits

        except Exception as e:
            logger.warning(f"  ⚠️  Failed to get commits: {e}")
            return []

    def _assess_completion(self) -> Dict:
        """
        Assess project completion status based on common patterns.

        Returns:
            Completion assessment dictionary
        """
        logger.info("📊 Assessing completion status...")

        # Count TODO/FIXME comments in sampled files
        todos = 0
        fixmes = 0

        for file_data in getattr(self, '_sampled_files_cache', {}).values():
            content = file_data['content'].lower()
            todos += content.count('todo')
            fixmes += content.count('fixme')

        assessment = {
            'todos_found': todos,
            'fixmes_found': fixmes,
            'issues_estimate': todos + fixmes,
            'maturity': self._estimate_maturity(todos, fixmes)
        }

        logger.info(f"  ✅ Found {todos} TODOs, {fixmes} FIXMEs")
        return assessment

    def _estimate_maturity(self, todos: int, fixmes: int) -> str:
        """Estimate project maturity based on issue count."""
        issues = todos + fixmes

        if issues == 0:
            return "Production-ready (no known issues)"
        elif issues < 10:
            return "Mature (few remaining items)"
        elif issues < 50:
            return "Active development (moderate backlog)"
        else:
            return "Early stage (significant work remaining)"

    def _gather_statistics(self) -> Dict:
        """
        Gather project statistics.

        Returns:
            Statistics dictionary
        """
        sampled = getattr(self, '_sampled_files_cache', {})

        total_lines = sum(f['lines'] for f in sampled.values())
        total_size = sum(f['size_bytes'] for f in sampled.values())

        return {
            'files_sampled': len(sampled),
            'total_lines': total_lines,
            'total_size_mb': round(total_size / 1_000_000, 2),
            'avg_file_size_kb': round((total_size / len(sampled) / 1000) if sampled else 0, 2)
        }

    def _scan_data_inventory(self) -> Optional[Dict]:
        """
        Scan data inventory if configured.

        Returns:
            Data inventory context or None if not configured
        """
        # Check if data inventory is enabled in config
        data_inventory_config = self.config.get('data_inventory', {})

        if not data_inventory_config.get('enabled', False):
            logger.info("📊 Data inventory disabled in config")
            return None

        inventory_path = data_inventory_config.get('inventory_path')

        if not inventory_path:
            logger.warning("⚠️ Data inventory enabled but no inventory_path configured")
            return None

        try:
            # Import and use the data inventory scanner (handle both direct and module execution)
            try:
                from scripts.data_inventory_scanner import DataInventoryScanner
            except ImportError:
                # Try local import if running as module
                import sys
                script_dir = Path(__file__).parent
                if str(script_dir) not in sys.path:
                    sys.path.insert(0, str(script_dir))
                from data_inventory_scanner import DataInventoryScanner

            logger.info(f"📊 Scanning data inventory: {inventory_path}")
            scanner = DataInventoryScanner(inventory_path)
            inventory = scanner.scan_full_inventory()

            logger.info("✅ Data inventory scan complete")
            return inventory

        except ImportError as e:
            logger.warning(f"⚠️ DataInventoryScanner not available (import failed): {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Data inventory scan failed: {e}")
            return None

    def format_for_prompt(self, context: Dict, max_chars: int = 50000) -> str:
        """
        Format project context as a prompt string for AI models.

        Args:
            context: Project context dictionary
            max_chars: Maximum characters to include

        Returns:
            Formatted prompt string
        """
        sections = []

        # Project Info
        info = context['project_info']
        sections.append(f"**Project**: {info['name']} ({info['sport']} - {info['league']})")
        sections.append(f"**Phase**: {info['phase']}")
        sections.append(f"**Goals**:\n" + "\n".join(f"- {g}" for g in info['goals']))
        sections.append(f"**Technologies**: {', '.join(info['technologies'])}")

        # File Tree
        sections.append(f"\n**File Structure**:\n```\n{context['file_tree']}\n```")

        # Sampled Code (truncated if needed)
        sampled = context['sampled_files']
        sections.append(f"\n**Code Samples ({len(sampled)} files)**:")

        char_count = sum(len(s) for s in sections)

        for file_path, file_data in sorted(sampled.items(), key=lambda x: x[1].get('priority', False), reverse=True):
            if char_count > max_chars:
                sections.append(f"\n... ({len(sampled) - len([s for s in sections if file_path in s])} more files truncated)")
                break

            file_section = f"\n**File**: `{file_path}` ({file_data['lines']} lines)\n```python\n{file_data['content'][:2000]}\n```"
            if len(file_data['content']) > 2000:
                file_section += f"\n... (truncated, {file_data['lines']} total lines)"

            sections.append(file_section)
            char_count += len(file_section)

        # Architecture
        arch = context['architecture']
        sections.append(f"\n**Architecture Summary**:")
        sections.append(f"- Classes: {len(arch['classes'])} (e.g., {', '.join([c['name'] for c in arch['classes'][:5]])}...)")
        sections.append(f"- Functions: {len(arch['functions'])}")
        sections.append(f"- Key imports: {', '.join(list(arch['imports'].keys())[:10])}")

        # Recent Work
        commits = context['recent_commits'][:5]
        sections.append(f"\n**Recent Development (last {len(commits)} commits)**:")
        for commit in commits:
            sections.append(f"- [{commit['hash']}] {commit['message']} ({commit['date']})")

        # Status
        status = context['completion_status']
        sections.append(f"\n**Completion Status**:")
        sections.append(f"- Maturity: {status['maturity']}")
        sections.append(f"- TODOs: {status['todos_found']}, FIXMEs: {status['fixmes_found']}")

        # Data Inventory (if available)
        data_inventory = context.get('data_inventory')
        if data_inventory and data_inventory.get('summary_for_ai'):
            sections.append(f"\n{data_inventory['summary_for_ai']}")

        return "\n".join(sections)


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Deep Project Code Analyzer')
    parser.add_argument('--config', required=True, help='Path to project config JSON')
    parser.add_argument('--output', help='Output file for analysis (JSON)')
    args = parser.parse_args()

    scanner = EnhancedProjectScanner(args.config)
    context = scanner.scan_project_deeply()

    if args.output:
        with open(args.output, 'w') as f:
            # Can't serialize Path objects, so convert to strings
            json.dump(context, f, indent=2, default=str)
        print(f"✅ Analysis saved to: {args.output}")
    else:
        # Print formatted version
        print("\n" + "="*80)
        print(scanner.format_for_prompt(context))
        print("="*80)


if __name__ == '__main__':
    main()
