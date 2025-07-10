import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app import app, extractor

def handler(req):
    """Vercel serverless function handler for /api/status/<task_id>"""
    with app.app_context():
        try:
            # Extract task_id from the URL path
            path = req.url.split('/')
            if len(path) < 3:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                    'body': {'error': 'Task ID is required'}
                }
            
            task_id = path[-1]  # Get the last part of the path
            
            if task_id not in extractor.active_downloads:
                return {
                    'statusCode': 404,
                    'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                    'body': {'error': 'Task not found'}
                }
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': 'https://carbalite.vercel.app',
                    'Content-Type': 'application/json'
                },
                'body': extractor.active_downloads[task_id]
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                'body': {'error': str(e)}
            }
