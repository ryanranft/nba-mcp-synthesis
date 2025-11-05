# Launch Script Fixed

**Issue:** The initial launch failed because `run_full_workflow.py` doesn't support the arguments the launch script was passing.

**Root Cause:**
The launch script tried to pass these arguments:
- `--book "All Books"` (not needed - no --book means all books)
- `--converge-until-done` (doesn't exist)
- `--max-iterations 200` (doesn't exist - read from config)
- `--config config/workflow_config.yaml` (doesn't exist - auto-loaded)

**Fix Applied:**
Changed the command to just:
```bash
python3 scripts/run_full_workflow.py --parallel --max-workers 4
```

The convergence settings (max 200 iterations, force convergence, etc.) are already configured in `workflow_config.yaml` and will be read automatically.

Also fixed a bash syntax error on line 193.

**To Restart:**
```bash
./setup_secrets_and_launch.sh
```

Or if you already have secrets loaded:
```bash
./launch_overnight_convergence.sh
```

Type "START" when prompted.

**What Will Actually Run:**
- All 51 books (no --book argument = all books)
- Parallel execution with 4 workers
- Convergence settings from workflow_config.yaml:
  - max_iterations: 200
  - force_convergence: true
  - convergence_threshold: 3
  - min_recommendations_per_iteration: 2

The run will take 10-15 hours and extract 300-400 recommendations.
