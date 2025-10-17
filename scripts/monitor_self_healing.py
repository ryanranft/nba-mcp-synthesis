#!/usr/bin/env python3
"""
Self-Healing Workflow Monitor
Monitors the progress of the self-healing workflow.
"""

import os
import sys
import time
import psutil
import json
from datetime import datetime
from pathlib import Path


def monitor_workflow():
    """Monitor the self-healing workflow."""
    print("🔍 Monitoring Self-Healing Workflow...")
    print("=" * 50)

    # Find the workflow process
    workflow_pid = None
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""
            if "master_self_healing_orchestrator.py" in cmdline:
                workflow_pid = proc.info["pid"]
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not workflow_pid:
        print("❌ Self-healing workflow not found")
        return

    print(f"📊 Found workflow process: PID {workflow_pid}")

    # Monitor for 2 minutes
    start_time = time.time()
    iteration = 0

    while time.time() - start_time < 120:  # 2 minutes
        iteration += 1
        print(f"\n🔄 Check {iteration} ({time.time() - start_time:.1f}s elapsed)")

        try:
            proc = psutil.Process(workflow_pid)
            if proc.is_running():
                runtime = time.time() - proc.create_time()
                print(
                    f"✅ Workflow running (PID: {workflow_pid}, Runtime: {runtime:.1f}s)"
                )

                # Check for new log files
                log_files = list(Path("logs").glob("*.json"))
                recent_logs = [
                    f for f in log_files if f.stat().st_mtime > start_time - 60
                ]

                if recent_logs:
                    print(f"📄 Recent log files: {len(recent_logs)}")
                    for log_file in recent_logs:
                        print(f"   - {log_file.name}")

                # Check for any other processes
                other_processes = []
                for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                    try:
                        cmdline = (
                            " ".join(proc.info["cmdline"])
                            if proc.info["cmdline"]
                            else ""
                        )
                        if any(
                            target in cmdline
                            for target in [
                                "individual_model_tester.py",
                                "immediate_status_checker.py",
                                "deployment_manager.py",
                            ]
                        ):
                            other_processes.append(
                                f"{proc.info['name']} (PID: {proc.info['pid']})"
                            )
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                if other_processes:
                    print(f"🔧 Sub-processes: {', '.join(other_processes)}")
                else:
                    print("ℹ️ No sub-processes running")

            else:
                print("❌ Workflow process stopped")
                break

        except psutil.NoSuchProcess:
            print("❌ Workflow process not found")
            break
        except Exception as e:
            print(f"❌ Error monitoring: {e}")

        time.sleep(10)  # Check every 10 seconds

    print(f"\n📊 Monitoring complete after {time.time() - start_time:.1f}s")


if __name__ == "__main__":
    monitor_workflow()
