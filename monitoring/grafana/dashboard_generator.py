#!/usr/bin/env python3
"""
Grafana Dashboard Generator
Programmatically creates and updates Grafana dashboards
"""

import json
import os
import requests
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class GrafanaDashboardGenerator:
    """Generate and upload Grafana dashboards"""

    def __init__(
        self,
        grafana_url: str = "http://localhost:3000",
        api_key: Optional[str] = None,
        username: str = "admin",
        password: str = "admin"
    ):
        self.grafana_url = grafana_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.password = password
        self.dashboards_dir = os.path.join(
            os.path.dirname(__file__),
            "dashboards"
        )

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    def _get_auth(self):
        """Get authentication tuple for requests"""
        if self.api_key:
            return None
        return (self.username, self.password)

    def load_dashboard_json(self, filename: str) -> Dict[str, Any]:
        """Load dashboard JSON from file"""
        filepath = os.path.join(self.dashboards_dir, filename)

        with open(filepath, 'r') as f:
            data = json.load(f)

        return data

    def upload_dashboard(
        self,
        dashboard_data: Dict[str, Any],
        folder_name: str = "NBA MCP Synthesis",
        overwrite: bool = True
    ) -> bool:
        """
        Upload dashboard to Grafana

        Args:
            dashboard_data: Dashboard JSON data
            folder_name: Folder to organize dashboard
            overwrite: Whether to overwrite existing dashboard

        Returns:
            True if successful
        """
        try:
            # Ensure folder exists
            folder_id = self._ensure_folder(folder_name)

            # Prepare dashboard payload
            payload = {
                "dashboard": dashboard_data.get("dashboard", dashboard_data),
                "folderId": folder_id,
                "overwrite": overwrite
            }

            # Upload dashboard
            response = requests.post(
                f"{self.grafana_url}/api/dashboards/db",
                json=payload,
                headers=self._get_auth_headers(),
                auth=self._get_auth(),
                timeout=10
            )

            if response.status_code in [200, 201]:
                dashboard_title = payload["dashboard"].get("title", "Unknown")
                logger.info(f"✅ Uploaded dashboard: {dashboard_title}")
                return True
            else:
                logger.error(f"Failed to upload dashboard: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error uploading dashboard: {e}")
            return False

    def _ensure_folder(self, folder_name: str) -> int:
        """Ensure folder exists and return folder ID"""
        try:
            # Check if folder exists
            response = requests.get(
                f"{self.grafana_url}/api/folders",
                headers=self._get_auth_headers(),
                auth=self._get_auth(),
                timeout=10
            )

            if response.status_code == 200:
                folders = response.json()
                for folder in folders:
                    if folder.get("title") == folder_name:
                        return folder.get("id")

            # Create folder if not exists
            response = requests.post(
                f"{self.grafana_url}/api/folders",
                json={"title": folder_name},
                headers=self._get_auth_headers(),
                auth=self._get_auth(),
                timeout=10
            )

            if response.status_code in [200, 201]:
                return response.json().get("id")

            # Return 0 (general folder) as fallback
            return 0

        except Exception as e:
            logger.warning(f"Error ensuring folder: {e}")
            return 0

    def upload_all_dashboards(self) -> Dict[str, bool]:
        """Upload all dashboards from dashboards directory"""
        results = {}

        dashboard_files = [
            "nba_synthesis.json",
            "workflow_metrics.json",
            "cost_analysis.json"
        ]

        for filename in dashboard_files:
            filepath = os.path.join(self.dashboards_dir, filename)

            if not os.path.exists(filepath):
                logger.warning(f"Dashboard file not found: {filename}")
                results[filename] = False
                continue

            try:
                dashboard_data = self.load_dashboard_json(filename)
                success = self.upload_dashboard(dashboard_data)
                results[filename] = success
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
                results[filename] = False

        return results

    def create_custom_panel(
        self,
        title: str,
        panel_type: str,
        query: str,
        grid_pos: Dict[str, int],
        panel_id: int = 1
    ) -> Dict[str, Any]:
        """
        Create a custom panel configuration

        Args:
            title: Panel title
            panel_type: Type of panel (graph, stat, table, etc.)
            query: Prometheus query
            grid_pos: Grid position {"h": height, "w": width, "x": x, "y": y}
            panel_id: Unique panel ID

        Returns:
            Panel configuration dict
        """
        panel = {
            "id": panel_id,
            "title": title,
            "type": panel_type,
            "gridPos": grid_pos,
            "targets": [
                {
                    "expr": query,
                    "refId": "A"
                }
            ]
        }

        # Add type-specific configurations
        if panel_type == "graph":
            panel["yaxes"] = [
                {"format": "short"},
                {"format": "short"}
            ]
        elif panel_type == "stat":
            panel["fieldConfig"] = {
                "defaults": {
                    "unit": "short"
                }
            }

        return panel


# CLI for testing
if __name__ == "__main__":
    import sys

    print("="*70)
    print("Grafana Dashboard Generator")
    print("="*70)
    print()

    # Check environment
    grafana_url = os.getenv("GRAFANA_URL", "http://localhost:3000")
    grafana_user = os.getenv("GRAFANA_USER", "admin")
    grafana_password = os.getenv("GRAFANA_PASSWORD", "admin")

    print(f"Grafana URL: {grafana_url}")
    print(f"Username: {grafana_user}")
    print()

    # Create generator
    generator = GrafanaDashboardGenerator(
        grafana_url=grafana_url,
        username=grafana_user,
        password=grafana_password
    )

    # Test connection
    print("Testing Grafana connection...")
    try:
        response = requests.get(
            f"{grafana_url}/api/health",
            auth=(grafana_user, grafana_password),
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Connected to Grafana")
        else:
            print(f"❌ Connection failed: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to Grafana: {e}")
        print()
        print("Make sure Grafana is running:")
        print("  docker-compose up -d grafana")
        sys.exit(1)

    print()

    # Upload dashboards
    print("Uploading dashboards...")
    results = generator.upload_all_dashboards()

    print()
    print("Results:")
    for filename, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {filename}")

    print()
    total = len(results)
    successful = sum(1 for s in results.values() if s)

    print(f"Uploaded {successful}/{total} dashboards successfully")
    print()

    if successful > 0:
        print("View dashboards at:")
        print(f"  {grafana_url}/dashboards")

    print("="*70)
