"""
Experiment Tracking Module
Track and compare ML experiments with parameters, metrics, and artifacts.
"""

import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, field
import json
from pathlib import Path
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Experiment:
    """ML experiment"""
    experiment_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    tags: Dict[str, str] = field(default_factory=dict)
    runs: List[str] = field(default_factory=list)


@dataclass
class ExperimentRun:
    """Single experiment run"""
    run_id: str
    experiment_id: str
    params: Dict[str, Any]
    metrics: Dict[str, float]
    artifacts: Dict[str, str] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = "running"
    notes: Optional[str] = None


class ExperimentTracker:
    """Track ML experiments"""

    def __init__(self, tracking_dir: str = "./experiments"):
        """
        Initialize experiment tracker.

        Args:
            tracking_dir: Directory for tracking data
        """
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

        self.experiments: Dict[str, Experiment] = {}
        self.runs: Dict[str, ExperimentRun] = {}

        self._load_experiments()

    def _load_experiments(self):
        """Load experiments from disk"""
        exp_file = self.tracking_dir / "experiments.json"
        if exp_file.exists():
            with open(exp_file, 'r') as f:
                data = json.load(f)
                for exp_id, exp_data in data["experiments"].items():
                    self.experiments[exp_id] = Experiment(
                        experiment_id=exp_data["experiment_id"],
                        name=exp_data["name"],
                        description=exp_data.get("description"),
                        created_at=datetime.fromisoformat(exp_data["created_at"]),
                        created_by=exp_data["created_by"],
                        tags=exp_data.get("tags", {}),
                        runs=exp_data.get("runs", [])
                    )

                for run_id, run_data in data["runs"].items():
                    self.runs[run_id] = ExperimentRun(
                        run_id=run_data["run_id"],
                        experiment_id=run_data["experiment_id"],
                        params=run_data["params"],
                        metrics=run_data["metrics"],
                        artifacts=run_data.get("artifacts", {}),
                        start_time=datetime.fromisoformat(run_data["start_time"]),
                        end_time=datetime.fromisoformat(run_data["end_time"]) if run_data.get("end_time") else None,
                        status=run_data["status"],
                        notes=run_data.get("notes")
                    )

            logger.info(f"Loaded {len(self.experiments)} experiments, {len(self.runs)} runs")

    def _save_experiments(self):
        """Save experiments to disk"""
        exp_file = self.tracking_dir / "experiments.json"
        data = {
            "experiments": {},
            "runs": {}
        }

        for exp_id, exp in self.experiments.items():
            data["experiments"][exp_id] = {
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "description": exp.description,
                "created_at": exp.created_at.isoformat(),
                "created_by": exp.created_by,
                "tags": exp.tags,
                "runs": exp.runs
            }

        for run_id, run in self.runs.items():
            data["runs"][run_id] = {
                "run_id": run.run_id,
                "experiment_id": run.experiment_id,
                "params": run.params,
                "metrics": run.metrics,
                "artifacts": run.artifacts,
                "start_time": run.start_time.isoformat(),
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "status": run.status,
                "notes": run.notes
            }

        with open(exp_file, 'w') as f:
            json.dump(data, f, indent=2)

    def create_experiment(
        self,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Experiment:
        """Create new experiment"""
        exp_id = hashlib.md5(f"{name}{datetime.utcnow()}".encode()).hexdigest()[:12]

        experiment = Experiment(
            experiment_id=exp_id,
            name=name,
            description=description,
            tags=tags or {}
        )

        self.experiments[exp_id] = experiment
        self._save_experiments()

        logger.info(f"Created experiment: {name} ({exp_id})")

        return experiment

    def start_run(
        self,
        experiment_id: str,
        params: Dict[str, Any],
        notes: Optional[str] = None
    ) -> ExperimentRun:
        """Start new experiment run"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        run_id = hashlib.md5(f"{experiment_id}{datetime.utcnow()}".encode()).hexdigest()[:12]

        run = ExperimentRun(
            run_id=run_id,
            experiment_id=experiment_id,
            params=params.copy(),
            metrics={},
            status="running",
            notes=notes
        )

        self.runs[run_id] = run
        self.experiments[experiment_id].runs.append(run_id)
        self._save_experiments()

        logger.info(f"Started run: {run_id} for experiment {experiment_id}")

        return run

    def log_metrics(
        self,
        run_id: str,
        metrics: Dict[str, float]
    ):
        """Log metrics for a run"""
        if run_id not in self.runs:
            raise ValueError(f"Run {run_id} not found")

        self.runs[run_id].metrics.update(metrics)
        self._save_experiments()

        logger.debug(f"Logged {len(metrics)} metrics for run {run_id}")

    def end_run(
        self,
        run_id: str,
        status: str = "completed"
    ):
        """End an experiment run"""
        if run_id not in self.runs:
            raise ValueError(f"Run {run_id} not found")

        self.runs[run_id].end_time = datetime.utcnow()
        self.runs[run_id].status = status
        self._save_experiments()

        logger.info(f"Ended run: {run_id} with status {status}")

    def compare_runs(
        self,
        run_ids: List[str]
    ) -> Dict[str, Any]:
        """Compare multiple runs"""
        if not all(rid in self.runs for rid in run_ids):
            raise ValueError("One or more runs not found")

        runs = [self.runs[rid] for rid in run_ids]

        # Get all metric names
        all_metrics = set()
        for run in runs:
            all_metrics.update(run.metrics.keys())

        comparison = {
            "runs": [],
            "best_by_metric": {}
        }

        for run in runs:
            comparison["runs"].append({
                "run_id": run.run_id,
                "params": run.params,
                "metrics": run.metrics,
                "status": run.status
            })

        # Find best for each metric
        for metric in all_metrics:
            values = [(run.run_id, run.metrics.get(metric)) for run in runs if metric in run.metrics]
            if values:
                best_run_id, best_value = max(values, key=lambda x: x[1] if x[1] is not None else float('-inf'))
                comparison["best_by_metric"][metric] = {
                    "run_id": best_run_id,
                    "value": best_value
                }

        return comparison

    def get_experiment_summary(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment summary"""
        if experiment_id not in self.experiments:
            return {"error": "Experiment not found"}

        experiment = self.experiments[experiment_id]
        runs = [self.runs[rid] for rid in experiment.runs if rid in self.runs]

        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "total_runs": len(runs),
            "completed_runs": len([r for r in runs if r.status == "completed"]),
            "failed_runs": len([r for r in runs if r.status == "failed"]),
            "best_run": max(runs, key=lambda r: r.metrics.get("accuracy", 0)).run_id if runs else None
        }


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("EXPERIMENT TRACKING DEMO")
    print("=" * 80)

    tracker = ExperimentTracker(tracking_dir="./demo_experiments")

    # Create experiment
    print("\n" + "=" * 80)
    print("CREATING EXPERIMENT")
    print("=" * 80)

    exp = tracker.create_experiment(
        name="NBA Win Prediction",
        description="Predict team win probability",
        tags={"sport": "basketball", "task": "classification"}
    )

    print(f"✅ Created experiment: {exp.name} ({exp.experiment_id})")

    # Run experiments
    print("\n" + "=" * 80)
    print("RUNNING EXPERIMENTS")
    print("=" * 80)

    import random

    for i in range(3):
        params = {
            "n_estimators": random.choice([50, 100, 200]),
            "max_depth": random.choice([5, 10, 15]),
            "learning_rate": random.choice([0.01, 0.1, 0.3])
        }

        run = tracker.start_run(exp.experiment_id, params, notes=f"Run {i+1}")

        # Simulate training
        metrics = {
            "accuracy": random.uniform(0.75, 0.95),
            "precision": random.uniform(0.7, 0.9),
            "recall": random.uniform(0.7, 0.9)
        }

        tracker.log_metrics(run.run_id, metrics)
        tracker.end_run(run.run_id, "completed")

        print(f"  Run {i+1}: accuracy={metrics['accuracy']:.3f}")

    print(f"\n✅ Completed 3 runs")

    # Compare runs
    print("\n" + "=" * 80)
    print("COMPARING RUNS")
    print("=" * 80)

    comparison = tracker.compare_runs(exp.runs)
    print(f"\nBest by metric:")
    for metric, best in comparison["best_by_metric"].items():
        print(f"  {metric}: {best['value']:.3f} (run: {best['run_id']})")

    # Experiment summary
    print("\n" + "=" * 80)
    print("EXPERIMENT SUMMARY")
    print("=" * 80)

    summary = tracker.get_experiment_summary(exp.experiment_id)
    print(f"\nExperiment: {summary['name']}")
    print(f"Total Runs: {summary['total_runs']}")
    print(f"Completed: {summary['completed_runs']}")
    print(f"Best Run: {summary['best_run']}")

    print("\n" + "=" * 80)
    print("Experiment Tracking Demo Complete!")
    print("=" * 80)

