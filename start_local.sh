#!/bin/bash

# Several.Club Local Development Server
echo "🚀 Starting Several.Club Local Server..."
echo ""

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 found"
    python3 start_server.py
elif command -v python &> /dev/null; then
    echo "✅ Python found"
    python start_server.py
else
    echo "❌ Python not found. Please install Python 3"
    exit 1
fi
