# Dashboard Usage Guide

Complete guide to using the NBA MCP Synthesis System real-time monitoring dashboard.

**Dashboard URL:** http://localhost:8080
**Auto-refresh:** Every 2 seconds

---

## Starting the Dashboard

### Method 1: Standalone Mode
```bash
# Start dashboard on default port (8080)
python3 scripts/workflow_monitor.py

# Custom port
python3 scripts/workflow_monitor.py --port 8081

# Debug mode (detailed logs)
python3 scripts/workflow_monitor.py --debug
```

### Method 2: Integrated with Workflow
```bash
# Terminal 1: Start dashboard
python3 scripts/workflow_monitor.py

# Terminal 2: Run workflow (dashboard will auto-update)
python3 scripts/run_full_workflow.py --book "All Books" --parallel
```

### Method 3: Background Mode
```python
from workflow_monitor import WorkflowMonitor

# In your script
monitor = WorkflowMonitor(port=8080, auto_start=True)
# Dashboard starts in background thread
```

---

## Dashboard Sections

### 1. Header
**Status Indicator:**
- 🟢 **Active** - Workflow currently running
- ⚪ **Idle** - No active workflow

**Current Status:**
- Workflow state (Active/Idle)
- Last update timestamp

---

### 2. Workflow Progress

**Displays:**
- **Current Phase:** Which phase is executing (e.g., "Phase 2: Analysis")
- **Books Processed:** Number of books completed / Total books
- **Progress Bar:** Visual representation (0-100%)
- **Elapsed Time:** How long workflow has been running
- **Time Remaining:** Estimated time until completion

**Interpretation:**
- Green progress bar: Normal operation
- Updates every 2 seconds
- Time remaining based on current pace

---

### 3. Cost Tracking

**Displays:**
- **Total Cost:** Current accumulated cost (USD)
- **Budget:** Maximum allowed cost from config
- **Remaining:** Budget minus current cost
- **Budget Bar:** Visual representation of budget usage

**Thresholds:**
- 🟢 Green (0-80%): Within budget
- 🟡 Yellow (80-95%): Approaching limit
- 🔴 Red (95-100%): Near or over budget

**Actions:**
- Budget alerts trigger automatic notifications
- Workflow may pause if limit exceeded

---

### 4. Phase Status

**Displays:**
- Grid of all workflow phases
- Each phase shows:
  - Phase name (e.g., "Phase 2: Analysis")
  - Status (Pending/In Progress/Complete/Failed)
  - Duration (if started)

**Phase Colors:**
- **Blue:** Currently in progress
- **Green:** Successfully completed
- **Red:** Failed (error occurred)
- **Gray:** Pending (not yet started)

**Hover:** Additional details appear on mouseover

---

### 5. API Quotas

**Displays:**
- **Gemini:** Tokens used / Limit (1M/min)
- **Claude:** Tokens used / Limit (20K/min)
- **Status Indicators:**
  - 🟢 < 80% used
  - 🟡 80-95% used
  - 🔴 > 95% used (throttling active)

**Throttling:**
- Automatically pauses requests when quota approached
- Waits for quota reset (60 seconds)
- Prevents rate limit errors

---

### 6. System Health

**Disk Space:**
- Shows free space in GB
- Tracks cache and results directories
- Alerts if < 10 GB free

**Memory:**
- Shows available memory in GB
- Tracks usage percentage
- Alerts if > 90% used

**Cache Size:**
- Current cache directory size
- Helps identify when cleanup needed

**Status Colors:**
- 🟢 Green: Healthy (< 80%)
- 🟡 Yellow: Warning (80-95%)
- 🔴 Red: Critical (> 95%)

---

### 7. Recent Alerts

**Displays:**
- Last 10 system alerts
- Each alert shows:
  - Timestamp
  - Severity level (Info/Warning/Critical)
  - Alert message

**Alert Types:**
- **Info:** Normal operations (e.g., "Phase 2 started")
- **Warning:** Non-critical issues (e.g., "Disk space low")
- **Critical:** Urgent problems (e.g., "API quota exceeded")

**Alert Colors:**
- 🔵 Blue border: Info
- 🟡 Yellow border: Warning
- 🔴 Red border: Critical

---

## API Endpoints

The dashboard provides REST API endpoints for programmatic access:

### GET /api/status
**Returns:** Current workflow status
```json
{
  "timestamp": "2025-10-19T12:00:00Z",
  "workflow_active": true,
  "current_phase": "Phase 2: Analysis",
  "elapsed": "45m 30s",
  "time_remaining": "2h 15m",
  "books": {
    "processed": 10,
    "total": 51,
    "progress": 19.6
  }
}
```

### GET /api/phases
**Returns:** All phase statuses
```json
{
  "phase_2": {
    "status": "in_progress",
    "duration": 2730.5,
    "start_time": "2025-10-19T10:00:00Z"
  },
  "phase_3": {
    "status": "pending",
    "duration": null
  }
}
```

### GET /api/cost
**Returns:** Cost tracking data
```json
{
  "total_cost": 45.67,
  "cost_by_phase": {
    "phase_2": 32.10,
    "phase_3": 13.57
  },
  "budget": 400.00,
  "remaining": 354.33
}
```

### GET /api/system
**Returns:** System resource metrics
```json
{
  "timestamp": "2025-10-19T12:00:00Z",
  "api_quotas": {
    "gemini": {
      "used": 125000,
      "limit": 1000000,
      "usage_percent": 0.125
    },
    "claude": {
      "used": 5000,
      "limit": 20000,
      "usage_percent": 0.25
    }
  },
  "disk": {
    "total_gb": 3721.9,
    "free_gb": 703.3,
    "usage_percent": 0.015,
    "cache_gb": 2.5,
    "results_gb": 1.2
  },
  "memory": {
    "total_gb": 96.0,
    "available_gb": 41.3,
    "usage_percent": 0.57
  },
  "alerts": []
}
```

### POST /api/update
**Updates workflow state (called by workflow scripts)**
```json
{
  "phase": "Phase 2: Analysis",
  "books_processed": 10,
  "total_books": 51,
  "active": true
}
```

---

## Programmatic Usage

### Python Integration
```python
from workflow_monitor import WorkflowMonitor

# Start dashboard in background
monitor = WorkflowMonitor(port=8080, auto_start=True)

# Update workflow state
monitor.update_workflow_state(
    phase="Phase 2: Analysis",
    books_processed=10,
    total_books=51,
    active=True
)

# Get current status
status = monitor.get_status_data()
print(f"Progress: {status['books']['progress']}%")
```

### JavaScript/Fetch
```javascript
// Fetch current status
async function getStatus() {
    const response = await fetch('http://localhost:8080/api/status');
    const data = await response.json();
    console.log(`Progress: ${data.books.progress}%`);
}

// Auto-refresh every 2 seconds
setInterval(getStatus, 2000);
```

### cURL
```bash
# Get status
curl http://localhost:8080/api/status

# Get phases
curl http://localhost:8080/api/phases

# Get cost data
curl http://localhost:8080/api/cost

# Get system metrics
curl http://localhost:8080/api/system
```

---

## Mobile/Responsive Design

The dashboard is fully responsive and works on mobile devices:

**Desktop (> 768px):**
- 2-column grid layout
- All features visible
- Hover effects enabled

**Mobile (< 768px):**
- Single column layout
- Touch-friendly controls
- Optimized for small screens

---

## Troubleshooting

### Dashboard Not Loading

**Problem:** Can't access http://localhost:8080

**Solutions:**
```bash
# 1. Check if dashboard is running
ps aux | grep workflow_monitor

# 2. Check if port is in use
lsof -i :8080

# 3. Try different port
python3 scripts/workflow_monitor.py --port 8081

# 4. Check firewall settings
sudo lsof -i -P -n | grep LISTEN
```

### Data Not Updating

**Problem:** Dashboard shows stale data

**Solutions:**
1. Check browser console for errors (F12)
2. Verify workflow is actually running
3. Check network tab for failed API calls
4. Restart dashboard and browser

### High Memory Usage

**Problem:** Dashboard consuming too much memory

**Solutions:**
```bash
# 1. Reduce refresh frequency (modify dashboard.js)
const REFRESH_INTERVAL = 5000; // 5 seconds instead of 2

# 2. Clear browser cache
# 3. Restart dashboard
```

### CORS Errors

**Problem:** API calls blocked by CORS policy

**Solution:**
```python
# Already enabled in workflow_monitor.py
from flask_cors import CORS
CORS(app)

# If still issues, allow specific origin:
CORS(app, origins=['http://localhost:3000'])
```

---

## Performance Tips

1. **Use Chrome/Firefox:** Best performance and compatibility
2. **Close when not needed:** Frees up port and resources
3. **Monitor network tab:** Check for failed requests
4. **Use API directly:** For automation, skip dashboard UI

---

## Advanced Configuration

### Custom Dashboard Theme
Edit `static/dashboard.css`:
```css
:root {
    --primary-color: #2563eb;  /* Your brand color */
    --bg-color: #0f172a;       /* Dark background */
    --card-bg: #1e293b;        /* Card background */
}
```

### Change Refresh Interval
Edit `static/dashboard.js`:
```javascript
const REFRESH_INTERVAL = 5000; // 5 seconds (default: 2000)
```

### Add Custom Metrics
Edit `scripts/workflow_monitor.py`:
```python
@app.route('/api/custom')
def get_custom():
    return jsonify({
        'your_metric': calculate_metric()
    })
```

---

## Security Considerations

**⚠️ Important:**
- Dashboard has **NO authentication**
- Only bind to localhost (127.0.0.1)
- Do NOT expose to public internet
- Use SSH tunnel for remote access

**Remote Access (Secure):**
```bash
# From remote machine
ssh -L 8080:localhost:8080 user@your-server

# Then access http://localhost:8080 on your local machine
```

---

## Best Practices

1. **Start dashboard first:** Before running workflow
2. **Monitor alerts:** Check regularly for issues
3. **Track costs:** Ensure staying within budget
4. **Use API endpoints:** For automation and scripting
5. **Close when done:** Free up resources

---

## FAQs

**Q: Can multiple users access the dashboard?**
A: Yes, but it's single-writer (only one workflow can update state)

**Q: Does the dashboard persist data?**
A: No, state is lost on restart (by design)

**Q: Can I run multiple dashboards?**
A: Yes, use different ports: `--port 8081`, `--port 8082`

**Q: Is there a production deployment option?**
A: Yes, use Gunicorn for production:
```bash
gunicorn -w 4 -b 0.0.0.0:8080 'workflow_monitor:app'
```

**Q: Can I customize the dashboard?**
A: Yes, edit HTML/CSS/JS files in `templates/` and `static/`

---

**Need Help?**
- Check integration tests: `python3 scripts/test_tier3_integration.py`
- View logs: `tail -f logs/workflow_monitor.log`
- Read main docs: `TIER3_COMPLETE.md`




