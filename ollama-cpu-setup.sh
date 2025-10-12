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
