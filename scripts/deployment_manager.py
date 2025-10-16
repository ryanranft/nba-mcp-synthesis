#!/usr/bin/env python3
"""
Deployment Manager
Manages deployments with proper process control and monitoring.
"""

import os
import sys
import time
import signal
import subprocess
import psutil
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class DeploymentInfo:
    deployment_id: str
    pid: Optional[int]
    start_time: float
    status: str
    log_file: str
    command: List[str]

class DeploymentManager:
    """Manage deployments with proper process control."""

    def __init__(self):
        self.deployments: Dict[str, DeploymentInfo] = {}
        self.max_deployment_runtime = 3600  # 1 hour
        self.check_interval = 30  # 30 seconds

    def kill_all_deployments(self) -> bool:
        """Kill all running deployments."""
        print("🛑 Killing all deployments...")

        killed_count = 0

        # Find all our processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                # Check if this is one of our deployment processes
                if any(target in cmdline for target in [
                    'automated_workflow.py',
                    'simplified_recursive_analysis.py',
                    'resilient_book_analyzer.py',
                    'four_model_book_analyzer.py',
                    'recursive_book_analysis.py'
                ]):
                    print(f"🛑 Killing process: {proc.info['name']} (PID: {proc.info['pid']})")
                    try:
                        os.kill(proc.info['pid'], signal.SIGKILL)
                        killed_count += 1
                        print(f"✅ Killed PID {proc.info['pid']}")
                    except ProcessLookupError:
                        print(f"ℹ️ Process {proc.info['pid']} already terminated")
                    except Exception as e:
                        print(f"❌ Failed to kill PID {proc.info['pid']}: {e}")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        print(f"🛑 Killed {killed_count} processes")
        return killed_count > 0

    def wait_for_processes_to_stop(self, timeout: int = 30) -> bool:
        """Wait for processes to stop with timeout."""
        print(f"⏳ Waiting for processes to stop (timeout: {timeout}s)...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            running_processes = self._get_running_processes()
            if not running_processes:
                print("✅ All processes stopped")
                return True

            print(f"⏳ {len(running_processes)} processes still running...")
            time.sleep(2)

        print("⚠️ Timeout waiting for processes to stop")
        return False

    def _get_running_processes(self) -> List[Dict[str, Any]]:
        """Get list of running processes."""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                if any(target in cmdline for target in [
                    'automated_workflow.py',
                    'simplified_recursive_analysis.py',
                    'resilient_book_analyzer.py',
                    'four_model_book_analyzer.py',
                    'recursive_book_analysis.py'
                ]):
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': cmdline
                    })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return processes

    def validate_timing(self) -> Dict[str, Any]:
        """Validate timing of processes."""
        print("🕐 Validating process timing...")

        issues = []
        current_time = time.time()

        for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                if any(target in cmdline for target in [
                    'automated_workflow.py',
                    'simplified_recursive_analysis.py',
                    'resilient_book_analyzer.py',
                    'four_model_book_analyzer.py',
                    'recursive_book_analysis.py'
                ]):
                    runtime = current_time - proc.info['create_time']

                    # Check for timing issues
                    if proc.info['create_time'] > current_time:
                        issues.append(f"Process {proc.info['name']} (PID {proc.info['pid']}) has future start time")

                    if runtime > self.max_deployment_runtime:
                        issues.append(f"Process {proc.info['name']} (PID {proc.info['pid']}) running for {runtime:.1f}s (max: {self.max_deployment_runtime}s)")

                    print(f"📊 {proc.info['name']} (PID {proc.info['pid']}): Runtime {runtime:.1f}s")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            'issues': issues,
            'current_time': current_time,
            'timestamp': datetime.now().isoformat()
        }

    def launch_deployment(self, config_file: str = "config/books_to_analyze_all_ai_ml.json") -> Optional[str]:
        """Launch a new deployment."""
        print("🚀 Launching new deployment...")

        # Ensure logs directory exists
        Path("logs").mkdir(exist_ok=True)

        # Create log file
        log_file = f"logs/workflow_deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        # Build command
        cmd = [
            'python3', 'scripts/automated_workflow.py',
            '--config', config_file,
            '--budget', '410.0',
            '--output', 'analysis_results/'
        ]

        # Add environment variables
        env = os.environ.copy()

        try:
            # Launch process
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=open(log_file, 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid
            )

            deployment_id = f"deployment_{int(time.time())}"

            self.deployments[deployment_id] = DeploymentInfo(
                deployment_id=deployment_id,
                pid=process.pid,
                start_time=time.time(),
                status='running',
                log_file=log_file,
                command=cmd
            )

            print(f"🚀 Launched deployment {deployment_id} (PID: {process.pid})")
            print(f"📄 Log file: {log_file}")

            return deployment_id

        except Exception as e:
            print(f"❌ Failed to launch deployment: {e}")
            return None

    def monitor_deployment(self, deployment_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Monitor a deployment."""
        if deployment_id not in self.deployments:
            return {'error': 'Deployment not found'}

        deployment = self.deployments[deployment_id]
        start_time = time.time()

        print(f"📊 Monitoring deployment {deployment_id}...")

        while time.time() - start_time < timeout:
            # Check if process is still running
            try:
                if deployment.pid:
                    proc = psutil.Process(deployment.pid)
                    if proc.is_running():
                        runtime = time.time() - deployment.start_time
                        print(f"⏳ Deployment running for {runtime:.1f}s...")

                        # Check log file size
                        if os.path.exists(deployment.log_file):
                            size = os.path.getsize(deployment.log_file)
                            print(f"📄 Log file size: {size} bytes")

                        time.sleep(10)
                    else:
                        print("✅ Deployment completed")
                        deployment.status = 'completed'
                        break
                else:
                    print("❌ No PID found for deployment")
                    break

            except psutil.NoSuchProcess:
                print("✅ Deployment process terminated")
                deployment.status = 'completed'
                break
            except Exception as e:
                print(f"❌ Error monitoring deployment: {e}")
                break

        return {
            'deployment_id': deployment_id,
            'status': deployment.status,
            'runtime': time.time() - deployment.start_time,
            'log_file': deployment.log_file
        }

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get status of all deployments."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'deployments': {},
            'running_processes': self._get_running_processes()
        }

        for deployment_id, deployment in self.deployments.items():
            status['deployments'][deployment_id] = {
                'deployment_id': deployment.deployment_id,
                'pid': deployment.pid,
                'start_time': deployment.start_time,
                'status': deployment.status,
                'log_file': deployment.log_file,
                'command': deployment.command
            }

        return status

def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Deployment Manager')
    parser.add_argument('--action', choices=['kill', 'launch', 'monitor', 'status'], required=True)
    parser.add_argument('--deployment-id', help='Deployment ID for monitor action')
    parser.add_argument('--config', default='config/books_to_analyze_all_ai_ml.json')

    args = parser.parse_args()

    manager = DeploymentManager()

    if args.action == 'kill':
        manager.kill_all_deployments()
        manager.wait_for_processes_to_stop()

    elif args.action == 'launch':
        deployment_id = manager.launch_deployment(args.config)
        if deployment_id:
            print(f"✅ Deployment launched: {deployment_id}")
        else:
            print("❌ Failed to launch deployment")

    elif args.action == 'monitor':
        if not args.deployment_id:
            print("❌ Deployment ID required for monitor action")
            return

        result = manager.monitor_deployment(args.deployment_id)
        print(f"📊 Monitoring result: {result}")

    elif args.action == 'status':
        status = manager.get_deployment_status()
        print(f"📊 Deployment status: {json.dumps(status, indent=2)}")

if __name__ == "__main__":
    main()

