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
