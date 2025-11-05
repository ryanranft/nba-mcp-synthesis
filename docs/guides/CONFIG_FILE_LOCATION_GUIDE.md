# Config File Location Guide

## 🎯 Quick Answer

**Q: Where should I create the Claude Desktop config file?**

**A**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**NOT in the project folder!** This is a macOS system folder where Claude Desktop looks for its configuration.

---

## 📂 Two Different Locations Explained

### 1. Template File (In Project) ✅ Already Created

```
Location: /Users/ryanranft/nba-mcp-synthesis/claude_desktop_config_TEMPLATE.json
Purpose:  Reference template with placeholder values
Status:   ✅ Created (by Claude Code)
Action:   None needed - this is just for copying
```

**What it contains**:
- Correct Python path
- Correct working directory
- Placeholder database credentials (YOUR_DATABASE_*, etc.)

**This file stays in the project** - it's just a template for reference!

---

### 2. Actual Config File (System Folder) ❌ You Need to Create This

```
Location: ~/Library/Application Support/Claude/claude_desktop_config.json
Full Path: /Users/ryanranft/Library/Application Support/Claude/claude_desktop_config.json
Purpose:  This is where Claude Desktop actually looks for MCP server config
Status:   ❌ Not created yet (you need to create it)
Action:   **YOU MUST CREATE THIS FILE**
```

**This is the file Claude Desktop reads!**

---

## 📊 Visual Diagram

```
Your Computer
├── /Users/ryanranft/
│   │
│   ├── nba-mcp-synthesis/  ← PROJECT FOLDER
│   │   ├── claude_desktop_config_TEMPLATE.json  ← Template (reference only)
│   │   ├── mcp_server/
│   │   ├── tests/
│   │   └── ... (all project files)
│   │
│   └── Library/  ← macOS SYSTEM FOLDER
│       └── Application Support/
│           └── Claude/  ← Claude Desktop config directory
│               └── claude_desktop_config.json  ← ACTUAL CONFIG (you create this)
```

---

## ✅ How to Create the Actual Config File

### Option 1: Using Terminal (Recommended)

```bash
# Step 1: Create the Claude config directory (if it doesn't exist)
mkdir -p ~/Library/Application\ Support/Claude/

# Step 2: Copy the template from project
cp /Users/ryanranft/nba-mcp-synthesis/claude_desktop_config_TEMPLATE.json \
   ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Step 3: Edit the file to add your database credentials
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Alternative editor:
open -e ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Option 2: Using Finder (GUI)

**Step 1**: Open Finder

**Step 2**: Go to Folder
- Press: `Cmd+Shift+G`
- Type: `~/Library/Application Support/`
- Click "Go"

**Step 3**: Navigate to Claude folder
- If `Claude/` folder doesn't exist, create it (right-click → New Folder)
- Open the `Claude/` folder

**Step 4**: Copy template
- Open another Finder window
- Navigate to: `/Users/ryanranft/nba-mcp-synthesis/`
- Copy `claude_desktop_config_TEMPLATE.json`
- Paste into `~/Library/Application Support/Claude/`
- Rename to `claude_desktop_config.json` (remove "_TEMPLATE" part)

**Step 5**: Edit credentials
- Double-click the file (opens in TextEdit)
- Replace placeholders:
  - `YOUR_DATABASE_HOST` → your actual database host
  - `YOUR_DATABASE_NAME` → your actual database name
  - `YOUR_USERNAME` → your actual username
  - `YOUR_PASSWORD` → your actual password
- Save and close

---

## 📝 What to Put in the Config File

Your actual config file should look like this:

```json
{
  "mcpServers": {
    "nba-mcp-server": {
      "command": "/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3",
      "args": ["-m", "mcp_server.server_simple"],
      "cwd": "/Users/ryanranft/nba-mcp-synthesis",
      "env": {
        "RDS_HOST": "localhost",              ← REPLACE with your host
        "RDS_PORT": "5432",                   ← Usually 5432 for PostgreSQL
        "RDS_DATABASE": "nba_stats",          ← REPLACE with your database name
        "RDS_USERNAME": "your_username",      ← REPLACE with your username
        "RDS_PASSWORD": "your_password",      ← REPLACE with your password
        "AWS_REGION": "us-east-1",
        "S3_BUCKET_NAME": "nba-sim-raw-data-lake"
      }
    }
  }
}
```

---

## 🔍 Verify File Location

### Check if file exists:

```bash
# Check if file exists
ls -la ~/Library/Application\ Support/Claude/claude_desktop_config.json

# If file exists, you'll see:
# -rw-r--r--  1 ryanranft  staff  XXX Oct 26 20:XX claude_desktop_config.json

# If file doesn't exist, you'll see:
# ls: /Users/ryanranft/Library/Application Support/Claude/claude_desktop_config.json: No such file or directory
```

### View file contents:

```bash
# View the file
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Should show JSON config with your credentials
```

---

## 🚨 Common Mistakes

### ❌ WRONG: Creating config in project folder

```
/Users/ryanranft/nba-mcp-synthesis/claude_desktop_config.json  ← WRONG!
```

Claude Desktop won't find it here!

### ❌ WRONG: Wrong filename

```
~/Library/Application Support/Claude/claude_desktop_config_TEMPLATE.json  ← WRONG!
```

Must be named exactly `claude_desktop_config.json` (no "_TEMPLATE")

### ❌ WRONG: Wrong directory

```
~/Library/Application Support/claude_desktop_config.json  ← WRONG!
```

Must be inside the `Claude/` subfolder!

### ✅ CORRECT:

```
~/Library/Application Support/Claude/claude_desktop_config.json  ← CORRECT!
```

---

## 📍 Why This Location?

### macOS Application Support Folder

`~/Library/Application Support/` is a standard macOS folder where applications store their configuration files.

**Structure**:
```
~/Library/Application Support/
├── Claude/  ← Claude Desktop config
├── VSCode/  ← VS Code config
├── Slack/   ← Slack config
└── ... (other apps)
```

Each application has its own subfolder. Claude Desktop looks specifically in the `Claude/` subfolder for `claude_desktop_config.json`.

---

## ✅ Verification Checklist

After creating the file, verify:

- [ ] File exists at: `~/Library/Application Support/Claude/claude_desktop_config.json`
- [ ] Filename is exactly: `claude_desktop_config.json` (no "_TEMPLATE")
- [ ] File contains valid JSON (no syntax errors)
- [ ] Database credentials filled in (no "YOUR_*" placeholders)
- [ ] Python path is correct: `/Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3`
- [ ] Working directory is correct: `/Users/ryanranft/nba-mcp-synthesis`
- [ ] Claude Desktop has been restarted after creating file

---

## 🔄 Next Steps

After creating the config file:

1. **Restart Claude Desktop**:
   - Quit completely (Cmd+Q)
   - Relaunch
   - Wait 15 seconds for MCP server to initialize

2. **Test connection** in Claude Desktop:
   ```
   What tools do you have available?
   Do you see any MCP tools?
   ```

3. **Verify access**:
   ```
   Using the MCP, list all available tables.
   ```

4. **Expected result**:
   - Should see 4 MCP tools
   - Should list 40 tables
   - Should be able to query database

---

## 🚨 Troubleshooting

### File not found after creating?

**Check location**:
```bash
find ~/ -name "claude_desktop_config.json" 2>/dev/null
```

Should only show one result in `~/Library/Application Support/Claude/`

### Claude Desktop still doesn't see MCP?

1. **Verify file location** (must be in system folder, not project)
2. **Check JSON syntax** (no trailing commas, proper quotes)
3. **Restart Claude Desktop** completely
4. **Wait 15 seconds** after restart
5. **Check Python path** exists: `ls -la /Users/ryanranft/miniconda3/envs/mcp-synthesis/bin/python3`

### Can't find the Library folder?

The `~/Library/` folder is hidden by default in macOS.

**To access**:
- **Finder**: Press `Cmd+Shift+G` and type `~/Library/`
- **Terminal**: Just use `cd ~/Library/` (it's not hidden in terminal)
- **Show in Finder permanently**:
  ```bash
  chflags nohidden ~/Library/
  ```

---

## 📚 Related Documentation

- **Setup Guide**: `CLAUDE_DESKTOP_MCP_SETUP.md` - Complete setup instructions
- **Quick Reference**: `CLAUDE_DESKTOP_QUICK_REFERENCE.md` - Usage examples
- **Testing**: `CLAUDE_DESKTOP_TESTING.md` - 8-step validation tests
- **Template**: `claude_desktop_config_TEMPLATE.json` - Config template (in project)

---

## 🎯 Summary

**Template File** (in project):
```
✅ /Users/ryanranft/nba-mcp-synthesis/claude_desktop_config_TEMPLATE.json
Purpose: Reference only, already created
```

**Actual Config File** (system folder):
```
❌ ~/Library/Application Support/Claude/claude_desktop_config.json
Purpose: Claude Desktop reads this file
Action:  YOU MUST CREATE THIS
```

**How to Create**:
1. Copy template from project
2. Paste to `~/Library/Application Support/Claude/`
3. Rename to remove "_TEMPLATE"
4. Edit to fill in database credentials
5. Save and restart Claude Desktop

**That's it!** 🚀
