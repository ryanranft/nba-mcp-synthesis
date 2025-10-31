"""
Validate all Option 2 Jupyter notebooks.

This script executes all 5 Option 2 notebooks and validates their outputs,
generating a comprehensive quality report.

Usage:
    python scripts/validate_notebooks.py [--save-executed] [--quick]
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.validation.notebook_validator import (
    NotebookValidator,
    ValidationConfig,
)


# Option 2 notebooks (in order)
OPTION2_NOTEBOOKS = [
    "examples/notebooks/01_player_performance_trend_analysis.ipynb",
    "examples/notebooks/02_career_longevity_modeling.ipynb",
    "examples/notebooks/03_coaching_change_causal_impact.ipynb",
    "examples/notebooks/04_injury_recovery_tracking.ipynb",
    "examples/notebooks/05_team_chemistry_factor_analysis.ipynb",
]


def main():
    """Run notebook validation."""
    parser = argparse.ArgumentParser(description="Validate Option 2 notebooks")
    parser.add_argument(
        "--save-executed",
        action="store_true",
        help="Save executed notebooks to disk",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode: reduced timeout, first notebook only",
    )
    parser.add_argument(
        "--notebook",
        type=int,
        help="Validate only notebook N (1-5)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("OPTION 2 NOTEBOOK VALIDATION")
    print("=" * 70)
    print("\nValidating 5 econometric analysis notebooks...")
    print(f"Configuration: timeout={600 if not args.quick else 60}s")
    print()

    # Configure validator
    config = ValidationConfig(
        timeout=60 if args.quick else 600,  # 1 min or 10 min per cell
        kernel_name="python3",
        allow_errors=True,  # Continue on errors to collect all issues
        store_outputs=True,
    )

    validator = NotebookValidator(config=config)

    # Select notebooks to validate
    if args.quick:
        notebooks = [OPTION2_NOTEBOOKS[0]]
        print("⚡ QUICK MODE: Validating first notebook only\n")
    elif args.notebook:
        idx = args.notebook - 1
        if idx < 0 or idx >= len(OPTION2_NOTEBOOKS):
            print(f"❌ Error: Notebook index must be 1-5, got {args.notebook}")
            return 1
        notebooks = [OPTION2_NOTEBOOKS[idx]]
        print(f"📓 Validating notebook {args.notebook} only\n")
    else:
        notebooks = OPTION2_NOTEBOOKS

    # Validate notebooks
    results = validator.validate_multiple(
        notebooks, save_executed=args.save_executed
    )

    # Print summary
    validator.print_summary()

    # Save results
    filename = "notebook_validation_quick.json" if args.quick else "notebook_validation_full.json"
    filepath = validator.save_results(
        output_dir="validation_results", filename=filename
    )
    print(f"\n✅ Validation results saved to: {filepath}")

    # Exit with appropriate code
    summary = validator.generate_summary()
    if summary["failed"] > 0:
        print(f"\n❌ {summary['failed']} notebook(s) failed validation")
        return 1
    else:
        print(f"\n✅ All {summary['successful']} notebook(s) passed validation")
        return 0


if __name__ == "__main__":
    sys.exit(main())
