#!/bin/bash

echo "📱 NBA MCP MOBILE ACCESS"
echo "=" | awk '{for(i=0;i<60;i++)printf"=";printf"\n"}'
echo ""

# Get Mac's local IP
MAC_IP=$(ipconfig getifaddr en0 2>/dev/null)
if [ -z "$MAC_IP" ]; then
    MAC_IP=$(ipconfig getifaddr en1 2>/dev/null)
fi

if [ -z "$MAC_IP" ]; then
    echo "❌ Could not find Mac IP address"
    echo "Try: ifconfig | grep 'inet '"
    exit 1
fi

echo "✅ Your Mac's IP Address: $MAC_IP"
echo ""
echo "🌐 CONNECT FROM YOUR PHONE:"
echo ""
echo "1. Make sure your phone is on the SAME WiFi network"
echo ""
echo "2. Open Safari or Chrome on your phone"
echo ""
echo "3. Go to this URL:"
echo ""
echo "   📱 http://$MAC_IP:8000/ollama_web_chat.html"
echo ""
echo "=" | awk '{for(i=0;i<60;i++)printf"=";printf"\n"}'
echo ""

# Check if web server is running
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "✅ Web chat is RUNNING on port 8000"
    echo ""
    echo "🎉 You're ready to connect!"
    echo ""
    echo "Just open this URL on your phone:"
    echo "http://$MAC_IP:8000/ollama_web_chat.html"
else
    echo "⚠️  Web chat is NOT running"
    echo ""
    echo "To start it, run:"
    echo "./start_ollama_chat.sh"
    echo ""
    echo "Then access from your phone:"
    echo "http://$MAC_IP:8000/ollama_web_chat.html"
fi

echo ""
echo "=" | awk '{for(i=0;i<60;i++)printf"=";printf"\n"}'
echo ""
echo "📚 What you can do from your phone:"
echo "  • Chat with AI (Ollama + MCP)"
echo "  • Use all 90 NBA MCP tools"
echo "  • Read any of 17 technical books"
echo "  • Run NBA analytics"
echo "  • Do ML calculations"
echo ""
echo "Need remote access? See MOBILE_ACCESS_SETUP.md"
echo ""
