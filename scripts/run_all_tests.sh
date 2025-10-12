#!/bin/bash
# Comprehensive Test Suite - CRITICAL 8

set -e

echo "🧪 NBA MCP Comprehensive Test Suite"
echo "=" * 80

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run unit tests
echo ""
echo "🔬 Running unit tests..."
pytest tests/ -v --cov=mcp_server --cov-report=html --cov-report=term

# Run integration tests
echo ""
echo "🔗 Running integration tests..."
RUN_INTEGRATION_TESTS=1 pytest tests/ -v -m integration

# Run security tests
echo ""
echo "🔐 Running security tests..."
pytest tests/ -v -k "auth or validation or security"

# Generate coverage report
echo ""
echo "📊 Test Coverage Report:"
pytest tests/ --cov=mcp_server --cov-report=term-missing

echo ""
echo "=" * 80
echo "✅ All tests complete!"
echo "View HTML report: open htmlcov/index.html"

