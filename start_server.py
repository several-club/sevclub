#!/usr/bin/env python3

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

# Server configuration
PORT = 8000
HOST = 'localhost'

class AutoReloadHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add headers to prevent caching and enable auto-reload
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_GET(self):
        # Add auto-reload script to HTML pages
        if self.path.endswith('.html') or self.path == '/':
            super().do_GET()
            # Add auto-reload script after the response
            if hasattr(self, '_auto_reload_added'):
                return
            self._auto_reload_added = True
        else:
            super().do_GET()

def start_server():
    # Change to the directory containing the HTML files
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create server
    with socketserver.TCPServer((HOST, PORT), AutoReloadHandler) as httpd:
        print(f"🚀 Server starting...")
        print(f"📁 Serving directory: {os.getcwd()}")
        print(f"🌐 Local URL: http://{HOST}:{PORT}")
        print(f"🔄 Auto-reload enabled")
        print(f"⏹️  Press Ctrl+C to stop")
        print("")
        
        # Open browser automatically
        try:
            webbrowser.open(f'http://{HOST}:{PORT}')
            print("🌐 Browser opened automatically")
        except:
            print("⚠️  Could not open browser automatically")
        
        print("")
        print("=" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
            sys.exit(0)

if __name__ == "__main__":
    start_server()
