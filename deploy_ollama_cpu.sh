#!/bin/bash

# Deploy Ollama on CPU-only AWS Instance (works with current limits)
# Temporary solution while waiting for GPU limit increase

set -e

echo "🚀 NBA MCP + Ollama AWS Deployment (CPU Version)"
echo "=================================================="
echo ""

# Configuration
INSTANCE_TYPE="t3.2xlarge"  # 8 vCPU, 32GB RAM - Can run 32B models
AMI_ID="ami-0c55b159cbfafe1f0"
KEY_NAME="ollama-mcp-key"
SECURITY_GROUP="ollama-mcp-sg"
REGION="us-east-1"

echo "📋 Configuration:"
echo "  Instance Type: $INSTANCE_TYPE (CPU-only)"
echo "  Region: $REGION"
echo "  vCPUs: 32"
echo "  RAM: 64GB"
echo "  Cost: ~$0.33/hour (vs $1.00/hour for GPU)"
echo ""

# Get latest Ubuntu AMI
echo "🔍 Finding latest Ubuntu AMI..."
AMI_ID=$(aws ec2 describe-images \
    --region $REGION \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)

echo "  Using AMI: $AMI_ID"
echo ""

# Create user data script
echo "📝 Creating instance bootstrap script..."
cat > ollama-cpu-setup.sh << 'EOF'
#!/bin/bash

# Update system
apt-get update
apt-get upgrade -y

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure Ollama
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << 'OVERRIDE'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
OVERRIDE

systemctl daemon-reload
systemctl restart ollama

# Pull 32B model (works well on CPU)
ollama pull qwen2.5-coder:32b

# Optional: Pull smaller models
# ollama pull llama3.1:8b
# ollama pull mistral:7b-instruct

echo "✅ Ollama CPU setup complete!"
EOF

echo "✅ Bootstrap script created"
echo ""

# Launch instance
echo "🚀 Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-groups $SECURITY_GROUP \
    --user-data file://ollama-cpu-setup.sh \
    --region $REGION \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=Ollama-MCP-CPU}]" \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=100,VolumeType=gp3}" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"
echo ""

# Wait for instance
echo "⏳ Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✅ Instance is running!"
echo ""
echo "═══════════════════════════════════════════════════════"
echo "🎉 Ollama CPU Instance Deployed!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📊 Instance Details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP:   $PUBLIC_IP"
echo "  Instance Type: $INSTANCE_TYPE (CPU-only)"
echo "  vCPUs: 32"
echo "  RAM: 64GB"
echo ""
echo "🔑 SSH Access:"
echo "  ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "⏳ Setup Progress:"
echo "  Installing Ollama and downloading 32B model."
echo "  This will take 10-15 minutes."
echo ""
echo "🌐 Ollama API:"
echo "  http://${PUBLIC_IP}:11434"
echo ""
echo "💰 Cost:"
echo "  t3.2xlarge: ~$0.33/hour"
echo "  Spot pricing: ~$0.40/hour (save 70%!)"
echo ""
echo "⚡ Performance:"
echo "  Slower than GPU (3-5 sec vs 1-2 sec)"
echo "  But still faster than local Mac!"
echo "  Good temporary solution while waiting for GPU approval"
echo ""
echo "🛑 To Stop Instance:"
echo "  aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION"
echo ""
echo "═══════════════════════════════════════════════════════"

# Save connection info
cat > ollama-cpu-connection.txt << EOFCON
Ollama CPU Instance Connection Info
===================================

Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Instance Type: $INSTANCE_TYPE (CPU-only, 8 vCPU, 32GB RAM)
Cost: $1.36/hour

SSH Command:
ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}

Ollama API:
http://${PUBLIC_IP}:11434

Model: qwen2.5-coder:32b

Performance:
- Response time: 3-5 seconds (vs 1-2 sec on GPU)
- Still faster than local Mac!
- Good temporary solution

Next Steps:
1. Wait 10-15 minutes for setup
2. Test: curl http://${PUBLIC_IP}:11434/api/tags
3. Configure: ./configure_ollama_aws.sh
4. Request GPU limit increase for better performance
EOFCON

echo "✅ Connection info saved to: ollama-cpu-connection.txt"
echo ""
echo "📚 Next: Wait 10-15 min, then run ./configure_ollama_aws.sh"


