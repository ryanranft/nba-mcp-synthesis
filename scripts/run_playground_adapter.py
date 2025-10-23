from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable when running this script directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from playground_adapter.app import create_app
from playground_adapter.config import get_config

if __name__ == "__main__":
    cfg = get_config()
    app = create_app()
    app.run(host=cfg.host, port=cfg.port)
