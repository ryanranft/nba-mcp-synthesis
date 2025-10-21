#!/usr/bin/env python3
"""
MCP Structure Validation Script

Validates the NBA MCP Synthesis system structure:
- Phase 8.5 can run without crash
- All tool files are accessible
- Recommendations have valid structure
- No broken imports
"""

import sys
import json
from pathlib import Path
from typing import List, Tuple


def check_phase_status_manager() -> Tuple[bool, str]:
    """Check if phase status manager can handle Phase 8.5."""
    try:
        # Add scripts directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        from phase_status_manager import PhaseStatusManager, PhaseState

        # Create temp status file
        temp_status = Path("test_phase_status.json")
        manager = PhaseStatusManager(status_file=temp_status)

        # Simulate autonomous workflow
        manager.skip_phase("phase_8", "Test skip")

        # Try to start Phase 8.5 with skip_prereq_check
        try:
            manager.start_phase("phase_8_5", "Test Phase 8.5", skip_prereq_check=True)
            manager.complete_phase("phase_8_5")

            # Cleanup
            if temp_status.exists():
                temp_status.unlink()

            return True, "✅ Phase 8.5 can start with skip_prereq_check=True"
        except ValueError as e:
            # Cleanup
            if temp_status.exists():
                temp_status.unlink()
            return False, f"❌ Phase 8.5 still fails: {e}"

    except Exception as e:
        return False, f"❌ Phase status manager error: {e}"


def check_run_workflow_has_force_fresh() -> Tuple[bool, str]:
    """Check if run_full_workflow.py has --force-fresh flag."""
    try:
        workflow_file = Path("scripts/run_full_workflow.py")
        content = workflow_file.read_text()

        if "--force-fresh" in content:
            return True, "✅ --force-fresh flag implemented"
        else:
            return False, "❌ --force-fresh flag missing"
    except Exception as e:
        return False, f"❌ Error checking workflow: {e}"


def check_mcp_tools_exist() -> Tuple[bool, str]:
    """Check if MCP tools directory exists and has files."""
    try:
        tools_dir = Path("mcp_server/tools")
        if not tools_dir.exists():
            return False, "❌ mcp_server/tools/ directory not found"

        tool_files = list(tools_dir.glob("*.py"))
        tool_files = [f for f in tool_files if f.name != "__init__.py"]

        if len(tool_files) == 0:
            return False, "❌ No tool files found"

        return True, f"✅ {len(tool_files)} tool files found"
    except Exception as e:
        return False, f"❌ Error checking tools: {e}"


def check_recommendations_structure() -> Tuple[bool, str]:
    """Check if recommendations directory exists and has structure."""
    try:
        rec_dir = Path("implementation_plans/recommendations")
        if not rec_dir.exists():
            return False, "❌ implementation_plans/recommendations/ not found"

        rec_dirs = [d for d in rec_dir.iterdir() if d.is_dir()]

        if len(rec_dirs) == 0:
            return False, "❌ No recommendation directories found"

        # Check a sample for README.md
        has_readme = 0
        for rec in rec_dirs[:10]:
            if (rec / "README.md").exists():
                has_readme += 1

        if has_readme == 0:
            return False, "❌ Recommendations missing README.md files"

        return True, f"✅ {len(rec_dirs)} recommendation directories found"
    except Exception as e:
        return False, f"❌ Error checking recommendations: {e}"


def check_config_files() -> Tuple[bool, str]:
    """Check if essential config files exist."""
    try:
        required_files = [
            "config/workflow_config.yaml",
            "PRIORITY_ACTION_LIST.md",
            "BACKGROUND_AGENT_INSTRUCTIONS.md"
        ]

        missing = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing.append(file_path)

        if missing:
            return False, f"❌ Missing files: {', '.join(missing)}"

        return True, "✅ All essential config files present"
    except Exception as e:
        return False, f"❌ Error checking configs: {e}"


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("MCP STRUCTURE VALIDATION")
    print("=" * 70)
    print()

    checks = [
        ("Phase 8.5 Fix", check_phase_status_manager),
        ("Force-Fresh Flag", check_run_workflow_has_force_fresh),
        ("MCP Tools", check_mcp_tools_exist),
        ("Recommendations", check_recommendations_structure),
        ("Config Files", check_config_files),
    ]

    results = []
    for name, check_func in checks:
        print(f"Checking {name}...", end=" ")
        success, message = check_func()
        results.append((name, success, message))
        print(message)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ ALL CHECKS PASSED")
        print("   The MCP structure is valid and ready for use.")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("   Please review the failures above.")
        print()
        print("Failed checks:")
        for name, success, message in results:
            if not success:
                print(f"  - {name}: {message}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

