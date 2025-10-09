# PyCharm NBA MCP Integration

Complete PyCharm IDE integration for NBA MCP Synthesis System. This enables automated workflows, web scraper generation, SQL query creation, and code analysis directly from your IDE.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Available Tools](#available-tools)
6. [Command Line Scripts](#command-line-scripts)
7. [Keyboard Shortcuts](#keyboard-shortcuts)
8. [Examples](#examples)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install the Tools in PyCharm

**Option A: Import XML (Fastest)**

1. Open PyCharm
2. Go to `Settings/Preferences` → `Tools` → `External Tools`
3. Click the gear icon → `Import`
4. Select: `/Users/ryanranft/nba-mcp-synthesis/pycharm/NBA_MCP_Tools.xml`
5. Click `OK`

**Option B: Manual Setup**

See [Manual Installation](#manual-installation) section below.

### 2. Verify Installation

1. Right-click in any Python file
2. Look for `External Tools` → `MCP:` menu items
3. You should see:
   - MCP: Analyze Code
   - MCP: Generate Scraper
   - MCP: Generate SQL Query
   - MCP: Execute Query with Explanation
   - And more...

### 3. Test It Out

Select some code, right-click → `External Tools` → `MCP: Explain Code`

---

## Features

### ✅ What This Integration Gives You

1. **Automated Web Scraper Generation**
   - Provide a URL and description
   - AI generates complete production-ready scraper
   - Includes error handling, pagination, rate limiting, database integration

2. **Natural Language to SQL**
   - Describe what you want in plain English
   - Get optimized SQL query with explanations
   - Includes performance tips and index recommendations

3. **Code Analysis**
   - Analyze selected code for bugs, performance issues, improvements
   - Get detailed explanations of complex code
   - Debug errors with AI assistance

4. **Database Query Execution**
   - Run SQL queries with natural language explanations
   - Get insights and recommendations
   - Automatic data quality notes

5. **Ollama-Primary Workflow**
   - Uses local Ollama model first (FREE, unlimited)
   - Falls back to Claude only when needed
   - **No more rate limits!**

---

## Installation

### Prerequisites

```bash
# Ensure you have:
# 1. PyCharm (Community or Professional)
# 2. Ollama installed and running
# 3. Python environment with dependencies

# Check Ollama
ollama list | grep qwen2.5-coder:32b

# If not installed:
ollama pull qwen2.5-coder:32b
```

### Step 1: Import External Tools

1. Open PyCharm
2. `File` → `Settings` (or `PyCharm` → `Preferences` on Mac)
3. Navigate to: `Tools` → `External Tools`
4. Click the gear icon → `Import`
5. Select: `/Users/ryanranft/nba-mcp-synthesis/pycharm/NBA_MCP_Tools.xml`
6. Click `OK` to confirm

### Step 2: Verify Environment

```bash
# From PyCharm terminal:
cd /Users/ryanranft/nba-mcp-synthesis
python3 pycharm/mcp_external_tool.py sql --request "Test query"
```

If you see a SQL query generated, you're all set!

### Step 3: Configure Keyboard Shortcuts (Optional)

1. `Settings` → `Keymap`
2. Search for "External Tools"
3. Expand to find "MCP:" tools
4. Right-click → `Add Keyboard Shortcut`
5. Recommended shortcuts:
   - `MCP: Improve Selected Code`: `Cmd+Shift+I` (Mac) / `Ctrl+Shift+I` (Win)
   - `MCP: Explain Code`: `Cmd+Shift+E` (Mac) / `Ctrl+Shift+E` (Win)
   - `MCP: Generate SQL Query`: `Cmd+Shift+Q` (Mac) / `Ctrl+Shift+Q` (Win)

---

## Usage

### From PyCharm Editor

**1. Analyze Selected Code**

```python
# Select this code:
def calculate_average(stats):
    total = sum([game['points'] for game in stats])
    return total / len(stats)  # Bug: ZeroDivisionError
```

- Right-click → `External Tools` → `MCP: Debug Error`
- AI will identify the bug and suggest a fix

**2. Generate Web Scraper**

- `Tools` → `External Tools` → `MCP: Generate Web Scraper (Custom)`
- Enter URL: `https://www.nba.com/stats/players`
- Enter description: `Extract player statistics`
- Get complete scraper code instantly

**3. Generate SQL Query**

- `Tools` → `External Tools` → `MCP: Generate SQL Query`
- Enter: `Find top 10 scorers in 2023-24 season`
- Get optimized query with explanations

**4. Execute and Explain Query**

```sql
-- Select this SQL:
SELECT * FROM players WHERE team_id = 1
```

- Right-click → `External Tools` → `MCP: Execute Query with Explanation`
- Get results + AI insights

---

## Available Tools

### 1. MCP: Analyze Code
**Shortcut:** (Configure in Keymap)
**Usage:** Select code → Right-click → MCP: Analyze Code
**Prompt:** Enter your analysis request

**Examples:**
- "Find performance bottlenecks"
- "Check for security issues"
- "Suggest refactoring"

---

### 2. MCP: Generate Scraper
**Usage:** Select existing scraper (optional) → MCP: Generate Scraper
**Prompt:** Enter target URL

**What it does:**
- Generates complete web scraper
- Includes error handling
- Adds pagination logic
- Implements rate limiting
- Saves to database if NBA data

---

### 3. MCP: Generate SQL Query
**Usage:** Tools → External Tools → MCP: Generate SQL Query
**Prompt:** Describe what you want

**Examples:**
- "Top 10 players by points per game"
- "Teams with most wins in playoff games"
- "Player statistics for specific season"

---

### 4. MCP: Execute Query with Explanation
**Usage:** Select SQL query → MCP: Execute Query
**No prompt needed**

**What it does:**
- Runs query against database
- Provides row count
- Explains results in plain English
- Suggests optimizations

---

### 5. MCP: Improve Selected Code
**Usage:** Select code → MCP: Improve Selected Code
**No prompt needed**

**Automatically checks:**
- Performance issues
- Code clarity
- Best practices
- Potential refactoring

---

### 6. MCP: Debug Error
**Usage:** Select error or problematic code → MCP: Debug Error
**No prompt needed**

**What it does:**
- Identifies root cause
- Provides fix
- Explains the issue

---

### 7. MCP: Explain Code
**Usage:** Select code → MCP: Explain Code
**No prompt needed**

**What it does:**
- Detailed explanation of functionality
- Line-by-line breakdown for complex code
- Clarifies intent

---

## Command Line Scripts

For automation outside PyCharm:

### Generate Web Scraper

```bash
cd /Users/ryanranft/nba-mcp-synthesis

./pycharm/scripts/quick_scraper.sh \
    "https://www.nba.com/stats/players" \
    "Extract player statistics"
```

### Generate SQL Query

```bash
./pycharm/scripts/quick_sql.sh \
    "Find top 10 scorers in 2023-24 season"
```

### Analyze File

```bash
./pycharm/scripts/analyze_file.sh \
    my_script.py \
    "Find performance issues"
```

---

## Keyboard Shortcuts

### Recommended Shortcuts

| Action | macOS | Windows/Linux |
|--------|-------|---------------|
| Improve Code | `Cmd+Shift+I` | `Ctrl+Shift+I` |
| Explain Code | `Cmd+Shift+E` | `Ctrl+Shift+E` |
| Debug Error | `Cmd+Shift+D` | `Ctrl+Shift+D` |
| Generate SQL | `Cmd+Shift+Q` | `Ctrl+Shift+Q` |

### How to Set Up

1. `Settings/Preferences` → `Keymap`
2. Search: "External Tools"
3. Expand to find MCP tools
4. Right-click tool → `Add Keyboard Shortcut`
5. Press your desired key combination

---

## Examples

### Example 1: Generate NBA Stats Scraper

**Goal:** Scrape player stats from NBA website

**Steps:**
1. `Tools` → `External Tools` → `MCP: Generate Web Scraper (Custom)`
2. URL: `https://www.nba.com/stats/players`
3. Description: `Extract points, rebounds, assists, and store in database`

**Result:** Complete production-ready scraper with:
- BeautifulSoup parsing
- Database integration (SQLite)
- Error handling and retries
- Rate limiting (respects robots.txt)
- Pagination handling
- Data validation

**Cost:** $0 (uses Ollama)

---

### Example 2: Optimize Slow Query

**Scenario:** You have a slow query

```sql
SELECT p.name, SUM(s.points) as total_points
FROM players p
JOIN player_game_stats s ON p.player_id = s.player_id
WHERE s.season = '2023-24'
GROUP BY p.name
ORDER BY total_points DESC
```

**Steps:**
1. Select the query
2. Right-click → `External Tools` → `MCP: Analyze Code`
3. Enter: "Optimize this query for performance"

**Result:** AI provides:
- Optimized query
- Index recommendations
- Performance comparison
- Execution plan analysis

**Cost:** $0 (uses Ollama)

---

### Example 3: Debug Complex Error

**Scenario:** Code failing with unclear error

```python
def process_game_data(games):
    results = []
    for game in games:
        stats = game['box_score']['team_stats']
        team_total = sum([stat['value'] for stat in stats if stat['type'] == 'points'])
        results.append(team_total)
    return results

# Error: KeyError: 'box_score'
```

**Steps:**
1. Select the code
2. Right-click → `External Tools` → `MCP: Debug Error`

**Result:** AI identifies:
- Root cause: Missing 'box_score' key in some game objects
- Fix: Add defensive checks
- Improved code with error handling

**Cost:** $0 (uses Ollama)

---

### Example 4: Automated Web Scraping Workflow

**Goal:** Fully automate daily NBA stats collection

**PyCharm Setup:**
1. Generate scraper using MCP tool
2. Save to `scrapers/nba_daily_stats.py`
3. Add to PyCharm Run Configuration
4. Schedule with PyCharm's "Run on Schedule" or cron

**Complete Workflow:**

```bash
# 1. Generate scraper
./pycharm/scripts/quick_scraper.sh \
    "https://www.nba.com/stats/teams/traditional" \
    "Extract team statistics and save to database"

# 2. Save to file
# (MCP tool does this automatically with --output flag)

# 3. Schedule in cron
# crontab -e
# 0 1 * * * cd /path/to/project && python3 scrapers/nba_daily_stats.py

# 4. Verify in PyCharm
# Right-click scraper file → Run
```

**Benefits:**
- No manual scraping
- AI handles edge cases
- Automatic error recovery
- Database integration included

---

## Troubleshooting

### Issue: "Ollama not available"

**Cause:** Ollama service not running

**Fix:**
```bash
# Start Ollama
ollama serve

# In another terminal, verify:
ollama list
```

---

### Issue: "Module not found: mcp_client"

**Cause:** Running from wrong directory

**Fix:**
```bash
# Always run from project root:
cd /Users/ryanranft/nba-mcp-synthesis
python3 pycharm/mcp_external_tool.py ...
```

---

### Issue: "ANTHROPIC_API_KEY not set"

**Cause:** Environment variables not loaded

**Fix:**
```bash
# Check .env file exists
ls -la /Users/ryanranft/nba-mcp-synthesis/.env

# If missing, create it:
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
echo "DEEPSEEK_API_KEY=your_key_here" >> .env
```

---

### Issue: "External Tools menu is empty"

**Cause:** XML not imported correctly

**Fix:**
1. `Settings` → `Tools` → `External Tools`
2. Check if tools are listed
3. If not, re-import `NBA_MCP_Tools.xml`
4. Restart PyCharm

---

### Issue: "Rate limit exceeded"

**Solution:** You're using the wrong workflow!

```bash
# Switch to Ollama-primary workflow:
python3 pycharm/mcp_external_tool.py scraper \
    --url "..." \
    --description "..." \
    # No --no-ollama flag
```

Ollama is **unlimited** and **free**!

---

## Manual Installation

If XML import doesn't work, add tools manually:

### MCP: Generate SQL Query

1. `Settings` → `Tools` → `External Tools` → `+` (Add)
2. Fill in:
   - **Name:** MCP: Generate SQL Query
   - **Program:** `$PyInterpreterDirectory$/python3`
   - **Arguments:** `$ProjectFileDir$/pycharm/mcp_external_tool.py sql --request "$Prompt$"`
   - **Working directory:** `$ProjectFileDir$`
3. Check: "Synchronize files after execution"
4. Click `OK`

Repeat for other tools (refer to `NBA_MCP_Tools.xml` for parameters).

---

## Architecture

### How It Works

```
PyCharm Editor
    ↓ (User selects code + triggers tool)
mcp_external_tool.py
    ↓ (Reads selected text)
OllamaModel (LOCAL, FREE)
    ↓ (Generates initial solution)
ClaudeModel (OPTIONAL, verify only)
    ↓ (Synthesizes final result)
PyCharm Console (Display result)
```

### Why Ollama-Primary?

**OLD Workflow:**
```
DeepSeek (API, 30 RPM) → Claude (API, 50 RPM)
❌ Rate limits
❌ Costs money
```

**NEW Workflow:**
```
Ollama (LOCAL, ∞ RPM) → Claude (optional verification)
✅ No rate limits
✅ 85-100% cost savings
✅ Faster
```

---

## Cost Analysis

| Operation | Old (DeepSeek+Claude) | New (Ollama+Claude) | Savings |
|-----------|-----------------------|---------------------|---------|
| Simple query | $0.013 | $0.002 | 85% |
| Scraper generation | $0.013 | $0.000 | 100% |
| Code analysis | $0.013 | $0.000 | 100% |
| SQL query | $0.005 | $0.000 | 100% |

**Daily usage estimate:**
- 20 queries/day × $0.013 = **$0.26/day** (old)
- 20 queries/day × $0.000 = **$0.00/day** (new)

**Monthly savings:** ~$7.80

---

## Configuration

### Environment Variables

Required in `.env`:
```bash
# Required for Claude verification (optional)
ANTHROPIC_API_KEY=sk-ant-...

# Required for DeepSeek fallback (optional)
DEEPSEEK_API_KEY=sk-...

# Optional - Ollama configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:32b
```

### Ollama Models

Recommended models:
- **qwen2.5-coder:32b** (19GB) - Best for code generation
- **qwen2.5-coder:14b** (9GB) - Faster, good quality
- **codellama:34b** (20GB) - Alternative

```bash
# Install recommended model
ollama pull qwen2.5-coder:32b

# Or lighter version
ollama pull qwen2.5-coder:14b
```

---

## Advanced Usage

### Custom Prompts

Edit tool parameters in PyCharm:

1. `Settings` → `Tools` → `External Tools`
2. Select a tool → Click pencil (Edit)
3. Modify `Arguments` parameter
4. Save

**Example:** Add custom instructions

```bash
# Original
$ProjectFileDir$/pycharm/mcp_external_tool.py analyze --code "$SelectedText$" --request "$Prompt$"

# Custom (always check security)
$ProjectFileDir$/pycharm/mcp_external_tool.py analyze --code "$SelectedText$" --request "Check for security vulnerabilities: $Prompt$"
```

### Batch Processing

Process multiple files:

```bash
# Analyze all Python files in directory
for file in scrapers/*.py; do
    ./pycharm/scripts/analyze_file.sh "$file" "Check for bugs"
done
```

### Integration with CI/CD

```yaml
# .github/workflows/analyze.yml
name: AI Code Review
on: [push]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Analyze changed files
        run: |
          for file in $(git diff --name-only HEAD~1); do
            python3 pycharm/mcp_external_tool.py analyze \
              --file "$file" \
              --request "Review for issues"
          done
```

---

## FAQ

### Q: Do I need Ollama?

**A:** Not required, but highly recommended:
- **With Ollama:** Unlimited queries, $0 cost, no rate limits
- **Without Ollama:** Falls back to DeepSeek+Claude, has rate limits, costs money

### Q: Can I use this without PyCharm?

**A:** Yes! Use command-line scripts:
```bash
./pycharm/scripts/quick_scraper.sh <url> <description>
./pycharm/scripts/quick_sql.sh <query>
./pycharm/scripts/analyze_file.sh <file> <request>
```

### Q: Does this work with other IDEs?

**A:** Conceptually yes, but requires setup:
- **VS Code:** Create tasks in `.vscode/tasks.json`
- **Sublime:** Create build systems
- **Vim:** Add custom commands

The core `mcp_external_tool.py` works anywhere.

### Q: What if Ollama is slow?

**A:** Try smaller model:
```bash
ollama pull qwen2.5-coder:14b  # 9GB instead of 19GB
```

Or disable Ollama for specific tasks:
```bash
python3 pycharm/mcp_external_tool.py sql --request "..." --no-ollama
```

### Q: Can I add custom tools?

**A:** Absolutely! Edit `mcp_external_tool.py`:

```python
async def my_custom_analysis(self, code: str) -> Dict[str, Any]:
    """Your custom analysis"""
    prompt = f"Do custom analysis: {code}"
    result = await self.ollama.query(prompt=prompt)
    return result
```

Then add to `main()` function with new action.

---

## Support

**Documentation:**
- Project root: `/Users/ryanranft/nba-mcp-synthesis/`
- This file: `/Users/ryanranft/nba-mcp-synthesis/pycharm/README.md`
- Setup summary: `/Users/ryanranft/nba-mcp-synthesis/SETUP_COMPLETE_SUMMARY.md`

**Testing:**
```bash
# Test tool directly
python3 pycharm/mcp_external_tool.py sql --request "test"

# Check Ollama
ollama list

# Check environment
python3 -c "from synthesis.models import OllamaModel; print(OllamaModel().is_available())"
```

---

## What's Next?

After setting up PyCharm integration, you can:

1. **Start building scrapers** for your NBA data collection
2. **Query your database** using natural language
3. **Automate ETL workflows** with AI-generated code
4. **Continue NBA simulator project** with AI assistance

All without rate limits or excessive API costs!

---

**Ready to automate your NBA project? 🏀**
