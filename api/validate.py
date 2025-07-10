import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app import app, extractor
from flask import request, jsonify

def handler(req):
    """Vercel serverless function handler for /api/validate"""
    with app.app_context():
        try:
            # Handle CORS preflight
            if req.method == 'OPTIONS':
                return {
                    'statusCode': 200,
                    'headers': {
                        'Access-Control-Allow-Origin': 'https://carbalite.vercel.app',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    }
                }
            
            if req.method != 'POST':
                return {
                    'statusCode': 405,
                    'body': {'error': 'Method not allowed'}
                }
            
            # Parse request body
            if hasattr(req, 'get_json'):
                data = req.get_json()
            else:
                import json
                data = json.loads(req.body or '{}')
            
            url = data.get('url', '').strip()
            
            if not url:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                    'body': {'error': 'URL is required'}
                }
            
            if not extractor.is_valid_url(url):
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                    'body': {'error': 'Invalid YouTube or SoundCloud URL'}
                }
            
            # Get video info
            video_info = extractor.get_video_info(url)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': 'https://carbalite.vercel.app',
                    'Content-Type': 'application/json'
                },
                'body': {
                    'valid': True,
                    'info': video_info
                }
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                'body': {'error': str(e)}
            }
