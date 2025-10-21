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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
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




