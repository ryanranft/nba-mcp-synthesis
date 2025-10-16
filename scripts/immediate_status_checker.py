#!/usr/bin/env python3
"""
Immediate Process Status Checker
Quickly checks what's running and validates timestamps.
"""

import os
import sys
import time
import psutil
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class ProcessStatus:
    pid: int
    name: str
    command: str
    start_time: float
    runtime_seconds: float
    status: str
    expected_max_runtime: int = 300

class ImmediateStatusChecker:
    """Immediate status checker for running processes."""

    def __init__(self):
        self.target_processes = [
            'automated_workflow.py',
            'simplified_recursive_analysis.py',
            'resilient_book_analyzer.py',
            'four_model_book_analyzer.py',
            'recursive_book_analysis.py'
        ]

    def check_all_processes(self) -> List[ProcessStatus]:
        """Check all running processes."""
        processes = []
        current_time = time.time()

        print("🔍 Checking for running processes...")

        for proc in psutil.process_iter(['pid', 'name', 'create_time', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''

                # Check if this is one of our target processes
                for target in self.target_processes:
                    if target in cmdline:
                        runtime = current_time - proc.info['create_time']

                        process_status = ProcessStatus(
                            pid=proc.info['pid'],
                            name=proc.info['name'],
                            command=cmdline,
                            start_time=proc.info['create_time'],
                            runtime_seconds=runtime,
                            status='running',
                            expected_max_runtime=self._get_expected_runtime(target)
                        )

                        processes.append(process_status)
                        print(f"📊 Found: {target} (PID: {proc.info['pid']}, Runtime: {runtime:.1f}s)")
                        break

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return processes

    def _get_expected_runtime(self, process_name: str) -> int:
        """Get expected maximum runtime for a process."""
        runtime_map = {
            'automated_workflow.py': 3600,  # 1 hour
            'simplified_recursive_analysis.py': 300,  # 5 minutes
            'resilient_book_analyzer.py': 300,  # 5 minutes
            'four_model_book_analyzer.py': 300,  # 5 minutes
            'recursive_book_analysis.py': 300,  # 5 minutes
        }
        return runtime_map.get(process_name, 300)

    def validate_timestamps(self, processes: List[ProcessStatus]) -> Dict[str, Any]:
        """Validate timestamps and detect timing issues."""
        issues = []
        current_time = time.time()

        for process in processes:
            # Check if runtime is reasonable
            if process.runtime_seconds > process.expected_max_runtime:
                issues.append(f"Process {process.name} (PID {process.pid}) running for {process.runtime_seconds:.1f}s (expected max: {process.expected_max_runtime}s)")

            # Check if start time is reasonable (not in the future)
            if process.start_time > current_time:
                issues.append(f"Process {process.name} (PID {process.pid}) has future start time: {process.start_time}")

            # Check if start time is too old (more than 24 hours)
            if current_time - process.start_time > 86400:  # 24 hours
                issues.append(f"Process {process.name} (PID {process.pid}) has been running for over 24 hours")

        return {
            'issues': issues,
            'total_processes': len(processes),
            'stuck_processes': len([p for p in processes if p.runtime_seconds > p.expected_max_runtime])
        }

    def check_api_keys(self) -> Dict[str, bool]:
        """Check if API keys are set."""
        required_keys = ['GOOGLE_API_KEY', 'DEEPSEEK_API_KEY', 'ANTHROPIC_API_KEY', 'OPENAI_API_KEY']
        status = {}

        print("\n🔑 Checking API keys...")

        for key in required_keys:
            value = os.getenv(key)
            if value and len(value) > 10:
                status[key] = True
                print(f"✅ {key}: Set")
            else:
                status[key] = False
                print(f"❌ {key}: Not set or invalid")

        return status

    def check_log_files(self) -> Dict[str, Any]:
        """Check log files for recent activity."""
        log_info = {}

        print("\n📄 Checking log files...")

        import glob
        log_files = glob.glob("logs/workflow_*.log")

        for log_file in log_files:
            try:
                stat = os.stat(log_file)
                size = stat.st_size
                modified_time = stat.st_mtime
                age_seconds = time.time() - modified_time

                log_info[log_file] = {
                    'size': size,
                    'modified_time': modified_time,
                    'age_seconds': age_seconds,
                    'last_modified': datetime.fromtimestamp(modified_time).isoformat()
                }

                print(f"📄 {log_file}: {size} bytes, modified {age_seconds:.1f}s ago")

            except Exception as e:
                print(f"❌ Error checking {log_file}: {e}")

        return log_info

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report."""
        print("\n" + "="*60)
        print("📊 IMMEDIATE STATUS REPORT")
        print("="*60)

        # Check processes
        processes = self.check_all_processes()

        # Validate timestamps
        timestamp_validation = self.validate_timestamps(processes)

        # Check API keys
        api_status = self.check_api_keys()

        # Check log files
        log_status = self.check_log_files()

        # Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'processes': [asdict(p) for p in processes],
            'timestamp_validation': timestamp_validation,
            'api_keys': api_status,
            'log_files': log_status,
            'summary': {
                'total_processes': len(processes),
                'stuck_processes': timestamp_validation['stuck_processes'],
                'api_keys_valid': sum(api_status.values()),
                'api_keys_total': len(api_status),
                'log_files_count': len(log_status)
            }
        }

        # Print summary
        print(f"\n📊 SUMMARY:")
        print(f"   Total processes: {report['summary']['total_processes']}")
        print(f"   Stuck processes: {report['summary']['stuck_processes']}")
        print(f"   Valid API keys: {report['summary']['api_keys_valid']}/{report['summary']['api_keys_total']}")
        print(f"   Log files: {report['summary']['log_files_count']}")

        if timestamp_validation['issues']:
            print(f"\n⚠️ ISSUES DETECTED:")
            for issue in timestamp_validation['issues']:
                print(f"   - {issue}")

        return report

def main():
    """Main function."""
    checker = ImmediateStatusChecker()
    report = checker.generate_report()

    # Save report
    report_file = f"logs/immediate_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Report saved to: {report_file}")

    return report

if __name__ == "__main__":
    main()

