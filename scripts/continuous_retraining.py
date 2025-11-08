#!/usr/bin/env python3
"""
Continuous Retraining Pipeline for NBA Betting Models

Orchestrates the complete model retraining workflow:
1. Feature extraction
2. Ensemble model training
3. Backtest calibration data generation
4. Kelly calibrator training
5. Model comparison and deployment

Features:
- Automatic model versioning with timestamps
- Performance comparison (new vs current model)
- Automated deployment if new model improves Brier score
- Notification support (SMS/email)
- Model archive (keeps last N models)

Usage:
    # Manual trigger
    python scripts/continuous_retraining.py

    # With custom settings
    python scripts/continuous_retraining.py --notify sms --min-improvement 0.02

    # Dry run (no deployment)
    python scripts/continuous_retraining.py --dry-run
"""

import argparse
import sys
import os
import json
import shutil
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
import warnings

import pandas as pd

warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.unified_secrets_manager import load_secrets_hierarchical


class ContinuousRetrainingPipeline:
    """
    Orchestrates the complete model retraining and deployment workflow
    """

    def __init__(
        self,
        data_dir: str = "data",
        models_dir: str = "models",
        archive_dir: str = "models/archive",
        plots_dir: str = "plots",
        reports_dir: str = "reports",
        keep_last_n_models: int = 5,
        min_improvement: float = 0.01,  # 1% Brier score improvement
        notify: Optional[str] = None
    ):
        """
        Initialize retraining pipeline

        Args:
            data_dir: Directory for data files
            models_dir: Directory for model files
            archive_dir: Directory for archived models
            plots_dir: Directory for plots
            reports_dir: Directory for reports
            keep_last_n_models: Number of previous models to retain
            min_improvement: Minimum Brier score improvement for deployment (default 1%)
            notify: Notification method ('sms', 'email', or None)
        """
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        self.archive_dir = Path(archive_dir)
        self.plots_dir = Path(plots_dir)
        self.reports_dir = Path(reports_dir)
        self.keep_last_n_models = keep_last_n_models
        self.min_improvement = min_improvement
        self.notify = notify

        # Create directories
        for directory in [self.data_dir, self.models_dir, self.archive_dir, self.plots_dir, self.reports_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Generate timestamp for this run
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # File paths
        self.features_file = self.data_dir / "game_features.csv"
        self.calibration_file = self.data_dir / "calibration_training_data.csv"

        # Current model paths
        self.current_ensemble_model = self.models_dir / "ensemble_game_outcome_model.pkl"
        self.current_calibrator = self.models_dir / "calibrated_kelly_engine.pkl"

        # New model paths (versioned)
        self.new_ensemble_model = self.models_dir / f"ensemble_{self.timestamp}.pkl"
        self.new_calibrator = self.models_dir / f"calibrator_{self.timestamp}.pkl"

        # Metadata
        self.metadata_file = self.models_dir / f"metadata_{self.timestamp}.json"

        # Results
        self.results = {
            "timestamp": self.timestamp,
            "steps_completed": [],
            "steps_failed": [],
            "metrics": {},
            "deployed": False
        }

    def run_feature_extraction(self) -> bool:
        """Step 1: Extract game features"""
        print("=" * 80)
        print("STEP 1: Feature Extraction")
        print("=" * 80)

        try:
            from subprocess import run, PIPE

            cmd = [
                "python", "scripts/prepare_game_features_complete.py",
                "--output", str(self.features_file)
            ]

            result = run(cmd, stdout=PIPE, stderr=PIPE, text=True)

            if result.returncode != 0:
                print(f"❌ Feature extraction failed:")
                print(result.stderr)
                self.results["steps_failed"].append("feature_extraction")
                return False

            # Verify file was created
            if not self.features_file.exists():
                print(f"❌ Features file not created: {self.features_file}")
                self.results["steps_failed"].append("feature_extraction")
                return False

            # Load and check data
            df = pd.read_csv(self.features_file)
            print(f"✓ Extracted features for {len(df)} games")
            print(f"✓ Features: {len(df.columns)} columns")

            self.results["metrics"]["games_count"] = len(df)
            self.results["metrics"]["features_count"] = len(df.columns)
            self.results["steps_completed"].append("feature_extraction")
            print()
            return True

        except Exception as e:
            print(f"❌ Error during feature extraction: {e}")
            self.results["steps_failed"].append("feature_extraction")
            return False

    def run_ensemble_training(self) -> bool:
        """Step 2: Train ensemble model"""
        print("=" * 80)
        print("STEP 2: Ensemble Model Training")
        print("=" * 80)

        try:
            from subprocess import run, PIPE

            # Train to temporary location
            temp_output = self.models_dir / "temp"
            temp_output.mkdir(exist_ok=True)

            cmd = [
                "python", "scripts/train_game_outcome_model.py",
                "--features", str(self.features_file),
                "--output", str(temp_output) + "/"
            ]

            result = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
            print(result.stdout)  # Show training progress

            if result.returncode != 0:
                print(f"❌ Ensemble training failed:")
                print(result.stderr)
                self.results["steps_failed"].append("ensemble_training")
                return False

            # Move trained model to versioned location
            temp_model = temp_output / "ensemble_game_outcome_model.pkl"
            if temp_model.exists():
                shutil.move(str(temp_model), str(self.new_ensemble_model))
                print(f"✓ Saved ensemble model: {self.new_ensemble_model}")
            else:
                print(f"❌ Ensemble model not created")
                self.results["steps_failed"].append("ensemble_training")
                return False

            # Load metadata
            metadata_path = temp_output / "model_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.results["metrics"].update(metadata)

            # Cleanup temp directory
            shutil.rmtree(temp_output)

            self.results["steps_completed"].append("ensemble_training")
            print()
            return True

        except Exception as e:
            print(f"❌ Error during ensemble training: {e}")
            self.results["steps_failed"].append("ensemble_training")
            return False

    def run_backtest(self) -> bool:
        """Step 3: Generate calibration data via backtest"""
        print("=" * 80)
        print("STEP 3: Backtest Calibration Data Generation")
        print("=" * 80)

        try:
            from subprocess import run, PIPE

            cmd = [
                "python", "scripts/backtest_historical_games.py",
                "--features", str(self.features_file),
                "--model", str(self.new_ensemble_model),
                "--output", str(self.calibration_file)
            ]

            result = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
            print(result.stdout)  # Show backtest progress

            if result.returncode != 0:
                print(f"❌ Backtest failed:")
                print(result.stderr)
                self.results["steps_failed"].append("backtest")
                return False

            # Verify calibration data created
            if not self.calibration_file.exists():
                print(f"❌ Calibration data not created: {self.calibration_file}")
                self.results["steps_failed"].append("backtest")
                return False

            df = pd.read_csv(self.calibration_file)
            print(f"✓ Generated {len(df)} calibration predictions")

            self.results["metrics"]["calibration_samples"] = len(df)
            self.results["steps_completed"].append("backtest")
            print()
            return True

        except Exception as e:
            print(f"❌ Error during backtest: {e}")
            self.results["steps_failed"].append("backtest")
            return False

    def run_calibrator_training(self) -> bool:
        """Step 4: Train Kelly calibrator"""
        print("=" * 80)
        print("STEP 4: Kelly Calibrator Training")
        print("=" * 80)

        try:
            from subprocess import run, PIPE

            # Train to temporary location
            temp_output = self.models_dir / "temp"
            temp_output.mkdir(exist_ok=True)

            cmd = [
                "python", "scripts/train_kelly_calibrator.py",
                "--data", str(self.calibration_file),
                "--output", str(temp_output) + "/"
            ]

            result = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
            print(result.stdout)  # Show calibrator training progress

            if result.returncode != 0:
                print(f"❌ Calibrator training failed:")
                print(result.stderr)
                self.results["steps_failed"].append("calibrator_training")
                return False

            # Move trained calibrator to versioned location
            temp_calibrator = temp_output / "calibrated_kelly_engine.pkl"
            if temp_calibrator.exists():
                shutil.move(str(temp_calibrator), str(self.new_calibrator))
                print(f"✓ Saved calibrator: {self.new_calibrator}")
            else:
                print(f"❌ Calibrator not created")
                self.results["steps_failed"].append("calibrator_training")
                return False

            # Load calibrator metadata
            cal_metadata_path = temp_output / "calibrator_metadata.json"
            if cal_metadata_path.exists():
                with open(cal_metadata_path, 'r') as f:
                    cal_metadata = json.load(f)
                    self.results["metrics"]["calibrator"] = cal_metadata

            # Cleanup temp directory
            shutil.rmtree(temp_output, ignore_errors=True)

            self.results["steps_completed"].append("calibrator_training")
            print()
            return True

        except Exception as e:
            print(f"❌ Error during calibrator training: {e}")
            self.results["steps_failed"].append("calibrator_training")
            return False

    def compare_models(self) -> Tuple[bool, str]:
        """
        Compare new model with current model

        Returns:
            (should_deploy, reason)
        """
        print("=" * 80)
        print("STEP 5: Model Comparison")
        print("=" * 80)

        # Check if current model exists
        if not self.current_ensemble_model.exists():
            print("✓ No existing model - deploying new model")
            return (True, "no_existing_model")

        try:
            # Load current model metadata
            current_metadata_path = self.models_dir / "model_metadata.json"
            if not current_metadata_path.exists():
                print("⚠ Current model metadata not found - deploying new model")
                return (True, "missing_metadata")

            with open(current_metadata_path, 'r') as f:
                current_metadata = json.load(f)

            # Compare Brier scores
            current_brier = current_metadata.get("test_brier_score")
            new_brier = self.results["metrics"].get("test_brier_score")

            if current_brier is None or new_brier is None:
                print("⚠ Cannot compare Brier scores - deploying new model")
                return (True, "missing_brier_scores")

            print(f"Current model Brier score: {current_brier:.4f}")
            print(f"New model Brier score:     {new_brier:.4f}")

            improvement = current_brier - new_brier
            improvement_pct = (improvement / current_brier) * 100

            print(f"Improvement: {improvement:.4f} ({improvement_pct:.1f}%)")
            print(f"Minimum required: {self.min_improvement:.4f} ({self.min_improvement * 100:.1f}%)")

            self.results["metrics"]["brier_improvement"] = improvement
            self.results["metrics"]["brier_improvement_pct"] = improvement_pct

            if improvement >= self.min_improvement:
                print(f"✓ New model improves Brier score by {improvement_pct:.1f}% - DEPLOYING")
                return (True, "performance_improved")
            else:
                print(f"❌ New model improvement ({improvement_pct:.1f}%) below threshold - KEEPING CURRENT")
                return (False, "insufficient_improvement")

        except Exception as e:
            print(f"⚠ Error comparing models: {e} - deploying new model")
            return (True, "comparison_error")

    def deploy_models(self, dry_run: bool = False) -> bool:
        """
        Deploy new models (replace current models)

        Args:
            dry_run: If True, don't actually deploy

        Returns:
            True if successful
        """
        print()
        print("=" * 80)
        print("STEP 6: Model Deployment")
        print("=" * 80)

        if dry_run:
            print("🔸 DRY RUN MODE - Not deploying models")
            return True

        try:
            # Archive current models if they exist
            if self.current_ensemble_model.exists():
                archive_name = f"ensemble_{datetime.now().strftime('%Y%m%d_%H%M%S')}_archived.pkl"
                archive_path = self.archive_dir / archive_name
                shutil.copy(str(self.current_ensemble_model), str(archive_path))
                print(f"✓ Archived current ensemble: {archive_path}")

            if self.current_calibrator.exists():
                archive_name = f"calibrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}_archived.pkl"
                archive_path = self.archive_dir / archive_name
                shutil.copy(str(self.current_calibrator), str(archive_path))
                print(f"✓ Archived current calibrator: {archive_path}")

            # Deploy new models
            shutil.copy(str(self.new_ensemble_model), str(self.current_ensemble_model))
            print(f"✓ Deployed new ensemble: {self.current_ensemble_model}")

            shutil.copy(str(self.new_calibrator), str(self.current_calibrator))
            print(f"✓ Deployed new calibrator: {self.current_calibrator}")

            # Update metadata
            metadata_path = self.models_dir / "model_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(self.results["metrics"], f, indent=2)
            print(f"✓ Updated metadata: {metadata_path}")

            # Cleanup old archives
            self._cleanup_old_models()

            self.results["deployed"] = True
            self.results["steps_completed"].append("deployment")
            print()
            return True

        except Exception as e:
            print(f"❌ Error during deployment: {e}")
            self.results["steps_failed"].append("deployment")
            return False

    def _cleanup_old_models(self):
        """Remove old archived models, keeping last N"""
        try:
            # Get all archived models
            archives = sorted(self.archive_dir.glob("*.pkl"), key=lambda p: p.stat().st_mtime, reverse=True)

            # Keep last N models
            if len(archives) > self.keep_last_n_models:
                for old_model in archives[self.keep_last_n_models:]:
                    old_model.unlink()
                    print(f"✓ Removed old archive: {old_model}")

        except Exception as e:
            print(f"⚠ Error cleaning up archives: {e}")

    def send_notification(self, message: str):
        """Send notification via configured channel"""
        if not self.notify:
            return

        try:
            if self.notify == 'sms':
                from mcp_server.betting.notifications import NotificationManager
                notifier = NotificationManager(config={'sms': {'enabled': True}})
                notifier.send_message(
                    subject="NBA Model Retraining Complete",
                    message=message,
                    channels=['sms']
                )
                print("✓ SMS notification sent")

            elif self.notify == 'email':
                # Email notification (not implemented yet)
                print("⚠ Email notifications not implemented yet")

        except Exception as e:
            print(f"⚠ Failed to send notification: {e}")

    def save_report(self):
        """Save retraining report"""
        report_path = self.reports_dir / f"retraining_report_{self.timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"✓ Saved retraining report: {report_path}")

    def run(self, dry_run: bool = False) -> bool:
        """
        Execute complete retraining pipeline

        Args:
            dry_run: If True, run training but don't deploy

        Returns:
            True if successful
        """
        print("=" * 80)
        print("NBA CONTINUOUS RETRAINING PIPELINE")
        print("=" * 80)
        print(f"Timestamp: {self.timestamp}")
        print(f"Dry Run: {dry_run}")
        print(f"Notify: {self.notify or 'None'}")
        print()

        # Step 1: Feature Extraction
        if not self.run_feature_extraction():
            print("\n❌ Pipeline failed at feature extraction")
            self.save_report()
            return False

        # Step 2: Ensemble Training
        if not self.run_ensemble_training():
            print("\n❌ Pipeline failed at ensemble training")
            self.save_report()
            return False

        # Step 3: Backtest
        if not self.run_backtest():
            print("\n❌ Pipeline failed at backtest")
            self.save_report()
            return False

        # Step 4: Calibrator Training
        if not self.run_calibrator_training():
            print("\n❌ Pipeline failed at calibrator training")
            self.save_report()
            return False

        # Step 5: Model Comparison
        should_deploy, reason = self.compare_models()
        self.results["deployment_decision"] = {
            "should_deploy": should_deploy,
            "reason": reason
        }

        # Step 6: Deployment
        if should_deploy:
            if not self.deploy_models(dry_run=dry_run):
                print("\n❌ Pipeline failed at deployment")
                self.save_report()
                return False
        else:
            print("\n⚠ New model not deployed (insufficient improvement)")
            self.results["deployed"] = False

        # Save report
        self.save_report()

        # Send notification
        if self.results["deployed"]:
            message = f"✅ NBA model retrained and deployed!\n\nBrier improvement: {self.results['metrics'].get('brier_improvement_pct', 0):.1f}%"
        else:
            message = f"⚠ NBA model retrained but not deployed (reason: {reason})"

        self.send_notification(message)

        # Summary
        print()
        print("=" * 80)
        print("RETRAINING PIPELINE COMPLETE")
        print("=" * 80)
        print(f"Steps completed: {len(self.results['steps_completed'])}")
        print(f"Steps failed: {len(self.results['steps_failed'])}")
        print(f"Deployed: {'✓ YES' if self.results['deployed'] else '✗ NO'}")
        print()

        return len(self.results['steps_failed']) == 0


def main():
    parser = argparse.ArgumentParser(
        description="NBA Continuous Retraining Pipeline"
    )
    parser.add_argument(
        '--min-improvement',
        type=float,
        default=0.01,
        help='Minimum Brier score improvement for deployment (default: 0.01 = 1%%)'
    )
    parser.add_argument(
        '--keep-models',
        type=int,
        default=5,
        help='Number of archived models to keep (default: 5)'
    )
    parser.add_argument(
        '--notify',
        choices=['sms', 'email'],
        help='Send notification via SMS or email'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run training but do not deploy models'
    )

    args = parser.parse_args()

    # Load secrets
    load_secrets_hierarchical("nba-mcp-synthesis", "NBA", "production")

    # Initialize and run pipeline
    pipeline = ContinuousRetrainingPipeline(
        min_improvement=args.min_improvement,
        keep_last_n_models=args.keep_models,
        notify=args.notify
    )

    success = pipeline.run(dry_run=args.dry_run)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
