import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app import app, extractor
from flask import send_file

def handler(req):
    """Vercel serverless function handler for /api/download/<task_id>"""
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
            
            task = extractor.active_downloads[task_id]
            
            if task['status'] != 'completed':
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                    'body': {'error': 'Download not completed'}
                }
            
            file_path = task.get('file_path')
            if not file_path or not Path(file_path).exists():
                return {
                    'statusCode': 404,
                    'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                    'body': {'error': 'Downloaded file not found'}
                }
            
            # For Vercel, we need to return the file content as binary
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': 'https://carbalite.vercel.app',
                    'Content-Type': 'application/octet-stream',
                    'Content-Disposition': f'attachment; filename="{task.get("filename", "download")}"'
                },
                'body': file_content,
                'isBase64Encoded': True
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Access-Control-Allow-Origin': 'https://carbalite.vercel.app'},
                'body': {'error': f'Failed to download file: {str(e)}'}
            }
