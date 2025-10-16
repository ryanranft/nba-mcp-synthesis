#!/bin/bash

echo "🚀 Launching Full Book Analysis + Implementation Workflow"
echo "============================================"

# Load environment variables
source .env.workflow

# Run simplified recursive analysis (reads books + triggers deployment)
python3 scripts/simplified_recursive_analysis.py \
    --config config/books_to_analyze_all_ai_ml.json \
    --output-dir analysis_results

echo "✅ Workflow complete!"

