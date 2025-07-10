import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app import app, extractor

def handler(req):
    """Vercel serverless function handler for /api/health"""
    with app.app_context():
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': 'https://carbalite.vercel.app',
                'Content-Type': 'application/json'
            },
            'body': {
                'status': 'healthy', 
                'message': 'CarbaLite backend is running on Vercel'
            }
        }
