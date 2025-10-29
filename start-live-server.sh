#!/bin/bash

echo "🚀 Starting Several Club development server with live reload..."
echo "📁 Directory: $(pwd)"
echo "🌐 Server will be available at: http://localhost:3000"
echo "🔄 Files will auto-reload when you make changes"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

# Check if Node.js is available
if command -v node &> /dev/null; then
    echo "✅ Node.js found, using live-server..."
    
    # Check if live-server is installed
    if ! command -v live-server &> /dev/null; then
        echo "📦 Installing live-server..."
        npm install -g live-server
    fi
    
    # Start live server
    live-server --port=3000 --open=/index.html --watch=. --no-browser
else
    echo "❌ Node.js not found. Installing Node.js..."
    echo "Please install Node.js from https://nodejs.org/"
    echo ""
    echo "Alternative: Use the Python server:"
    echo "  ./start-dev-server.sh"
fi
