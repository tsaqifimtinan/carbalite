import sys
import os
from pathlib import Path
import uuid
import threading

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app import app, extractor
from flask import request, jsonify

def handler(req):
    """Vercel serverless function handler for /api/extract"""
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
            media_type = data.get('type', 'audio')
            format_id = data.get('format_id')
            
            # User preferences from frontend
            preferences = data.get('preferences', {})
            preferred_format = None
            quality_settings = {}
            
            if media_type == 'audio':
                preferred_format = preferences.get('selectedAudioFormat', 'mp3')
                quality_settings['audioQuality'] = preferences.get('audioQuality', '320k')
            else:
                preferred_format = preferences.get('selectedVideoFormat', 'mp4')
                quality_settings['videoQuality'] = preferences.get('videoQuality', '720p')
                quality_settings['audioQuality'] = preferences.get('audioQuality', '320k')
            
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
            
            # Generate unique task ID
            task_id = str(uuid.uuid4())
            
            # Start extraction in background thread with user preferences
            thread = threading.Thread(
                target=extractor.extract_raw_media, 
                args=(url, task_id, format_id, media_type, preferred_format, quality_settings)
            )
            thread.daemon = True
            thread.start()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': 'https://carbalite.vercel.app',
                    'Content-Type': 'application/json'
                },
                'body': {
                    'task_id': task_id,
                    'message': f'Media extraction started with format: {preferred_format}',
                    'preferences': {
                        'format': preferred_format,
                        'quality': quality_settings
                    }
                }
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                'body': {'error': str(e)}
            }
