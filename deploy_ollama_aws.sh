#!/bin/bash

# Deploy Ollama on AWS EC2 with GPU for Better MCP Performance
# This script sets up a powerful GPU instance running Ollama

set -e

echo "🚀 NBA MCP + Ollama AWS Deployment"
echo "===================================="
echo ""

# Configuration
INSTANCE_TYPE="g5.xlarge"  # NVIDIA A10G GPU, 24GB VRAM
# Alternative: g5.2xlarge (48GB VRAM), p3.2xlarge (Tesla V100)
AMI_ID="ami-0c55b159cbfafe1f0"  # Amazon Linux 2 with GPU support
KEY_NAME="ollama-mcp-key"
SECURITY_GROUP="ollama-mcp-sg"
REGION="us-east-1"

echo "📋 Configuration:"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  Region: $REGION"
echo "  GPU: NVIDIA A10G (24GB VRAM)"
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed"
    exit 1
fi

echo "✅ AWS CLI found"
echo ""

# Get latest Ubuntu AMI with GPU support
echo "🔍 Finding latest Ubuntu AMI with GPU support..."
AMI_ID=$(aws ec2 describe-images \
    --region $REGION \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
    --output text)

echo "  Using AMI: $AMI_ID"
echo ""

# Create security group
echo "🔒 Creating security group..."
if ! aws ec2 describe-security-groups --group-names $SECURITY_GROUP --region $REGION &> /dev/null; then
    aws ec2 create-security-group \
        --group-name $SECURITY_GROUP \
        --description "Security group for Ollama MCP server" \
        --region $REGION

    # Allow SSH (22)
    aws ec2 authorize-security-group-ingress \
        --group-name $SECURITY_GROUP \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region $REGION

    # Allow Ollama API (11434)
    aws ec2 authorize-security-group-ingress \
        --group-name $SECURITY_GROUP \
        --protocol tcp \
        --port 11434 \
        --cidr 0.0.0.0/0 \
        --region $REGION

    echo "✅ Security group created"
else
    echo "✅ Security group already exists"
fi

echo ""

# Create key pair if needed
echo "🔑 Checking SSH key pair..."
if ! aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION &> /dev/null; then
    echo "  Creating new key pair..."
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --region $REGION \
        --query 'KeyMaterial' \
        --output text > ${KEY_NAME}.pem

    chmod 400 ${KEY_NAME}.pem
    echo "✅ Key pair created: ${KEY_NAME}.pem"
    echo "⚠️  SAVE THIS FILE! You'll need it to SSH into the instance"
else
    echo "✅ Key pair already exists"
fi

echo ""

# Create user data script
echo "📝 Creating instance bootstrap script..."
cat > ollama-setup.sh << 'EOF'
#!/bin/bash

# Update system
apt-get update
apt-get upgrade -y

# Install NVIDIA drivers
apt-get install -y nvidia-driver-535
apt-get install -y nvidia-cuda-toolkit

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update
apt-get install -y nvidia-container-toolkit
systemctl restart docker

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Configure Ollama to listen on all interfaces
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << 'OVERRIDE'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
OVERRIDE

systemctl daemon-reload
systemctl restart ollama

# Pull larger models (this will take a while)
ollama pull qwen2.5-coder:72b      # 72B model - much better!
# ollama pull llama3.1:70b         # Alternative: Llama 3.1 70B
# ollama pull deepseek-coder:33b   # Alternative: DeepSeek 33B

# Create health check endpoint
echo "Ollama GPU Instance Ready!" > /var/www/html/health.html

echo "✅ Ollama setup complete!"
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
    --user-data file://ollama-setup.sh \
    --region $REGION \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=Ollama-MCP-GPU}]" \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=100,VolumeType=gp3}" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"
echo ""

# Wait for instance to be running
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
echo "🎉 Ollama AWS Instance Deployed!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "📊 Instance Details:"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP:   $PUBLIC_IP"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  GPU: NVIDIA A10G (24GB VRAM)"
echo ""
echo "🔑 SSH Access:"
echo "  ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "⏳ Setup Progress:"
echo "  The instance is installing Ollama and downloading models."
echo "  This will take 15-30 minutes."
echo ""
echo "🧪 Check Status:"
echo "  ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo "  sudo journalctl -u ollama -f"
echo ""
echo "🌐 Ollama API:"
echo "  http://${PUBLIC_IP}:11434"
echo ""
echo "💰 Estimated Cost:"
echo "  g5.xlarge: ~\$1.00/hour"
echo "  Monthly (24/7): ~\$730"
echo "  Recommended: Stop when not in use!"
echo ""
echo "🛑 To Stop Instance:"
echo "  aws ec2 stop-instances --instance-ids $INSTANCE_ID --region $REGION"
echo ""
echo "▶️ To Start Instance:"
echo "  aws ec2 start-instances --instance-ids $INSTANCE_ID --region $REGION"
echo ""
echo "🗑️ To Terminate Instance:"
echo "  aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION"
echo ""
echo "═══════════════════════════════════════════════════════"

# Save connection info
cat > ollama-aws-connection.txt << EOFCON
Ollama AWS Connection Info
==========================

Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Region: $REGION
Instance Type: $INSTANCE_TYPE

SSH Command:
ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}

Ollama API:
http://${PUBLIC_IP}:11434

Models Available:
- qwen2.5-coder:72b (Better than 32B local!)
- llama3.1:70b (optional)
- deepseek-coder:33b (optional)

Next Steps:
1. Wait 15-30 minutes for setup to complete
2. SSH in and check: sudo systemctl status ollama
3. Test: curl http://${PUBLIC_IP}:11434/api/tags
4. Update your local config to use this endpoint
EOFCON

echo "✅ Connection info saved to: ollama-aws-connection.txt"
echo ""
echo "📚 Next: Run ./configure_ollama_aws.sh to connect your MCP"


