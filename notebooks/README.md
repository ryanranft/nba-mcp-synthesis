# NBA MCP Synthesis - Jupyter Notebooks

This directory contains Jupyter notebooks for interactive NBA data analysis and experimentation.

---

## Overview

Jupyter notebooks provide an interactive environment for:
- Exploratory data analysis (EDA)
- Prototyping new features
- Testing data transformations
- Visualizing NBA statistics
- Running experiments

---

## Available Notebooks

### Data Analysis
- **`01_player_stats_analysis.ipynb`**: Player performance analysis
- **`02_team_performance_trends.ipynb`**: Team statistics over seasons
- **`03_game_predictions.ipynb`**: ML models for game outcome prediction

### Feature Engineering
- **`04_advanced_metrics.ipynb`**: Calculate PER, TS%, USG%, etc.
- **`05_player_similarity.ipynb`**: Find similar players using embeddings
- **`06_lineup_optimization.ipynb`**: Optimize starting lineups

### Experimentation
- **`07_model_training.ipynb`**: Train ML models on NBA data
- **`08_hyperparameter_tuning.ipynb`**: Optimize model parameters
- **`09_feature_importance.ipynb`**: Analyze feature contributions

### Visualization
- **`10_interactive_dashboards.ipynb`**: Create Plotly dashboards
- **`11_shot_charts.ipynb`**: Visualize shooting patterns
- **`12_player_comparison.ipynb`**: Compare multiple players

---

## Setup

### Install Jupyter
```bash
pip install jupyter notebook jupyterlab
```

### Start Jupyter Lab
```bash
jupyter lab
```

### Start Jupyter Notebook
```bash
jupyter notebook
```

---

## Environment Setup

All notebooks assume the following environment:

```python
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
sys.path.append(os.path.dirname(os.getcwd()))

# Import MCP modules
from mcp_server.tools import *
from data_quality.validator import DataValidator
```

---

## Data Sources

Notebooks can access:
- **PostgreSQL Database**: NBA historical stats
- **S3 Bucket**: Raw data files
- **MCP Server**: Real-time data queries
- **Local Cache**: Preprocessed datasets

---

## Best Practices

### Code Quality
- Use meaningful variable names
- Add markdown cells for explanations
- Keep cells focused on single tasks
- Document assumptions and limitations

### Performance
- Sample large datasets for exploration
- Cache expensive computations
- Use vectorized operations
- Profile slow cells

### Reproducibility
- Set random seeds: `np.random.seed(42)`
- Document package versions
- Save intermediate results
- Version control notebooks (use nbstripout)

---

## Common Workflows

### 1. Load NBA Player Stats
```python
from mcp_server.basketball_reference import BasketballReferenceConnector

br = BasketballReferenceConnector()
player_stats = await br.get_player_stats("LeBron James", "2023-24")
df = pd.DataFrame([player_stats])
```

### 2. Calculate Advanced Metrics
```python
from mcp_server.tools.algebra_helper import get_sports_formula

per = get_sports_formula("per", **player_stats)
true_shooting = get_sports_formula("true_shooting", **player_stats)
```

### 3. Validate Data Quality
```python
from data_quality.validator import DataValidator

validator = DataValidator(use_configured_context=False)
result = await validator.validate_table("players", data=df)
```

### 4. Create Visualizations
```python
import plotly.express as px

fig = px.scatter(df, x="FGA", y="PTS", size="MP", color="TEAM")
fig.show()
```

---

## Exporting Notebooks

### Export to Python Script
```bash
jupyter nbconvert --to script notebook.ipynb
```

### Export to HTML
```bash
jupyter nbconvert --to html notebook.ipynb
```

### Export to PDF
```bash
jupyter nbconvert --to pdf notebook.ipynb
```

---

## Troubleshooting

### Kernel Issues
```bash
# Restart kernel: Kernel → Restart
# Clear outputs: Cell → All Output → Clear
```

### Import Errors
```bash
# Verify project root in path
import sys
print(sys.path)

# Reinstall packages
pip install --upgrade -r requirements.txt
```

### Memory Issues
```python
# Monitor memory usage
import psutil
print(f"Memory: {psutil.virtual_memory().percent}%")

# Clear large variables
del large_dataframe
import gc; gc.collect()
```

---

## Contributing

When adding new notebooks:
1. Follow naming convention: `##_descriptive_name.ipynb`
2. Add summary to this README
3. Include clear markdown explanations
4. Test all cells execute without errors
5. Strip outputs before committing: `nbstripout notebook.ipynb`

---

## Resources

### Learning
- [Jupyter Documentation](https://jupyter.org/documentation)
- [Pandas User Guide](https://pandas.pydata.org/docs/user_guide/)
- [NBA Stats API](https://github.com/swar/nba_api)

### Extensions
- **nbextensions**: Useful notebook extensions
- **jupyterlab-git**: Git integration
- **jupyterlab-lsp**: Language server protocol
- **nbdime**: Notebook diff/merge tools

---

## Contact

For questions or issues with notebooks:
- Open an issue on GitHub
- Ask in #nba-mcp-notebooks Slack channel
- Email: nba-mcp-support@example.com

---

**Last Updated**: October 23, 2025
