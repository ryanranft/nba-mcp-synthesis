#!/bin/bash
# Load API keys from secure files and export them as environment variables

# Function to load API key from file
load_api_key() {
    local key_file="$1"
    local var_name="$2"

    if [ -f "$key_file" ]; then
        # Extract the value after the = sign
        local key_value=$(grep -v '^#' "$key_file" | grep -v '^$' | cut -d'=' -f2- | tr -d ' ')
        if [ -n "$key_value" ] && [ "$key_value" != "your_${var_name,,}_api_key_here" ]; then
            export "$var_name"="$key_value"
            echo "✅ Loaded $var_name"
        else
            echo "⚠️  $var_name not set or using placeholder value"
        fi
    else
        echo "❌ API key file not found: $key_file"
    fi
}

echo "🔑 Loading API keys from secure files..."

# Load each API key
load_api_key "$HOME/.cursor/secrets/google_api_key.txt" "GOOGLE_API_KEY"
load_api_key "$HOME/.cursor/secrets/deepseek_api_key.txt" "DEEPSEEK_API_KEY"
load_api_key "$HOME/.cursor/secrets/anthropic_api_key.txt" "ANTHROPIC_API_KEY"
load_api_key "$HOME/.cursor/secrets/openai_api_key.txt" "OPENAI_API_KEY"

echo ""
echo "🔍 API Key Status:"
echo "GOOGLE_API_KEY: ${GOOGLE_API_KEY:+SET}"
echo "DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY:+SET}"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+SET}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
echo ""

# Check if all keys are loaded
if [ -n "$GOOGLE_API_KEY" ] && [ -n "$DEEPSEEK_API_KEY" ] && [ -n "$ANTHROPIC_API_KEY" ] && [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ All API keys loaded successfully!"
    echo "🚀 Ready to run the workflow!"
else
    echo "❌ Some API keys are missing. Please update the files in ~/.cursor/secrets/"
    echo ""
    echo "To update API keys:"
    echo "1. Edit the files in ~/.cursor/secrets/"
    echo "2. Replace 'your_*_api_key_here' with your actual API keys"
    echo "3. Run this script again"
fi




