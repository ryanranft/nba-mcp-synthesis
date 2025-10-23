from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional, Any, Dict


def _getenv(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    return val if val is not None and val != "" else default


@dataclass
class AdapterConfig:
    # Adapter server
    host: str = "0.0.0.0"
    port: int = 5055
    log_level: str = "INFO"

    # MCP
    mcp_server_url: str = "http://localhost:3000"
    connect_on_start: bool = True

    # Inventory
    project_config_path: str = "project_configs/nba_mcp_synthesis.json"
    inventory_report_path: str = "data_inventory_report.json"
    inventory_enabled_default: bool = True

    # Caching (seconds)
    tools_cache_ttl: int = 300
    inventory_cache_ttl: int = 900

    # Misc
    environment: str = "development"


def load_project_config(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def get_config() -> AdapterConfig:
    return AdapterConfig(
        host=_getenv("PLAYGROUND_ADAPTER_HOST", "0.0.0.0") or "0.0.0.0",
        port=int(_getenv("PLAYGROUND_ADAPTER_PORT", "5055") or "5055"),
        log_level=_getenv("PLAYGROUND_ADAPTER_LOG_LEVEL", "INFO") or "INFO",
        mcp_server_url=_getenv("MCP_SERVER_URL", "http://localhost:3000")
        or "http://localhost:3000",
        connect_on_start=(_getenv("PLAYGROUND_CONNECT_ON_START", "true") or "true")
        .lower()
        .strip()
        == "true",
        project_config_path=_getenv(
            "PLAYGROUND_PROJECT_CONFIG", "project_configs/nba_mcp_synthesis.json"
        )
        or "project_configs/nba_mcp_synthesis.json",
        inventory_report_path=_getenv(
            "PLAYGROUND_INVENTORY_REPORT", "data_inventory_report.json"
        )
        or "data_inventory_report.json",
        inventory_enabled_default=(
            _getenv("PLAYGROUND_INVENTORY_ENABLED", "true") or "true"
        )
        .lower()
        .strip()
        == "true",
        tools_cache_ttl=int(_getenv("PLAYGROUND_TOOLS_CACHE_TTL", "300") or "300"),
        inventory_cache_ttl=int(
            _getenv("PLAYGROUND_INVENTORY_CACHE_TTL", "900") or "900"
        ),
        environment=_getenv("PLAYGROUND_ENV", "development") or "development",
    )
