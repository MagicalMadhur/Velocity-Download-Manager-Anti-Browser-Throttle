from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
from typing import Callable

class DownloadHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress logging
        
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/download':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                url = data.get('url')
                filename = data.get('filename')
                req_type = data.get('type', 'file')
                
                if url:
                    if hasattr(self.server, 'add_download_cb'):
                        self.server.add_download_cb(url, filename, req_type)
                        
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "success"}')
                    return
            except Exception as e:
                print(f"Error handling browser request: {e}")
                
        self.send_response(400)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(b'{"status": "error"}')


class BrowserIntegrationServer:
    def __init__(self, add_download_callback: Callable, port=6800):
        self.port = port
        self.add_download_callback = add_download_callback
        self.server = None
        self.thread = None

    def start(self):
        try:
            self.server = HTTPServer(('127.0.0.1', self.port), DownloadHandler)
            self.server.add_download_cb = self.add_download_callback
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            print(f"Browser integration server listening on port {self.port}")
        except Exception as e:
            print(f"Failed to start browser integration server: {e}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
