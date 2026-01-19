#!/bin/bash
# Quick Ollama test script

echo "Enter your Ollama server IP (e.g., 192.168.1.100):"
read OLLAMA_IP

echo ""
echo "Testing connectivity to Ollama server..."
curl -s http://${OLLAMA_IP}:11434/api/tags | python3 -m json.tool

echo ""
echo "If you see model information above, your server is accessible!"
echo ""
echo "Now add these to your .env file:"
echo "LLM_ENABLE=True"
echo "LLM_PROVIDER=ollama"
echo "LLM_OLLAMA_HOST=http://${OLLAMA_IP}"
echo "LLM_OLLAMA_PORT=11434"
echo "LLM_MODEL=gemma2:2b"
