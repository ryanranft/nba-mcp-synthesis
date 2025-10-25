# Streamlit Integration

## Overview
Streamlit connector provides interactive data visualization and dashboard capabilities for NBA analytics.

## Configuration

### Environment Variables
```bash
STREAMLIT_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
```

## Usage

### Starting Streamlit Dashboard
```python
import streamlit as st
from mcp_server.streamlit_connector import StreamlitDashboard

dashboard = StreamlitDashboard()
dashboard.run()
```

### Example Dashboard
```python
st.title("NBA Player Analytics")
st.metric("Average PPG", "25.3")
st.line_chart(player_stats_df)
```

## Testing
Run tests with:
```bash
pytest tests/test_streamlit_connector.py
```

## Features
- Real-time data visualization
- Interactive player comparison
- Custom metric dashboards
- NBA game predictions display

## Dependencies
- streamlit>=1.28.0
- plotly>=5.17.0
- pandas>=2.1.0


