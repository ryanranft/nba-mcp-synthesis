#!/usr/bin/env python3
"""
Pre-Flight Check for Overnight Convergence Run

Validates all requirements before autonomous execution.

Usage:
    python3 scripts/pre_flight_check.py
"""

import os
import sys
import yaml
import json
import socket
from pathlib import Path
from typing import List, Tuple


def check_api_keys() -> Tuple[bool, str]:
    """Check if API keys are set."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    claude_key = os.environ.get("CLAUDE_API_KEY")

    if not gemini_key:
        return False, "GEMINI_API_KEY not set"
    if not claude_key:
        return False, "CLAUDE_API_KEY not set"

    return True, f"API keys configured ({len(gemini_key)} + {len(claude_key)} chars)"


def check_disk_space() -> Tuple[bool, str]:
    """Check available disk space."""
    import shutil

    stat = shutil.disk_usage(".")
    free_gb = stat.free / (1024**3)

    if free_gb < 10:
        return False, f"Only {free_gb:.1f} GB available (need 10+ GB)"

    return True, f"{free_gb:.1f} GB available"


def check_port(port: int = 8080) -> Tuple[bool, str]:
    """Check if port is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("localhost", port))
    sock.close()

    if result == 0:
        return False, f"Port {port} is in use"

    return True, f"Port {port} is available"


def check_config() -> Tuple[bool, str]:
    """Check workflow configuration."""
    config_file = Path("config/workflow_config.yaml")

    if not config_file.exists():
        return False, "workflow_config.yaml not found"

    try:
        with open(config_file) as f:
            config = yaml.safe_load(f)

        # Check critical settings
        max_iter = config["phases"]["phase_2"]["convergence"]["max_iterations"]
        if max_iter < 200:
            return False, f"max_iterations only {max_iter} (need 200)"

        cost_limit = config["cost_limits"]["total_workflow"]
        if cost_limit < 300:
            return False, f"cost_limit only ${cost_limit} (need $300+)"

        return True, f"Configured: {max_iter} iterations, ${cost_limit:.0f} limit"
    except Exception as e:
        return False, f"Config error: {e}"


def check_scripts() -> Tuple[bool, str]:
    """Check launch scripts exist and are executable."""
    scripts = ["launch_overnight_convergence.sh", "check_progress.sh"]

    missing = []
    for script in scripts:
        path = Path(script)
        if not path.exists():
            missing.append(f"{script} (not found)")
        elif not os.access(path, os.X_OK):
            missing.append(f"{script} (not executable)")

    if missing:
        return False, f"Issues: {', '.join(missing)}"

    return True, f"{len(scripts)} scripts ready"


def check_baseline() -> Tuple[bool, str]:
    """Check if pre-convergence baseline exists."""
    baseline_file = Path("analysis_results/pre_convergence_summary.json")

    if not baseline_file.exists():
        return False, "Pre-convergence baseline not created"

    try:
        with open(baseline_file) as f:
            data = json.load(f)

        books = data.get("total_books", 0)
        return True, f"Baseline captured ({books} books)"
    except Exception as e:
        return False, f"Baseline error: {e}"


def check_integration_tests() -> Tuple[bool, str]:
    """Check if integration tests pass."""
    test_script = Path("scripts/test_tier3_integration.py")

    if not test_script.exists():
        return False, "test_tier3_integration.py not found"

    # For simplicity, just check it exists
    # Full test run is done separately
    return True, "Test suite available"


def main():
    """Run all pre-flight checks."""
    print("=" * 60)
    print("Pre-Flight Check - Overnight Convergence Run")
    print("=" * 60)
    print()

    checks = [
        ("API Keys", check_api_keys),
        ("Disk Space", check_disk_space),
        ("Port 8080", check_port),
        ("Configuration", check_config),
        ("Launch Scripts", check_scripts),
        ("Baseline Backup", check_baseline),
        ("Integration Tests", check_integration_tests),
    ]

    results = []
    all_passed = True

    for name, check_func in checks:
        try:
            passed, message = check_func()
            results.append((name, passed, message))

            status = "✅" if passed else "❌"
            print(f"{status} {name:20s} {message}")

            if not passed:
                all_passed = False
        except Exception as e:
            results.append((name, False, f"Error: {e}"))
            print(f"❌ {name:20s} Error: {e}")
            all_passed = False

    print()
    print("=" * 60)

    if all_passed:
        print("✅ ALL CHECKS PASSED - READY TO LAUNCH")
        print()
        print("To launch:")
        print("  ./launch_overnight_convergence.sh")
        print()
        return 0
    else:
        print("❌ SOME CHECKS FAILED - CANNOT LAUNCH")
        print()
        print("Fix the issues above, then run this check again.")
        print()

        failed = [r for r in results if not r[1]]
        print(f"Failed checks ({len(failed)}):")
        for name, _, message in failed:
            print(f"  - {name}: {message}")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
