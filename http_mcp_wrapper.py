#!/usr/bin/env python3
"""
HTTP MCP Server Wrapper
=======================
Wraps stdio-based MCP servers and exposes them via HTTP/SSE endpoints.

This allows remote clients (like web-based Claude Code) to connect to
MCP servers running on your local machine.

Usage:
    python http_mcp_wrapper.py --host 0.0.0.0 --port 8080

Then expose via ngrok:
    ngrok http 8080

Architecture:
    Web Client → ngrok → HTTP Wrapper → stdio MCP Server
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    print("ERROR: Missing dependencies. Install with:")
    print("  pip install fastapi uvicorn")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP HTTP Bridge", version="1.0.0")

# Enable CORS for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MCPServerProcess:
    """Manages a subprocess running an MCP server"""

    def __init__(self, command: str, args: list[str], cwd: str, env: dict[str, str]):
        self.command = command
        self.args = args
        self.cwd = cwd
        self.env = env
        self.process: Optional[asyncio.subprocess.Process] = None

    async def start(self):
        """Start the MCP server subprocess"""
        logger.info(f"Starting MCP server: {self.command} {' '.join(self.args)}")

        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.cwd,
            env=self.env
        )
        logger.info(f"MCP server started with PID: {self.process.pid}")

    async def send_request(self, request_data: dict) -> dict:
        """Send a JSON-RPC request to the MCP server and get response"""
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP server not started")

        # Send request
        request_json = json.dumps(request_data) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()

        # Read response
        response_line = await self.process.stdout.readline()
        response_data = json.loads(response_line.decode())

        return response_data

    async def stop(self):
        """Stop the MCP server subprocess"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            logger.info("MCP server stopped")


# Global MCP server instances
mcp_servers = {}


def load_mcp_config() -> dict:
    """Load MCP configuration from .claude/mcp.json and adapt paths for current system"""
    config_paths = [
        Path(__file__).parent / ".claude" / "mcp.json",
        Path(__file__).parent / ".mcp.json",
        Path.home() / ".claude.json"
    ]

    for config_path in config_paths:
        if config_path.exists():
            logger.info(f"Loading MCP config from: {config_path}")
            with open(config_path) as f:
                config = json.load(f)

            # Adapt paths from Linux to current system (Mac)
            adapted_servers = {}
            for server_name, server_config in config.get("mcpServers", {}).items():
                adapted_config = server_config.copy()

                # Replace /home/user/ with user's home directory
                if "cwd" in adapted_config:
                    adapted_config["cwd"] = adapted_config["cwd"].replace(
                        "/home/user/", str(Path.home()) + "/"
                    )

                if "env" in adapted_config:
                    for key, value in adapted_config["env"].items():
                        if isinstance(value, str) and "/home/user/" in value:
                            adapted_config["env"][key] = value.replace(
                                "/home/user/", str(Path.home()) + "/"
                            )

                # Replace args paths
                if "args" in adapted_config:
                    adapted_config["args"] = [
                        arg.replace("/home/user/", str(Path.home()) + "/")
                        for arg in adapted_config["args"]
                    ]

                adapted_servers[server_name] = adapted_config

            return adapted_servers

    logger.warning("No MCP config file found, using defaults")
    return {}


async def get_or_create_server(server_name: str) -> MCPServerProcess:
    """Get or create an MCP server instance"""
    if server_name in mcp_servers:
        return mcp_servers[server_name]

    # Load configuration from file
    configs = load_mcp_config()

    if server_name not in configs:
        raise ValueError(f"Unknown server: {server_name}. Available: {list(configs.keys())}")

    config = configs[server_name]

    # Add default env dict if not present
    if "env" not in config:
        config["env"] = {}

    server = MCPServerProcess(**config)
    await server.start()
    mcp_servers[server_name] = server

    return server


@app.post("/mcp/{server_name}/message")
async def mcp_message(server_name: str, request: Request):
    """
    Handle MCP JSON-RPC messages via HTTP POST

    This endpoint receives JSON-RPC requests and forwards them to the
    appropriate MCP server via stdio.
    """
    try:
        request_data = await request.json()
        logger.info(f"Received request for {server_name}: {request_data.get('method', 'unknown')}")

        server = await get_or_create_server(server_name)
        response_data = await server.send_request(request_data)

        return response_data

    except Exception as e:
        logger.error(f"Error handling request: {e}", exc_info=True)
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            },
            "id": request_data.get("id") if "request_data" in locals() else None
        }


@app.get("/mcp/{server_name}/sse")
async def mcp_sse(server_name: str):
    """
    Server-Sent Events endpoint for streaming MCP messages

    This allows the MCP protocol's streaming capabilities to work over HTTP.
    """
    async def event_generator():
        try:
            server = await get_or_create_server(server_name)

            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'server': server_name})}\n\n"

            # Keep connection alive (simplified - real implementation would handle streaming)
            while True:
                await asyncio.sleep(1)
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        except asyncio.CancelledError:
            logger.info(f"SSE connection closed for {server_name}")
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}", exc_info=True)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "running_servers": list(mcp_servers.keys())
    }


@app.get("/servers")
async def list_servers():
    """List all available MCP servers from config"""
    configs = load_mcp_config()
    return {
        "available_servers": list(configs.keys()),
        "running_servers": list(mcp_servers.keys()),
        "configs": {
            name: {
                "command": config["command"],
                "cwd": config.get("cwd", ""),
                "args_count": len(config.get("args", []))
            }
            for name, config in configs.items()
        }
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up MCP servers on shutdown"""
    logger.info("Shutting down MCP servers...")
    for server in mcp_servers.values():
        await server.stop()


def main():
    """Run the HTTP MCP bridge server"""
    import argparse

    parser = argparse.ArgumentParser(description="HTTP MCP Server Bridge")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting HTTP MCP Bridge on {args.host}:{args.port}")
    logger.info("Expose this server via ngrok: ngrok http " + str(args.port))

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info" if not args.debug else "debug"
    )


if __name__ == "__main__":
    main()
