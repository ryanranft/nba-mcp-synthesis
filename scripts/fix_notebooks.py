"""
Fix tutorial notebooks to use correct EconometricSuite API.

Changes:
- outcome_var -> target
- treatment_var -> (removed, not needed for basic regression)
- control_vars -> predictors
- ols_analysis() -> regression()
"""

import nbformat
import re
from pathlib import Path


def fix_notebook(notebook_path):
    """Fix a single notebook."""
    print(f"\nFixing: {notebook_path}")

    # Load notebook
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)

    fixed_count = 0
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            original = cell.source

            # Fix 1: Replace EconometricSuite initialization with outcome_var
            # Pattern 1: Simple case with outcome_var, treatment_var, control_vars=[]
            pattern1 = r'EconometricSuite\s*\(\s*data\s*=\s*(\w+)\s*,\s*outcome_var\s*=\s*[\'"](\w+)[\'"]\s*,\s*treatment_var\s*=\s*[\'"](\w+)[\'"]\s*,\s*control_vars\s*=\s*\[\s*\]\s*\)'
            replacement1 = r'EconometricSuite(data=\1, target="\2")'
            cell.source = re.sub(pattern1, replacement1, cell.source)

            # Pattern 2: With non-empty control_vars
            pattern2 = r'EconometricSuite\s*\(\s*data\s*=\s*(\w+)\s*,\s*outcome_var\s*=\s*[\'"](\w+)[\'"]\s*,\s*treatment_var\s*=\s*[\'"](\w+)[\'"]\s*,\s*control_vars\s*=\s*\[([^\]]+)\]\s*\)'
            replacement2 = r'EconometricSuite(data=\1, target="\2")'
            cell.source = re.sub(pattern2, replacement2, cell.source)

            # Pattern 3: outcome_var with time_var (for time series)
            pattern3 = r'outcome_var\s*=\s*[\'"](\w+)[\'"]'
            replacement3 = r'target="\1"'
            cell.source = re.sub(pattern3, replacement3, cell.source)

            # Pattern 4: time_var -> time_col
            pattern4 = r'time_var\s*=\s*[\'"](\w+)[\'"]'
            replacement4 = r'time_col="\1"'
            cell.source = re.sub(pattern4, replacement4, cell.source)

            # Fix 2: Replace ols_analysis() with regression()
            # Need to extract what the original treatment_var was to use as predictor
            treatment_var_match = re.search(
                r'treatment_var\s*=\s*[\'"](\w+)[\'"]', original
            )
            if treatment_var_match and ".ols_analysis()" in cell.source:
                treatment_var = treatment_var_match.group(1)
                # Check if there were control vars
                control_vars_match = re.search(
                    r"control_vars\s*=\s*\[([^\]]*)\]", original
                )
                if control_vars_match:
                    control_vars_str = control_vars_match.group(1).strip()
                    if control_vars_str:  # Non-empty control vars
                        # Parse control vars
                        control_vars = [
                            v.strip().strip("'\"")
                            for v in control_vars_str.split(",")
                            if v.strip()
                        ]
                        predictors = [treatment_var] + control_vars
                    else:  # Empty control vars
                        predictors = [treatment_var]
                else:
                    predictors = [treatment_var]

                predictors_str = ", ".join([f"'{p}'" for p in predictors])
                pattern3 = r"\.ols_analysis\s*\(\s*\)"
                replacement3 = f".regression(predictors=[{predictors_str}])"
                cell.source = re.sub(pattern3, replacement3, cell.source)
            else:
                # No treatment_var found, just do basic replacement
                pattern3 = r"\.ols_analysis\s*\(\s*\)"
                replacement3 = ".regression()"
                cell.source = re.sub(pattern3, replacement3, cell.source)

            # Fix 3: Replace result_multi = suite_multi.ols_analysis() patterns
            # This handles the case where predictors should be specified
            if "suite_multi" in cell.source and "control_vars" in original:
                # Extract control_vars list from original
                import ast

                match = re.search(r"control_vars\s*=\s*\[([^\]]+)\]", original)
                if match:
                    control_vars_str = match.group(1)
                    # Parse the list
                    control_vars = [
                        v.strip().strip("'\"") for v in control_vars_str.split(",")
                    ]
                    # Add treatment var to predictors
                    treatment_match = re.search(
                        r'treatment_var\s*=\s*[\'"](\w+)[\'"]', original
                    )
                    if treatment_match:
                        treatment_var = treatment_match.group(1)
                        predictors = [treatment_var] + control_vars
                        predictors_str = ", ".join([f"'{p}'" for p in predictors])

                        # Replace with regression call that includes predictors
                        cell.source = re.sub(
                            r"suite_multi\.regression\(\)",
                            f"suite_multi.regression(predictors=[{predictors_str}])",
                            cell.source,
                        )

            if cell.source != original:
                fixed_count += 1
                print(f"  Fixed cell {i+1}")

    # Save
    with open(notebook_path, "w") as f:
        nbformat.write(nb, f)

    print(f"  ✓ {fixed_count} cells updated")
    return fixed_count


def main():
    """Fix all tutorial notebooks."""
    notebooks_dir = Path("examples")
    notebooks = [
        notebooks_dir / "01_nba_101_getting_started.ipynb",
        notebooks_dir / "02_player_valuation_performance.ipynb",
        notebooks_dir / "03_team_strategy_game_outcomes.ipynb",
        notebooks_dir / "04_contract_analytics_salary_cap.ipynb",
        notebooks_dir / "05_live_game_analytics_dashboard.ipynb",
    ]

    total_fixed = 0
    for nb_path in notebooks:
        if nb_path.exists():
            total_fixed += fix_notebook(nb_path)
        else:
            print(f"  ⚠ Not found: {nb_path}")

    print(f"\n{'='*60}")
    print(f"Total cells fixed across all notebooks: {total_fixed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
