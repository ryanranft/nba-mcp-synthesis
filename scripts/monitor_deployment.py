#!/usr/bin/env python3
"""
Multi-Pass Book Deployment Monitor

Real-time monitoring script that launches the Multi-Pass Book Deployment
and displays progress updates every 30 seconds.
"""

import os
import sys
import json
import time
import subprocess
import signal
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class DeploymentMonitor:
    def __init__(self):
        self.progress_file = "analysis_results/multi_pass_progress.json"
        self.log_file = "logs/deployment_monitor.log"
        self.deployment_process = None
        self.start_time = None
        self.last_progress_time = None
        self.running = True

        # ANSI color codes
        self.COLORS = {
            "GREEN": "\033[92m",
            "RED": "\033[91m",
            "YELLOW": "\033[93m",
            "BLUE": "\033[94m",
            "CYAN": "\033[96m",
            "WHITE": "\033[97m",
            "BOLD": "\033[1m",
            "END": "\033[0m",
        }

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals gracefully."""
        print(
            f"\n{self.COLORS['YELLOW']}Received signal {signum}, shutting down...{self.COLORS['END']}"
        )
        self.running = False
        if self.deployment_process:
            self.deployment_process.terminate()
        sys.exit(0)

    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system("clear" if os.name == "posix" else "cls")

    def _format_time(self, seconds: float) -> str:
        """Format seconds into HH:MM:SS."""
        td = timedelta(seconds=int(seconds))
        return str(td)

    def _create_progress_bar(self, current: int, total: int, width: int = 20) -> str:
        """Create a visual progress bar."""
        if total == 0:
            return "[" + " " * width + "]"

        filled = int((current / total) * width)
        bar = "=" * filled + ">" + " " * (width - filled - 1)
        return f"[{bar}]"

    def _get_file_counts(self) -> Dict[str, int]:
        """Count generated files by type."""
        counts = {"python": 0, "tests": 0, "sql": 0, "yaml": 0, "guides": 0, "total": 0}

        try:
            # Count files in NBA Simulator AWS phases directory
            phases_dir = "/Users/ryanranft/nba-simulator-aws/docs/phases"
            if os.path.exists(phases_dir):
                for root, dirs, files in os.walk(phases_dir):
                    for file in files:
                        if file.startswith("implement_") and file.endswith(".py"):
                            counts["python"] += 1
                        elif file.startswith("test_") and file.endswith(".py"):
                            counts["tests"] += 1
                        elif file.endswith(".sql"):
                            counts["sql"] += 1
                        elif file.endswith(".yaml"):
                            counts["yaml"] += 1
                        elif file.endswith("IMPLEMENTATION_GUIDE.md"):
                            counts["guides"] += 1

                counts["total"] = (
                    counts["python"]
                    + counts["tests"]
                    + counts["sql"]
                    + counts["yaml"]
                    + counts["guides"]
                )
        except Exception as e:
            pass

        return counts

    def _read_progress(self) -> Optional[Dict[str, Any]]:
        """Read progress from the progress file."""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            pass
        return None

    def _launch_deployment(self):
        """Launch the Multi-Pass Book Deployment in background."""
        print(
            f"{self.COLORS['CYAN']}Launching Multi-Pass Book Deployment...{self.COLORS['END']}"
        )

        # Set up environment
        env = os.environ.copy()

        # Launch deployment process
        self.deployment_process = subprocess.Popen(
            [sys.executable, "scripts/multi_pass_book_deployment.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            cwd=os.getcwd(),
        )

        self.start_time = datetime.now()
        print(
            f"{self.COLORS['GREEN']}Deployment launched successfully!{self.COLORS['END']}"
        )

    def _display_progress(self, progress: Dict[str, Any]):
        """Display current progress information."""
        self._clear_screen()

        # Header
        print(f"{self.COLORS['BOLD']}{self.COLORS['CYAN']}{'='*40}")
        print("Multi-Pass Book Deployment Monitor")
        print(f"{'='*40}{self.COLORS['END']}")

        # Status and timing
        status = progress.get("status", "UNKNOWN")
        status_color = (
            self.COLORS["GREEN"] if status == "RUNNING" else self.COLORS["YELLOW"]
        )
        print(f"Status: {status_color}{status}{self.COLORS['END']}")

        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Elapsed: {self._format_time(elapsed)}")

        # Current pass
        current_pass = progress.get("current_pass", "Unknown")
        pass_name = progress.get("pass_name", "")
        if pass_name:
            print(
                f"Current Pass: {self.COLORS['BLUE']}{current_pass} - {pass_name}{self.COLORS['END']}"
            )
        else:
            print(
                f"Current Pass: {self.COLORS['BLUE']}{current_pass}{self.COLORS['END']}"
            )

        print()

        # Progress bar
        processed = progress.get("recommendations_processed", 0)
        total = progress.get("total_recommendations", 201)
        percentage = (processed / total * 100) if total > 0 else 0

        progress_bar = self._create_progress_bar(processed, total)
        print(f"Progress: {progress_bar} {processed}/{total} ({percentage:.1f}%)")

        # Files generated
        file_counts = self._get_file_counts()
        print(
            f"\nFiles Generated: {self.COLORS['GREEN']}{file_counts['total']}{self.COLORS['END']} total"
        )
        print(f"- Python implementations: {file_counts['python']}")
        print(f"- Unit tests: {file_counts['tests']}")
        print(f"- SQL migrations: {file_counts['sql']}")
        print(f"- CloudFormation: {file_counts['yaml']}")
        print(f"- Implementation guides: {file_counts['guides']}")

        # Circuit breaker status
        circuit_breaker = progress.get("circuit_breaker_state", "UNKNOWN")
        skipped = progress.get("skipped_recommendations", 0)

        if circuit_breaker == "OPEN":
            print(
                f"\nCircuit Breaker: {self.COLORS['RED']}OPEN{self.COLORS['END']} ({skipped} skipped)"
            )
        else:
            print(
                f"\nCircuit Breaker: {self.COLORS['GREEN']}{circuit_breaker}{self.COLORS['END']}"
            )

        # Latest activity
        latest_activity = progress.get("latest_activity", "No recent activity")
        print(f"\nLatest: {latest_activity}")

        # Next update
        print(
            f"\n{self.COLORS['YELLOW']}Next update in 30 seconds...{self.COLORS['END']}"
        )
        print(
            f"{self.COLORS['WHITE']}Press Ctrl+C to stop monitoring{self.COLORS['END']}"
        )

    def _display_completion_summary(self, progress: Dict[str, Any]):
        """Display final completion summary."""
        self._clear_screen()

        print(f"{self.COLORS['BOLD']}{self.COLORS['GREEN']}{'='*50}")
        print("DEPLOYMENT COMPLETED SUCCESSFULLY!")
        print(f"{'='*50}{self.COLORS['END']}")

        # Timing
        if self.start_time:
            total_time = (datetime.now() - self.start_time).total_seconds()
            print(f"Total Execution Time: {self._format_time(total_time)}")

        # Final statistics
        processed = progress.get("recommendations_processed", 0)
        total = progress.get("total_recommendations", 201)
        success_rate = progress.get("success_rate", 0)

        print(f"\nFinal Statistics:")
        print(f"- Recommendations Processed: {processed}/{total}")
        print(f"- Success Rate: {success_rate:.1f}%")

        # File counts
        file_counts = self._get_file_counts()
        print(f"\nFiles Generated:")
        print(f"- Python implementations: {file_counts['python']}")
        print(f"- Unit tests: {file_counts['tests']}")
        print(f"- SQL migrations: {file_counts['sql']}")
        print(f"- CloudFormation: {file_counts['yaml']}")
        print(f"- Implementation guides: {file_counts['guides']}")
        print(f"- Total files: {file_counts['total']}")

        # Circuit breaker stats
        skipped = progress.get("skipped_recommendations", 0)
        if skipped > 0:
            print(
                f"\nCircuit Breaker: {self.COLORS['YELLOW']}{skipped} recommendations skipped{self.COLORS['END']}"
            )

        # File locations
        print(f"\nGenerated files location:")
        print(f"- NBA Simulator AWS: /Users/ryanranft/nba-simulator-aws/docs/phases/")

        print(
            f"\n{self.COLORS['GREEN']}Deployment monitoring complete!{self.COLORS['END']}"
        )

    def _check_for_crashes(self, progress: Dict[str, Any]) -> bool:
        """Check if deployment process has crashed."""
        if not self.deployment_process:
            return True

        # Check if process is still running
        if self.deployment_process.poll() is not None:
            return True

        # Check if progress file hasn't been updated in 2+ minutes
        last_update = progress.get("last_update")
        if last_update:
            try:
                last_update_time = datetime.fromisoformat(last_update)
                if (datetime.now() - last_update_time).total_seconds() > 120:
                    return True
            except:
                pass

        return False

    def run(self):
        """Main monitoring loop."""
        print(
            f"{self.COLORS['BOLD']}{self.COLORS['CYAN']}Starting Multi-Pass Book Deployment Monitor{self.COLORS['END']}"
        )

        # Launch deployment
        self._launch_deployment()

        # Monitoring loop
        while self.running:
            try:
                progress = self._read_progress()

                if progress:
                    # Check for completion
                    if progress.get("completed", False):
                        self._display_completion_summary(progress)
                        break

                    # Check for crashes
                    if self._check_for_crashes(progress):
                        print(
                            f"\n{self.COLORS['RED']}Deployment process appears to have crashed or stalled!{self.COLORS['END']}"
                        )
                        break

                    # Display progress
                    self._display_progress(progress)
                    self.last_progress_time = datetime.now()
                else:
                    # No progress file yet, show waiting message
                    self._clear_screen()
                    print(
                        f"{self.COLORS['YELLOW']}Waiting for deployment to start...{self.COLORS['END']}"
                    )

                # Wait 30 seconds
                time.sleep(30)

            except KeyboardInterrupt:
                print(
                    f"\n{self.COLORS['YELLOW']}Monitoring interrupted by user{self.COLORS['END']}"
                )
                break
            except Exception as e:
                print(
                    f"\n{self.COLORS['RED']}Error in monitoring loop: {e}{self.COLORS['END']}"
                )
                time.sleep(30)

        # Cleanup
        if self.deployment_process:
            self.deployment_process.terminate()
            self.deployment_process.wait()


def main():
    """Main entry point."""
    monitor = DeploymentMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
