#!/bin/bash

# Start development server with live reload
echo "Starting development server with live reload..."
echo "Your site will be available at: http://localhost:3000"
echo "Press Ctrl+C to stop the server"
echo ""

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    echo "Using Python 3 HTTP server with live reload..."
    # Install live reload if not already installed
    pip3 install livereload 2>/dev/null || echo "Installing livereload..."
    pip3 install livereload
    
    # Start live reload server
    python3 -c "
import os
from livereload import Server, shell

server = Server()
server.watch('.', shell('echo "Files changed, reloading..."'))
server.serve(port=3000, host='localhost', open_url=True)
"
elif command -v python &> /dev/null; then
    echo "Using Python HTTP server..."
    python -m http.server 3000
else
    echo "Python not found. Please install Python or use a different method."
    echo "You can also use:"
    echo "  - VS Code Live Server extension"
    echo "  - Browser-sync: npx browser-sync start --server --files '*.html, *.css, *.js'"
    echo "  - Live Server: npx live-server"
fi
