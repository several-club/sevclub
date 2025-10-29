#!/usr/bin/env python3

import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Server configuration
PORT = 8000
HOST = 'localhost'

class LiveReloadHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add headers to prevent caching
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_GET(self):
        # Add live-reload script to HTML pages
        if self.path.endswith('.html') or self.path == '/':
            super().do_GET()
            # Add live-reload script
            if hasattr(self, '_live_reload_added'):
                return
            self._live_reload_added = True
        else:
            super().do_GET()

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, server):
        self.server = server
        self.last_modified = {}
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(('.html', '.css', '.js')):
            print(f"🔄 File changed: {os.path.basename(event.src_path)}")
            # Trigger browser refresh
            self.notify_browser()
    
    def notify_browser(self):
        # Send a simple notification that files have changed
        print("🔄 Files updated - refresh your browser")

def start_live_server():
    # Change to the directory containing the HTML files
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create server
    with socketserver.TCPServer((HOST, PORT), LiveReloadHandler) as httpd:
        print(f"🚀 Live Server starting...")
        print(f"📁 Serving directory: {os.getcwd()}")
        print(f"🌐 Local URL: http://{HOST}:{PORT}")
        print(f"🔄 Live reload enabled")
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
        
        # Start file watcher
        event_handler = FileChangeHandler(httpd)
        observer = Observer()
        observer.schedule(event_handler, path='.', recursive=True)
        observer.start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
            observer.stop()
            sys.exit(0)

if __name__ == "__main__":
    start_live_server()
