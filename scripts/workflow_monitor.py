#!/usr/bin/env python3
"""
Real-Time Workflow Monitor Dashboard

Provides a web-based dashboard for monitoring workflow progress, costs, and system health.
Accessible at http://localhost:8080

Author: NBA MCP Synthesis System
Version: 3.0
"""

import os
import json
import logging
import threading
import time
import glob
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Import existing components
try:
    from phase_status_manager import PhaseStatusManager
    from cost_safety_manager import CostSafetyManager
    from resource_monitor import ResourceMonitor
except ImportError:
    # Allow standalone testing
    PhaseStatusManager = None
    CostSafetyManager = None
    ResourceMonitor = None

logger = logging.getLogger(__name__)


class WorkflowMonitor:
    """Real-time workflow monitoring dashboard."""

    def __init__(self, port: int = 8080, auto_start: bool = False):
        """
        Initialize Workflow Monitor.

        Args:
            port: Port for Flask app (default 8080)
            auto_start: Auto-start dashboard in background thread
        """
        self.port = port
        self.app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent.parent / 'templates'),
            static_folder=str(Path(__file__).parent.parent / 'static')
        )
        CORS(self.app)  # Enable CORS for API requests

        # Components
        self.status_manager = PhaseStatusManager() if PhaseStatusManager else None
        self.cost_tracker = CostSafetyManager() if CostSafetyManager else None
        self.resource_monitor = ResourceMonitor() if ResourceMonitor else None

        # State
        self.start_time = datetime.now()
        self.workflow_active = False
        self.current_phase = None
        self.books_processed = 0
        self.total_books = 0

        # Setup routes
        self._setup_routes()

        logger.info(f"Workflow Monitor initialized on port {port}")

        if auto_start:
            self.start_background()

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/')
        def dashboard():
            """Main dashboard page."""
            return render_template('dashboard.html')

        @self.app.route('/api/status')
        def get_status():
            """Get current workflow status."""
            return jsonify(self.get_status_data())

        @self.app.route('/api/phases')
        def get_phases():
            """Get phase status details."""
            if not self.status_manager:
                return jsonify({'error': 'PhaseStatusManager not available'}), 503

            try:
                phases = self.status_manager.get_all_phases()
                return jsonify(phases)
            except Exception as e:
                logger.error(f"Failed to get phases: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/cost')
        def get_cost():
            """Get cost tracking details."""
            if not self.cost_tracker:
                return jsonify({'error': 'CostSafetyManager not available'}), 503

            try:
                cost_data = {
                    'total_cost': self.cost_tracker.get_total_cost(),
                    'cost_by_phase': self.cost_tracker.get_cost_by_phase(),
                    'budget': self.cost_tracker.get_budget(),
                    'remaining': self.cost_tracker.get_remaining_budget()
                }
                return jsonify(cost_data)
            except Exception as e:
                logger.error(f"Failed to get cost data: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/system')
        def get_system():
            """Get system resource metrics."""
            if not self.resource_monitor:
                return jsonify({'error': 'ResourceMonitor not available'}), 503

            try:
                return jsonify(self.resource_monitor.get_system_metrics())
            except Exception as e:
                logger.error(f"Failed to get system metrics: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/live-progress')
        def get_live_progress():
            """Get real-time progress from filesystem."""
            try:
                return jsonify(self._get_live_progress())
            except Exception as e:
                logger.error(f"Failed to get live progress: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/logs/tail')
        def get_log_tail():
            """Get last N lines from log file."""
            try:
                lines = request.args.get('lines', default=20, type=int)
                return jsonify(self._get_log_tail(lines))
            except Exception as e:
                logger.error(f"Failed to get log tail: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/process-status')
        def get_process_status():
            """Get status of overnight convergence process."""
            try:
                return jsonify(self._get_process_status())
            except Exception as e:
                logger.error(f"Failed to get process status: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/update', methods=['POST'])
        def update_workflow():
            """Update workflow state (called by workflow scripts)."""
            try:
                data = request.get_json()
                if data.get('phase'):
                    self.current_phase = data['phase']
                if data.get('books_processed') is not None:
                    self.books_processed = data['books_processed']
                if data.get('total_books') is not None:
                    self.total_books = data['total_books']
                if data.get('active') is not None:
                    self.workflow_active = data['active']

                return jsonify({'status': 'updated'})
            except Exception as e:
                logger.error(f"Failed to update workflow: {e}")
                return jsonify({'error': str(e)}), 500

    def get_status_data(self) -> Dict:
        """Get comprehensive status data."""
        elapsed = (datetime.now() - self.start_time).total_seconds()

        # Calculate progress
        progress = 0.0
        if self.total_books > 0:
            progress = (self.books_processed / self.total_books) * 100

        # Estimate time remaining
        time_remaining = "Unknown"
        if self.books_processed > 0 and self.total_books > 0:
            time_per_book = elapsed / self.books_processed
            remaining_books = self.total_books - self.books_processed
            remaining_seconds = time_per_book * remaining_books
            time_remaining = self._format_duration(remaining_seconds)

        return {
            'timestamp': datetime.now().isoformat(),
            'workflow_active': self.workflow_active,
            'current_phase': self.current_phase,
            'elapsed': self._format_duration(elapsed),
            'time_remaining': time_remaining,
            'books': {
                'processed': self.books_processed,
                'total': self.total_books,
                'progress': round(progress, 1)
            }
        }

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def start_background(self):
        """Start dashboard in background thread."""
        thread = threading.Thread(
            target=self._run_flask,
            daemon=True
        )
        thread.start()
        logger.info(f"Dashboard started in background: http://localhost:{self.port}")

    def _run_flask(self):
        """Run Flask app (called by background thread)."""
        try:
            self.app.run(
                host='0.0.0.0',
                port=self.port,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"Flask app failed: {e}")

    def run(self, debug: bool = False):
        """Run dashboard in foreground (blocking)."""
        logger.info(f"Starting dashboard at http://localhost:{self.port}")
        try:
            self.app.run(
                host='0.0.0.0',
                port=self.port,
                debug=debug,
                use_reloader=False
            )
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        except Exception as e:
            logger.error(f"Dashboard error: {e}")

    def update_workflow_state(
        self,
        phase: Optional[str] = None,
        books_processed: Optional[int] = None,
        total_books: Optional[int] = None,
        active: Optional[bool] = None
    ):
        """
        Update workflow state.

        Args:
            phase: Current phase name
            books_processed: Number of books processed
            total_books: Total number of books
            active: Whether workflow is active
        """
        if phase is not None:
            self.current_phase = phase
        if books_processed is not None:
            self.books_processed = books_processed
        if total_books is not None:
            self.total_books = total_books
        if active is not None:
            self.workflow_active = active

    def _get_live_progress(self) -> Dict:
        """Get real-time progress by reading filesystem."""
        base_dir = Path(__file__).parent.parent
        analysis_dir = base_dir / 'analysis_results'

        # Count completed books
        completed_files = list(analysis_dir.glob('*_RECOMMENDATIONS_COMPLETE.md'))
        completed_count = len(completed_files)

        # Get total books from book_analyzer_inputs
        total_count = 51  # Default
        inputs_file = base_dir / 'book_analyzer_inputs.json'
        if inputs_file.exists():
            try:
                with open(inputs_file, 'r') as f:
                    data = json.load(f)
                    total_count = len(data.get('books', []))
            except:
                pass

        # Calculate progress
        progress = 0.0
        if total_count > 0:
            progress = (completed_count / total_count) * 100

        # Get current book from logs
        current_book = self._get_current_book_from_logs()

        return {
            'books_completed': completed_count,
            'total_books': total_count,
            'progress_percent': round(progress, 1),
            'current_book': current_book,
            'timestamp': datetime.now().isoformat()
        }

    def _get_current_book_from_logs(self) -> Optional[str]:
        """Parse current book being processed from log files."""
        base_dir = Path(__file__).parent.parent
        logs_dir = base_dir / 'logs'

        # Find most recent overnight convergence log
        log_files = list(logs_dir.glob('overnight_convergence_*.log'))
        if not log_files:
            return None

        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)

        try:
            # Read last 100 lines to find current book
            with open(latest_log, 'r') as f:
                lines = f.readlines()
                # Look for patterns like "Processing: BookName" or "Analyzing: BookName"
                for line in reversed(lines[-100:]):
                    if 'Processing:' in line or 'Analyzing:' in line:
                        # Extract book name
                        parts = line.split(':', 1)
                        if len(parts) > 1:
                            return parts[1].strip()
            return None
        except Exception as e:
            logger.error(f"Failed to parse current book: {e}")
            return None

    def _get_log_tail(self, num_lines: int = 20) -> Dict:
        """Get last N lines from most recent log file."""
        base_dir = Path(__file__).parent.parent
        logs_dir = base_dir / 'logs'

        # Find most recent overnight convergence log
        log_files = list(logs_dir.glob('overnight_convergence_*.log'))
        if not log_files:
            return {
                'log_file': None,
                'lines': [],
                'error': 'No log files found'
            }

        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)

        try:
            with open(latest_log, 'r') as f:
                all_lines = f.readlines()
                tail_lines = all_lines[-num_lines:] if len(all_lines) > num_lines else all_lines

            return {
                'log_file': latest_log.name,
                'lines': [line.rstrip() for line in tail_lines],
                'total_lines': len(all_lines),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to read log tail: {e}")
            return {
                'log_file': latest_log.name,
                'lines': [],
                'error': str(e)
            }

    def _get_process_status(self) -> Dict:
        """Get status of overnight convergence process."""
        try:
            # Find recursive_book_analysis.py process
            ps_output = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=5
            )

            process_info = None
            for line in ps_output.stdout.split('\n'):
                if 'recursive_book_analysis.py' in line:
                    parts = line.split()
                    if len(parts) >= 11:
                        process_info = {
                            'pid': parts[1],
                            'cpu_percent': parts[2],
                            'memory_percent': parts[3],
                            'status': 'running',
                            'command': ' '.join(parts[10:])
                        }
                        break

            if not process_info:
                # Check if any overnight convergence process is running
                for line in ps_output.stdout.split('\n'):
                    if 'overnight_convergence' in line or 'launch_with_secrets' in line:
                        parts = line.split()
                        if len(parts) >= 11:
                            process_info = {
                                'pid': parts[1],
                                'cpu_percent': parts[2],
                                'memory_percent': parts[3],
                                'status': 'running',
                                'command': ' '.join(parts[10:])
                            }
                            break

            if process_info:
                return {
                    'found': True,
                    'process': process_info,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'found': False,
                    'message': 'No overnight convergence process found',
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to get process status: {e}")
            return {
                'found': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def main():
    """Run dashboard standalone."""
    import argparse

    parser = argparse.ArgumentParser(description='Workflow Monitor Dashboard')
    parser.add_argument('--port', type=int, default=8080, help='Port for dashboard')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    monitor = WorkflowMonitor(port=args.port)

    print(f"\n{'='*60}")
    print(f"🎯 Workflow Monitor Dashboard")
    print(f"{'='*60}")
    print(f"\n📊 Dashboard URL: http://localhost:{args.port}")
    print(f"🔄 Auto-refresh: Every 2 seconds")
    print(f"⌨️  Press Ctrl+C to stop\n")
    print(f"{'='*60}\n")

    monitor.run(debug=args.debug)


if __name__ == '__main__':
    main()







