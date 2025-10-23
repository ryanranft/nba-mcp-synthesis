from __future__ import annotations

import asyncio
import json
import logging
import os
import traceback
import uuid
from typing import Any, Dict, Optional, Tuple

from flask import Flask, jsonify, request

# Local modules
from playground_adapter.config import get_config, load_project_config
from playground_adapter.cache import TTLCache

# Use existing MCP client
from synthesis.mcp_client import MCPClient

app = Flask(__name__)
cfg = get_config()

logging.basicConfig(
    level=getattr(logging, cfg.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("playground-adapter")

# Global MCP client (lazy connection)
_mcp_client: Optional[MCPClient] = None

# Caches
cache = TTLCache()
TOOLS_CACHE_KEY = "tools_list"
INVENTORY_CACHE_KEY = "inventory_summary"


def _correlation_id() -> str:
    return request.headers.get("X-Correlation-Id") or str(uuid.uuid4())


def _json_response(payload: Dict[str, Any], status: int = 200):
    payload.setdefault("correlation_id", _correlation_id())
    return jsonify(payload), status


def _ensure_mcp() -> MCPClient:
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient(server_url=cfg.mcp_server_url)
    if not _mcp_client.connected:
        try:
            asyncio.run(_mcp_client.connect())
        except Exception as e:
            logger.warning(f"Failed to connect to MCP: {e}")
    return _mcp_client


def _read_inventory_from_report(path: str) -> Optional[Dict[str, Any]]:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            summary = data.get("summary_for_ai")
            if summary:
                return {
                    "enabled": True,
                    "summary": summary,
                    "source": "report",
                    "metadata": data.get("metadata", {}),
                }
    except Exception as e:
        logger.warning(f"Failed reading inventory report: {e}")
    return None


def _build_inventory_from_project_config() -> Optional[Dict[str, Any]]:
    project_cfg = load_project_config(cfg.project_config_path)
    di = (
        (project_cfg.get("data_inventory") or {})
        if isinstance(project_cfg, dict)
        else {}
    )
    enabled = di.get("enabled", cfg.inventory_enabled_default)
    if not enabled:
        return {"enabled": False, "summary": "", "source": "disabled"}

    # Compose a compact summary if detailed report not available
    db = di.get("database", {})
    cov = di.get("data_coverage", {})
    systems = di.get("systems", [])
    key_tables = db.get("key_tables", [])

    parts = []
    parts.append("## 📊 DATA INVENTORY SUMMARY")
    if key_tables:
        parts.append(f"Key Tables: {', '.join(key_tables)}")
    if cov:
        s3_objects = cov.get("s3_objects")
        s3_gb = cov.get("s3_size_gb")
        seasons = cov.get("seasons") or cov.get("seasons_estimated")
        cov_bits = []
        if s3_objects:
            cov_bits.append(f"{s3_objects} S3 objects")
        if s3_gb:
            cov_bits.append(f"{s3_gb} GB")
        if seasons:
            cov_bits.append(f"Seasons: {seasons}")
        if cov_bits:
            parts.append(f"Coverage: {', '.join(cov_bits)}")
    if systems:
        parts.append(f"Available Systems: {', '.join(systems)}")
    summary = "\n".join(parts)

    return {
        "enabled": True,
        "summary": summary,
        "source": "project_config",
        "metadata": {"database": db, "data_coverage": cov, "systems": systems},
    }


def get_inventory_summary(force_refresh: bool = False) -> Dict[str, Any]:
    if not force_refresh:
        cached = cache.get(INVENTORY_CACHE_KEY)
        if cached:
            return cached

    # Prefer report, fallback to project config synthesized summary
    result = _read_inventory_from_report(cfg.inventory_report_path)
    if not result:
        result = _build_inventory_from_project_config() or {
            "enabled": cfg.inventory_enabled_default,
            "summary": "",
            "source": "none",
        }

    cache.set(INVENTORY_CACHE_KEY, result, ttl=cfg.inventory_cache_ttl)
    return result


@app.route("/health", methods=["GET"])
def health():
    tools_count = None
    mcp_up = False
    try:
        client = _ensure_mcp()
        if client.connected:
            # Try cached tools first
            tools = cache.get(TOOLS_CACHE_KEY)
            if tools is None:
                tools = client.available_tools or []
                cache.set(TOOLS_CACHE_KEY, tools, ttl=cfg.tools_cache_ttl)
            tools_count = len(tools)
            mcp_up = True
    except Exception:
        mcp_up = False

    inv = get_inventory_summary(force_refresh=False)
    return _json_response(
        {
            "status": "ok",
            "mcp": {"up": mcp_up, "tools_count": tools_count},
            "inventory": {
                "enabled": inv.get("enabled", False),
                "source": inv.get("source"),
            },
            "environment": cfg.environment,
        }
    )


@app.route("/mcp/tools", methods=["GET"])
def list_tools():
    try:
        client = _ensure_mcp()
        tools = cache.get(TOOLS_CACHE_KEY)
        if tools is None:
            tools = client.available_tools or []
            cache.set(TOOLS_CACHE_KEY, tools, ttl=cfg.tools_cache_ttl)
        return _json_response({"tools": tools, "cached": tools is not None})
    except Exception as e:
        return _json_response({"error": str(e)}, status=500)


@app.route("/mcp/call", methods=["POST"])
def call_tool():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    arguments = payload.get("arguments") or {}
    if not name:
        return _json_response({"error": "Missing 'name' in body"}, status=400)

    # Propagate correlation id for auditing
    arguments.setdefault("_client_id", _correlation_id())

    try:
        client = _ensure_mcp()
        result = asyncio.run(client.call_tool(name, arguments))
        return _json_response(result, status=200 if result.get("success") else 400)
    except Exception as e:
        logger.error(f"Tool call failed: {e}\n{traceback.format_exc()}")
        return _json_response(
            {"success": False, "tool": name, "error": str(e)}, status=500
        )


@app.route("/context/gather", methods=["POST"])
def gather_context():
    payload = request.get_json(silent=True) or {}
    query_type = payload.get("query_type")
    user_input = payload.get("user_input")
    code = payload.get("code")
    include_inventory = bool(payload.get("include_inventory", True))

    if not query_type or not user_input:
        return _json_response(
            {"error": "query_type and user_input are required"}, status=400
        )

    try:
        client = _ensure_mcp()
        ctx = asyncio.run(
            client.gather_context(
                query_type=query_type, user_input=user_input, code=code
            )
        )
        if include_inventory:
            inv = get_inventory_summary(force_refresh=False)
            if inv.get("enabled"):
                ctx["inventory_summary"] = inv.get("summary", "")
        return _json_response(ctx)
    except Exception as e:
        logger.error(f"gather_context failed: {e}\n{traceback.format_exc()}")
        return _json_response({"error": str(e)}, status=500)


@app.route("/inventory/summary", methods=["GET"])
def inventory_summary():
    refresh = request.args.get("refresh") == "true"
    try:
        inv = get_inventory_summary(force_refresh=refresh)
        return _json_response(inv)
    except Exception as e:
        return _json_response({"error": str(e)}, status=500)


@app.route("/playground/session/experiment", methods=["POST"])
def create_experiment():
    """
    Bridge to an MCP tool if available, otherwise return 501 to indicate unsupported.
    """
    payload = request.get_json(silent=True) or {}
    args = {
        "session_id": payload.get("session_id"),
        "experiment_name": payload.get("experiment_name"),
        "description": payload.get("description"),
        "_client_id": _correlation_id(),
    }
    tool_name = "playground_create_experiment"
    try:
        client = _ensure_mcp()
        if tool_name in (client.available_tools or []):
            result = asyncio.run(client.call_tool(tool_name, args))
            return _json_response(result, status=200 if result.get("success") else 400)
        return _json_response(
            {"success": False, "error": f"Tool '{tool_name}' not available"}, status=501
        )
    except Exception as e:
        return _json_response({"success": False, "error": str(e)}, status=500)


@app.route("/playground/session/visualizations", methods=["POST"])
def generate_visualizations():
    """
    Bridge to an MCP tool if available, otherwise return 501 to indicate unsupported.
    """
    payload = request.get_json(silent=True) or {}
    args = {
        "session_id": payload.get("session_id"),
        "visualization_types": payload.get("visualization_types") or [],
        "_client_id": _correlation_id(),
    }
    tool_name = "playground_generate_visualizations"
    try:
        client = _ensure_mcp()
        if tool_name in (client.available_tools or []):
            result = asyncio.run(client.call_tool(tool_name, args))
            return _json_response(result, status=200 if result.get("success") else 400)
        return _json_response(
            {"success": False, "error": f"Tool '{tool_name}' not available"}, status=501
        )
    except Exception as e:
        return _json_response({"success": False, "error": str(e)}, status=500)


def create_app() -> Flask:
    # Optionally connect on start
    if cfg.connect_on_start:
        try:
            _ensure_mcp()
        except Exception as e:
            logger.warning(f"Deferred MCP connection due to error: {e}")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=cfg.host, port=cfg.port)
