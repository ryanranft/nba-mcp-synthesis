# PyCharm AI Playground Integration

This guide shows how to connect your AI Playground session in PyCharm to your MCP adapter and auto-include a Data Inventory summary in every prompt.

Prerequisites
- Python environment ready.
- MCP server or adapter reachable locally (default adapter URL: http://localhost:5055).
- Optional: Data Inventory report generated (or enabled in your project config).

Start the adapter
- Run (in the project root):
  - python scripts/run_playground_adapter.py
- Adapter default: http://localhost:5055
- Quick checks:
  - Health: curl -s http://localhost:5055/health | jq .
  - Tools: curl -s http://localhost:5055/mcp/tools | jq .
  - Inventory: curl -s http://localhost:5055/inventory/summary | jq .

Create a Playground session (PyCharm)
1) Open Tools → AI Assistant → New Playground (or open the AI panel and click “New Playground”).
2) Choose your model(s) in “Playground Settings”.
3) Paste this System Prompt (kept short, grounded, re-usable):

System Prompt (paste into the “System prompt” field)
Use the provided context sections and the Data Inventory Summary when present. Always ground answers in concrete tables, columns, and systems. If you reference data, prefer exact table/column names and explain assumptions briefly.

Recommended settings
- Max tokens: 2000–4000
- Temperature: 0.3 (deterministic data/SQL work)
- Top-p: default

Fetch context from MCP (two options)

Option A — One-click via curl from Terminal
- For SQL/code tasks, run:
  - curl -s -X POST http://localhost:5055/context/gather \
    -H "Content-Type: application/json" \
    -d '{"query_type":"sql_optimization","user_input":"<your current question or SQL>","include_inventory":true}' \
    | jq -r '.inventory_summary, .schemas, .table_stats, .explain_plan, .related_files' > .ai/_playground_context.md
- In the Playground, click “Attach File” (paperclip) and select .ai/_playground_context.md (or copy-paste sections you need).

Option B — HTTP Request scratch file
- Create a new HTTP Request scratch in PyCharm (Cmd/Ctrl+Shift+A → “HTTP Request”).
- Add:
  - GET http://localhost:5055/inventory/summary
  - POST http://localhost:5055/context/gather
    Content-Type: application/json

    {
      "query_type": "general_analysis",
      "user_input": "{{your_prompt_here}}",
      "include_inventory": true
    }
- Run requests; copy only the sections you want into the Playground (Inventory summary first, then schemas/stats/explain plan).

Playground workflow (recommended)
1) Toggle “Data Inventory” concept ON (by including the inventory summary first).
2) Add relevant sections (schemas, stats, explain plan) under your prompt.
3) Ask your question. The System Prompt ensures answers use the included context.

MCP tool calls from the Playground (optional)
- Open a terminal tab in PyCharm and call:
  - curl -s -X POST http://localhost:5055/mcp/call \
    -H "Content-Type: application/json" \
    -d '{"name":"get_table_schema","arguments":{"table_name":"master_player_game_stats"}}' | jq .
- Copy results you want into your Playground context.

Saving sessions as “experiments” (if supported by your adapter)
- POST http://localhost:5055/playground/session/experiment
- Body:
  {
    "session_id": "<some-id-you-use-in-your notes>",
    "experiment_name": "My Analysis",
    "description": "What I tested"
  }

Troubleshooting
- Adapter down: /health returns mcp.up=false → start/restart adapter.
- No inventory summary: verify /inventory/summary returns enabled=true; if not, enable inventory in project config or generate a fresh report, then retry.
- Slow responses: lower the number of sections you paste; keep Inventory + only the schemas/stats you need.

Verification checklist (2 minutes)
- curl /health shows ok and mcp.up true (or tools_count present).
- In Playground, run a simple SQL optimization prompt and confirm the answer references concrete tables/columns from the attached context.
