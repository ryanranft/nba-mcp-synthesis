#!/bin/bash

# Fix AWS vCPU Limits and Deploy Ollama

echo "🔧 AWS vCPU Limit Resolution Guide"
echo "===================================="
echo ""

echo "📊 Issue: vCPU limit for g5 instances is 0"
echo ""

# Check current limits
echo "🔍 Checking your current AWS limits..."
echo ""

# Check g5 limits
echo "G5 Instance Limits:"
aws service-quotas get-service-quota \
    --service-code ec2 \
    --quota-code L-DB2E81BA \
    --region us-east-1 2>/dev/null || echo "  Cannot query (expected)"

echo ""

# Check other GPU instance families
echo "Alternative GPU Instance Families:"
echo "  p3 (Tesla V100): Checking..."
aws service-quotas get-service-quota \
    --service-code ec2 \
    --quota-code L-417A185B \
    --region us-east-1 2>/dev/null || echo "  Cannot query"

echo ""

# Try to find what we CAN use
echo "🔍 Finding available instance types..."
echo ""

# Check standard instances
echo "Standard Instance Limits (non-GPU):"
aws service-quotas get-service-quota \
    --service-code ec2 \
    --quota-code L-1216C47A \
    --region us-east-1 \
    --query 'Quota.Value' \
    --output text 2>/dev/null || echo "  Unknown"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "📝 Solutions"
echo "═══════════════════════════════════════════════════════"
echo ""

echo "Option 1: Request Limit Increase (Recommended) ⭐"
echo "  Time: 24-48 hours"
echo "  Steps:"
echo "    1. Open AWS Console: https://console.aws.amazon.com/servicequotas"
echo "    2. Search for 'Running On-Demand G and VT instances'"
echo "    3. Click 'Request quota increase'"
echo "    4. Enter value: 32 (for g5.xlarge)"
echo "    5. Submit request"
echo ""

echo "Option 2: Try Different Region"
echo "  Some regions have higher default limits"
echo "  Try: us-west-2, eu-west-1"
echo ""

echo "Option 3: Use CPU-Only Instance (Temporary)"
echo "  While waiting for limit increase"
echo "  Instance: c6i.4xlarge (16 vCPU, $0.68/hour)"
echo "  Can run 13B-32B models"
echo ""

echo "Option 4: Try P3 Instances"
echo "  If g5 limit is 0, p3 might work"
echo "  Instance: p3.2xlarge ($3.06/hour)"
echo ""

echo "═══════════════════════════════════════════════════════"
echo ""
echo "🚀 Quick Actions:"
echo ""
echo "1. Request limit increase now:"
echo "   open 'https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas/L-DB2E81BA'"
echo ""
echo "2. Try different region:"
echo "   ./deploy_ollama_aws_alt.sh us-west-2"
echo ""
echo "3. Deploy CPU version (temporary):"
echo "   ./deploy_ollama_cpu.sh"
echo ""

# Create AWS console link
cat > request_limit_increase.txt << EOF
AWS Service Quota Increase Request
===================================

Follow these steps:

1. Open this URL:
   https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas/L-DB2E81BA

2. Click "Request quota increase"

3. Fill in:
   - Quota name: Running On-Demand G and VT instances
   - Current quota: 0 vCPUs
   - Desired quota: 32 vCPUs (for g5.xlarge)
   - Reason: "Running Ollama AI models for NBA data analysis"

4. Submit request

Expected approval time: 24-48 hours

You'll receive an email when approved.

Alternative while waiting:
- Use local Ollama (free, slower)
- Deploy CPU-only version (see deploy_ollama_cpu.sh)
- Try different AWS region (us-west-2, eu-west-1)
EOF

echo "✅ Detailed instructions saved to: request_limit_increase.txt"
echo ""


