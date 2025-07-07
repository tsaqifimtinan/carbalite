"""
Flask Backend for CarbaLite - YouTube & SoundCloud Media Extractor
Provides API endpoints for extracting raw media for client-side processing with ffmpeg.wasm
"""

import os
import sys
import re
import json
import tempfile
import shutil
from pathlib import Path
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import yt_dlp
import requests
from urllib.parse import urlparse
import uuid
from datetime import datetime, timedelta
import threading
import time
import io

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Clean up old files every hour
CLEANUP_INTERVAL = 3600  # 1 hour
FILE_EXPIRY = 3600  # Files expire after 1 hour

class MediaExtractor:
    def __init__(self):
        self.active_downloads = {}
        
    def is_valid_url(self, url):
        """Validate if the URL is a valid YouTube or SoundCloud URL"""
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        
        soundcloud_regex = re.compile(
            r'(https?://)?(www\.)?soundcloud\.com/[\w\-\.]+'
        )
        
        return youtube_regex.match(url) is not None or soundcloud_regex.match(url) is not None
    
    def sanitize_filename(self, filename):
        """Remove invalid characters from filename"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        filename = re.sub(r'\s+', ' ', filename).strip()
        return filename[:200]
    
    def download_thumbnail(self, thumbnail_url):
        """Download video thumbnail"""
        try:
            response = requests.get(thumbnail_url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Warning: Could not download thumbnail: {e}")
            return None
    
    def get_video_info(self, url):
        """Extract video information without downloading"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                video_info = ydl.extract_info(url, download=False)
                
            return {
                'title': video_info.get('title', 'Unknown'),
                'uploader': video_info.get('uploader', 'Unknown'),
                'duration': video_info.get('duration'),
                'thumbnail': video_info.get('thumbnail'),
                'description': video_info.get('description', ''),
                'upload_date': video_info.get('upload_date'),
                'view_count': video_info.get('view_count'),
                'webpage_url': video_info.get('webpage_url', url),
                'formats': self._get_format_info(video_info)
            }
        except Exception as e:
            raise Exception(f"Failed to extract video info: {str(e)}")
    
    def _get_format_info(self, video_info):
        """Extract available format information for client-side processing"""
        formats = []
        if 'formats' in video_info:
            for fmt in video_info['formats']:
                format_info = {
                    'format_id': fmt.get('format_id'),
                    'ext': fmt.get('ext'),
                    'quality': fmt.get('quality'),
                    'filesize': fmt.get('filesize'),
                    'abr': fmt.get('abr'),  # Audio bitrate
                    'vbr': fmt.get('vbr'),  # Video bitrate
                    'fps': fmt.get('fps'),
                    'width': fmt.get('width'),
                    'height': fmt.get('height'),
                    'acodec': fmt.get('acodec'),
                    'vcodec': fmt.get('vcodec'),
                    'url': fmt.get('url'),
                    'format_note': fmt.get('format_note')
                }
                if format_info['url']:  # Only include formats with accessible URLs
                    formats.append(format_info)
        return formats
    
    def extract_raw_media(self, url, task_id, format_id=None, media_type='audio', preferred_format=None, quality_settings=None):
        """Extract raw media stream for client-side processing with user preferences"""
        try:
            self.active_downloads[task_id] = {
                'status': 'extracting',
                'progress': 0,
                'message': 'Extracting media information...'
            }
            
            # Configure yt-dlp with better options based on user preferences
            ydl_opts = {
                'quiet': True,
                'no_warnings': False,
                'extractaudio': False,
            }
            
            # Set format selector based on user preferences and media type
            if media_type == 'video':
                if preferred_format:
                    # User specified video format preference
                    video_quality = quality_settings.get('videoQuality', '720p') if quality_settings else '720p'
                    height_map = {'480p': 480, '720p': 720, '1080p': 1080}
                    max_height = height_map.get(video_quality, 720)
                    
                    ydl_opts['format'] = f'best[ext={preferred_format}][height<={max_height}]/best[height<={max_height}]/best[ext={preferred_format}]/best'
                else:
                    ydl_opts['format'] = 'best[ext=mp4]/best[ext=webm]/best'
            else:
                # Audio download
                if preferred_format:
                    # User specified audio format preference
                    audio_quality = quality_settings.get('audioQuality', '320k') if quality_settings else '320k'
                    quality_map = {'128k': 128, '256k': 256, '320k': 320}
                    max_abr = quality_map.get(audio_quality, 320)
                    
                    ydl_opts['format'] = f'bestaudio[ext={preferred_format}][abr<={max_abr}]/bestaudio[abr<={max_abr}]/bestaudio[ext={preferred_format}]/bestaudio'
                else:
                    ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio'
            
            # Get video info
            video_info = None
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                video_info = ydl.extract_info(url, download=False)
            
            self.active_downloads[task_id]['message'] = 'Finding best format...'
            
            # Select appropriate format with better logic
            selected_format = None
            available_formats = video_info.get('formats', [])
            
            if format_id:
                # Find specific format
                for fmt in available_formats:
                    if fmt.get('format_id') == format_id:
                        selected_format = fmt
                        break
            else:
                # Auto-select best format based on media type and user preferences
                if media_type == 'audio':
                    # Prioritize user's preferred audio format
                    target_format = preferred_format or 'mp3'
                    target_quality = quality_settings.get('audioQuality', '320k') if quality_settings else '320k'
                    quality_map = {'128k': 128, '256k': 256, '320k': 320}
                    max_abr = quality_map.get(target_quality, 320)
                    
                    # First try: exact format match with quality preference
                    preferred_formats = [f for f in available_formats 
                                       if f.get('vcodec') == 'none' and f.get('acodec') != 'none' 
                                       and f.get('ext') == target_format
                                       and f.get('url') and (f.get('abr', 0) or 0) <= max_abr]
                    
                    if preferred_formats:
                        # Sort by audio bitrate, prefer higher quality within limit
                        preferred_formats.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
                        selected_format = preferred_formats[0]
                    else:
                        # Second try: any audio-only format with quality preference
                        audio_formats = [f for f in available_formats 
                                       if f.get('vcodec') == 'none' and f.get('acodec') != 'none' 
                                       and f.get('url') and (f.get('abr', 0) or 0) <= max_abr]
                        
                        if audio_formats:
                            # Sort by format preference, then quality
                            def format_priority(fmt):
                                ext = fmt.get('ext', '')
                                if ext == target_format:
                                    return (3, fmt.get('abr', 0) or 0)
                                elif ext in ['mp3', 'm4a', 'aac']:
                                    return (2, fmt.get('abr', 0) or 0)
                                else:
                                    return (1, fmt.get('abr', 0) or 0)
                            
                            audio_formats.sort(key=format_priority, reverse=True)
                            selected_format = audio_formats[0]
                        else:
                            # Fallback: any format with audio
                            mixed_formats = [f for f in available_formats 
                                           if f.get('acodec') != 'none' and f.get('url')]
                            if mixed_formats:
                                mixed_formats.sort(key=lambda x: x.get('abr', 0) or 0, reverse=True)
                                selected_format = mixed_formats[0]
                else:
                    # For video, find best quality video with audio based on user preferences
                    target_format = preferred_format or 'mp4'
                    target_quality = quality_settings.get('videoQuality', '720p') if quality_settings else '720p'
                    height_map = {'480p': 480, '720p': 720, '1080p': 1080}
                    max_height = height_map.get(target_quality, 720)
                    
                    # First try: exact format match with quality preference
                    preferred_formats = [f for f in available_formats 
                                       if f.get('vcodec') != 'none' and f.get('acodec') != 'none' 
                                       and f.get('ext') == target_format
                                       and f.get('url') and (f.get('height', 0) or 0) <= max_height]
                    
                    if preferred_formats:
                        # Sort by resolution, prefer higher quality within limit
                        preferred_formats.sort(key=lambda x: (x.get('height', 0) or 0, x.get('abr', 0) or 0), reverse=True)
                        selected_format = preferred_formats[0]
                    else:
                        # Second try: any video format with quality preference
                        video_formats = [f for f in available_formats 
                                       if f.get('vcodec') != 'none' and f.get('acodec') != 'none' 
                                       and f.get('url') and (f.get('height', 0) or 0) <= max_height]
                        
                        if video_formats:
                            # Sort by format preference, then quality
                            def format_priority(fmt):
                                ext = fmt.get('ext', '')
                                if ext == target_format:
                                    return (3, fmt.get('height', 0) or 0, fmt.get('abr', 0) or 0)
                                elif ext in ['mp4', 'webm', 'mkv']:
                                    return (2, fmt.get('height', 0) or 0, fmt.get('abr', 0) or 0)
                                else:
                                    return (1, fmt.get('height', 0) or 0, fmt.get('abr', 0) or 0)
                            
                            video_formats.sort(key=format_priority, reverse=True)
                            selected_format = video_formats[0]
                        else:
                            # Fallback: any video format
                            video_formats = [f for f in available_formats 
                                           if f.get('vcodec') != 'none' and f.get('url')]
                            if video_formats:
                                video_formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
                                selected_format = video_formats[0]
            
            if not selected_format or not selected_format.get('url'):
                raise Exception("No suitable format found")
            
            print(f"Selected format for {media_type}: {selected_format.get('format_id')} - {selected_format.get('ext')} - {selected_format.get('format_note')} - Size: {selected_format.get('filesize')}")
            print(f"User preferences - Format: {preferred_format}, Quality: {quality_settings}")
            
            # Generate proper filename with metadata
            title = self.sanitize_filename(video_info.get('title', 'Unknown'))
            uploader = self.sanitize_filename(video_info.get('uploader', ''))
            ext = selected_format.get('ext', preferred_format or ('mp4' if media_type == 'video' else 'mp3'))
            
            if uploader:
                filename = f"{title} - {uploader}.{ext}"
            else:
                filename = f"{title}.{ext}"
            
            self.active_downloads[task_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Media stream ready!',
                'stream_url': selected_format['url'],
                'filename': filename,
                'format_info': {
                    'format_id': selected_format.get('format_id'),
                    'ext': ext,
                    'filesize': selected_format.get('filesize'),
                    'abr': selected_format.get('abr'),
                    'vbr': selected_format.get('vbr'),
                    'fps': selected_format.get('fps'),
                    'width': selected_format.get('width'),
                    'height': selected_format.get('height'),
                    'acodec': selected_format.get('acodec'),
                    'vcodec': selected_format.get('vcodec'),
                    'format_note': selected_format.get('format_note')
                },
                'video_info': {
                    'title': video_info.get('title', 'Unknown'),
                    'uploader': video_info.get('uploader', 'Unknown'),
                    'duration': video_info.get('duration'),
                    'thumbnail': video_info.get('thumbnail'),
                    'upload_date': video_info.get('upload_date'),
                    'view_count': video_info.get('view_count'),
                    'description': video_info.get('description', '')[:500]  # Truncate description
                }
            }
            
        except Exception as e:
            self.active_downloads[task_id] = {
                'status': 'error',
                'progress': 0,
                'message': f'Error: {str(e)}'
            }
    
    def stream_media(self, stream_url):
        """Stream media content with proper headers for CORS"""
        try:
            # Use proper headers that YouTube expects
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Make request to the media URL with proper headers
            response = requests.get(stream_url, stream=True, timeout=30, headers=headers)
            response.raise_for_status()
            
            # Get content length and type
            content_length = response.headers.get('content-length', '')
            content_type = response.headers.get('content-type', 'application/octet-stream')
            
            # Create a generator to stream the content
            def generate():
                for chunk in response.iter_content(chunk_size=16384):  # Larger chunks for better performance
                    if chunk:  # Filter out keep-alive chunks
                        yield chunk
            
            # Return response with appropriate headers
            return Response(
                generate(),
                content_type=content_type,
                headers={
                    'Content-Length': content_length,
                    'Accept-Ranges': 'bytes',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET',
                    'Access-Control-Allow-Headers': 'Range, Content-Type',
                    'Cache-Control': 'no-cache',
                    'X-Content-Type-Options': 'nosniff'
                }
            )
            
        except Exception as e:
            print(f"Streaming error: {e}")
            return jsonify({'error': f'Failed to stream media: {str(e)}'}), 500

# Initialize extractor
extractor = MediaExtractor()

# Routes
@app.route('/api/validate', methods=['POST'])
def validate_url():
    """Validate URL and get video information"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if not extractor.is_valid_url(url):
            return jsonify({'error': 'Invalid YouTube or SoundCloud URL'}), 400
        
        # Get video info
        video_info = extractor.get_video_info(url)
        
        return jsonify({
            'valid': True,
            'info': video_info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract', methods=['POST'])
def extract_media():
    """Extract raw media stream for client-side processing with user preferences"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        media_type = data.get('type', 'audio')  # 'audio' or 'video'
        format_id = data.get('format_id')  # Optional specific format
        
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
            return jsonify({'error': 'URL is required'}), 400
        
        if not extractor.is_valid_url(url):
            return jsonify({'error': 'Invalid YouTube or SoundCloud URL'}), 400
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Start extraction in background thread with user preferences
        thread = threading.Thread(
            target=extractor.extract_raw_media, 
            args=(url, task_id, format_id, media_type, preferred_format, quality_settings)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': f'Media extraction started with format: {preferred_format}',
            'preferences': {
                'format': preferred_format,
                'quality': quality_settings
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<task_id>', methods=['GET'])
def get_extraction_status(task_id):
    """Get extraction status"""
    if task_id not in extractor.active_downloads:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify(extractor.active_downloads[task_id])

@app.route('/api/stream/<task_id>', methods=['GET'])
def stream_media(task_id):
    """Stream the raw media for client-side processing"""
    if task_id not in extractor.active_downloads:
        return jsonify({'error': 'Task not found'}), 404
    
    task = extractor.active_downloads[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Extraction not completed'}), 400
    
    stream_url = task.get('stream_url')
    if not stream_url:
        return jsonify({'error': 'Stream URL not available'}), 404
    
    return extractor.stream_media(stream_url)

@app.route('/api/thumbnail/<task_id>', methods=['GET'])
def get_thumbnail(task_id):
    """Get video thumbnail"""
    if task_id not in extractor.active_downloads:
        return jsonify({'error': 'Task not found'}), 404
    
    task = extractor.active_downloads[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Extraction not completed'}), 400
    
    thumbnail_url = task.get('video_info', {}).get('thumbnail')
    if not thumbnail_url:
        return jsonify({'error': 'Thumbnail not available'}), 404
    
    try:
        thumbnail_data = extractor.download_thumbnail(thumbnail_url)
        if thumbnail_data:
            return Response(
                thumbnail_data,
                content_type='image/jpeg',
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'public, max-age=3600'
                }
            )
        else:
            return jsonify({'error': 'Failed to download thumbnail'}), 500
    except Exception as e:
        return jsonify({'error': f'Thumbnail error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'CarbaLite backend is running'})

# Legacy endpoints for backward compatibility (deprecated)
@app.route('/api/download', methods=['POST'])
def start_download():
    """Legacy download endpoint - redirects to new extract endpoint"""
    return jsonify({
        'error': 'This endpoint is deprecated. Use /api/extract instead.',
        'message': 'CarbaLite now uses client-side processing with ffmpeg.wasm'
    }), 410

@app.route('/api/download/<task_id>', methods=['GET'])
def download_file(task_id):
    """Legacy download endpoint - redirects to new stream endpoint"""
    return jsonify({
        'error': 'This endpoint is deprecated. Use /api/stream instead.',
        'message': 'CarbaLite now uses client-side processing with ffmpeg.wasm'
    }), 410

def cleanup_old_tasks():
    """Clean up old extraction tasks from memory"""
    while True:
        try:
            current_time = time.time()
            # Remove tasks older than 1 hour
            tasks_to_remove = []
            for task_id, task_data in extractor.active_downloads.items():
                # Assume task was created when it was first added
                # In a production environment, you'd want to add a timestamp
                if len(extractor.active_downloads) > 100:  # Simple cleanup when too many tasks
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove[:50]:  # Remove oldest 50 tasks
                extractor.active_downloads.pop(task_id, None)
                print(f"Cleaned up old task: {task_id}")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        time.sleep(CLEANUP_INTERVAL)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_tasks)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    print("CarbaLite Backend Server Starting...")
    print("Client-side processing with ffmpeg.wasm enabled")
    print("Required dependencies: yt-dlp, requests, flask, flask-cors")
    print("No server-side ffmpeg required!")
    print("Ready for Vercel deployment")
    print("=" * 60)
    
    app.run(debug=True, port=5000, host='0.0.0.0')
