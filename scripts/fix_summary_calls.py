"""
Fix .summary attribute references to .summary() method calls in notebooks.
"""

import nbformat
import re
from pathlib import Path

notebooks = [
    "examples/02_player_valuation_performance.ipynb",
    "examples/03_team_strategy_game_outcomes.ipynb",
    "examples/04_contract_analytics_salary_cap.ipynb",
    "examples/05_live_game_analytics_dashboard.ipynb",
]

total_fixed = 0
for nb_path in notebooks:
    print(f"\nFixing: {nb_path}")
    with open(nb_path) as f:
        nb = nbformat.read(f, as_version=4)

    fixed_count = 0
    for cell in nb.cells:
        if cell.cell_type == "code":
            original = cell.source

            # Fix all result.summary references (attribute -> method call)
            # Replace .summary (not followed by parentheses) with .summary()
            cell.source = re.sub(r"\.summary(?!\()", ".summary()", cell.source)

            if cell.source != original:
                fixed_count += 1
                print(f"  Fixed cell: .summary -> .summary()")

    # Save
    with open(nb_path, "w") as f:
        nbformat.write(nb, f)

    print(f"  ✓ {fixed_count} cells fixed")
    total_fixed += fixed_count

print("\n" + "=" * 60)
print(f"Total cells fixed: {total_fixed}")
print("=" * 60)
