import sys
import os
import json
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app import app, extractor
from flask import Flask
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', 'https://carbalite.vercel.app')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            with app.app_context():
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                else:
                    data = {}
                
                url = data.get('url', '').strip()
                
                if not url:
                    self.send_response(400)
                    self.send_header('Access-Control-Allow-Origin', 'https://carbalite.vercel.app')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {'error': 'URL is required'}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                if not extractor.is_valid_url(url):
                    self.send_response(400)
                    self.send_header('Access-Control-Allow-Origin', 'https://carbalite.vercel.app')
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {'error': 'Invalid YouTube or SoundCloud URL'}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return
                
                # Get video info
                video_info = extractor.get_video_info(url)
                
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', 'https://carbalite.vercel.app')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                response = {
                    'valid': True,
                    'video_info': video_info
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Access-Control-Allow-Origin', 'https://carbalite.vercel.app')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'error': str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        self.send_response(405)
        self.send_header('Access-Control-Allow-Origin', 'https://carbalite.vercel.app')
        self.end_headers()
