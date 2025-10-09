# NBA MCP Synthesis - Jupyter Notebooks

Interactive notebooks for exploring and demonstrating the NBA MCP Synthesis System.

## Available Notebooks

### 1. Data Exploration (`01_data_exploration.ipynb`)
- Connect to MCP server
- List and explore database tables
- Query NBA data
- Visualize statistics
- Access S3 files

### 2. Synthesis Workflow (`02_synthesis_workflow.ipynb`)
- SQL query optimization examples
- Statistical analysis demonstrations
- ETL code generation
- Cost analysis and tracking

## Getting Started

### Prerequisites

```bash
# Install Jupyter
pip install jupyter notebook ipykernel

# Install visualization libraries
pip install matplotlib seaborn pandas

# Make sure MCP server is running
./scripts/start_mcp_server.sh
```

### Running Notebooks

```bash
# Start Jupyter from project root
cd /Users/ryanranft/nba-mcp-synthesis
jupyter notebook notebooks/
```

Or use JupyterLab:

```bash
pip install jupyterlab
jupyter lab notebooks/
```

### Configuration

Make sure your `.env` file is properly configured with:
- Database credentials (`RDS_*`)
- AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- API keys (`DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`)
- MCP server URL (usually `http://localhost:3000`)

## Notebook Organization

Each notebook is designed to:
1. Load environment variables from `.env`
2. Connect to MCP server
3. Demonstrate specific functionality
4. Clean up connections when done

## Tips

### Running Async Code in Jupyter

All MCP operations are asynchronous. Jupyter notebooks support `await` directly in cells.

### Saving Results

Synthesis results are automatically saved to `synthesis_output/` directory with timestamps.

### Cost Tracking

Each synthesis operation tracks:
- Tokens used per model
- Cost per model
- Total execution time

Monitor costs in the notebook output or check the saved JSON files.

## Troubleshooting

### "MCP server not connected"
- Make sure the MCP server is running: `./scripts/start_mcp_server.sh`
- Check server logs: `tail -f logs/mcp_server.log`

### "Module not found"
- Make sure you're running from the project root
- Reinstall dependencies: `pip install -r requirements.txt`

### "Database connection error"
- Check `.env` has correct RDS credentials
- Verify database is accessible from your network

## Next Steps

After exploring these notebooks:
1. Try the Streamlit dashboard for a web interface
2. Check `synthesis_output/` for saved results
3. Review the full documentation in `DEPLOYMENT.md`

## Contributing

To add new notebooks:
1. Follow the naming convention: `##_description.ipynb`
2. Include markdown cells with explanations
3. Add entry to this README
4. Test the notebook before committing
