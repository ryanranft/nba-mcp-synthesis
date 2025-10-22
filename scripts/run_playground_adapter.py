from __future__ import annotations

from playground_adapter.app import create_app
from playground_adapter.config import get_config

if __name__ == "__main__":
    cfg = get_config()
    app = create_app()
    app.run(host=cfg.host, port=cfg.port)
