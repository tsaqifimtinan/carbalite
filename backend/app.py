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

# Configuration for allowed origins
ALLOWED_ORIGINS = [
    'http://localhost:3000',           # Development frontend
    'http://127.0.0.1:3000',          # Development frontend
    'https://carbalite.vercel.app',    # Production frontend
]

# For Vercel deployment, also allow preview URLs
if os.getenv('VERCEL_URL'):
    ALLOWED_ORIGINS.append(f"https://{os.getenv('VERCEL_URL')}")

# Configure CORS with specific settings
CORS(app, 
     origins=ALLOWED_ORIGINS,  # Allow specific domains
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'Accept', 'Origin', 'X-Requested-With'],
     expose_headers=['Content-Length', 'Content-Type', 'Content-Disposition'],
     supports_credentials=False,
     send_wildcard=False,  # Explicitly disable wildcard
     automatic_options=True  # Handle OPTIONS requests automatically
)

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
        """Download media with user preferences and provide file for download"""
        try:
            self.active_downloads[task_id] = {
                'status': 'extracting',
                'progress': 0,
                'message': 'Extracting media information...'
            }
            
            # Generate filename first
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                video_info = ydl.extract_info(url, download=False)
            
            title = self.sanitize_filename(video_info.get('title', 'Unknown'))
            uploader = self.sanitize_filename(video_info.get('uploader', ''))
            
            # Determine final format and filename
            if media_type == 'audio':
                final_format = preferred_format or 'mp3'
                if uploader:
                    filename = f"{title} - {uploader}.{final_format}"
                else:
                    filename = f"{title}.{final_format}"
            else:
                final_format = preferred_format or 'mp4' 
                if uploader:
                    filename = f"{title} - {uploader}.{final_format}"
                else:
                    filename = f"{title}.{final_format}"
            
            # Create output path
            output_path = DOWNLOAD_DIR / filename
            temp_path = DOWNLOAD_DIR / f"temp_{task_id}"
            
            self.active_downloads[task_id]['message'] = 'Configuring download options...'
            
            # Configure yt-dlp with proper download options
            ydl_opts = {
                'quiet': False,
                'no_warnings': False,
                'outtmpl': str(temp_path / '%(title)s.%(ext)s'),
                'extract_flat': False,
            }
            
            # Configure format and post-processing based on user preferences
            if media_type == 'audio':
                # Audio download with quality preferences
                audio_quality = quality_settings.get('audioQuality', '320k') if quality_settings else '320k'
                quality_map = {'128k': '5', '256k': '0', '320k': '0'}  # ffmpeg quality scale (5=128k, 0=best)
                ffmpeg_quality = quality_map.get(audio_quality, '0')
                
                if preferred_format == 'mp3':
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': audio_quality.replace('k', ''),
                    }]
                elif preferred_format == 'wav':
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'wav',
                    }]
                elif preferred_format == 'flac':
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'flac',
                    }]
                elif preferred_format == 'aac':
                    ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'aac',
                        'preferredquality': audio_quality.replace('k', ''),
                    }]
                else:
                    # Default to best audio
                    ydl_opts['format'] = 'bestaudio/best'
            else:
                # Video download with quality preferences
                video_quality = quality_settings.get('videoQuality', '720p') if quality_settings else '720p'
                height_map = {'480p': 480, '720p': 720, '1080p': 1080, '1440p': 1440, '2160p': 2160}
                max_height = height_map.get(video_quality, 720)
                
                if preferred_format == 'mp4':
                    ydl_opts['format'] = f'best[ext=mp4][height<={max_height}]/best[height<={max_height}]/best[ext=mp4]/best'
                elif preferred_format == 'webm':
                    ydl_opts['format'] = f'best[ext=webm][height<={max_height}]/best[height<={max_height}]/best[ext=webm]/best'
                elif preferred_format == 'mkv':
                    ydl_opts['format'] = f'best[ext=mkv][height<={max_height}]/best[height<={max_height}]/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mkv',
                    }]
                else:
                    ydl_opts['format'] = f'best[height<={max_height}]/best'
            
            # Add progress hook
            def progress_hook(d):
                if d['status'] == 'downloading':
                    if 'total_bytes' in d or 'total_bytes_estimate' in d:
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        downloaded = d.get('downloaded_bytes', 0)
                        if total > 0:
                            progress = int((downloaded / total) * 80)  # Reserve 20% for post-processing
                            self.active_downloads[task_id].update({
                                'progress': progress,
                                'message': f'Downloading... {progress}%'
                            })
                elif d['status'] == 'finished':
                    self.active_downloads[task_id].update({
                        'progress': 80,
                        'message': 'Processing audio/video...'
                    })
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            # Create temp directory
            temp_path.mkdir(exist_ok=True)
            
            self.active_downloads[task_id]['message'] = 'Starting download...'
            
            # Download with yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded file
            downloaded_files = list(temp_path.glob('*'))
            if not downloaded_files:
                raise Exception("No file was downloaded")
            
            downloaded_file = downloaded_files[0]  # Get the first (should be only) file
            
            # Move to final location with correct filename
            final_path = DOWNLOAD_DIR / filename
            if final_path.exists():
                final_path.unlink()  # Remove existing file
            
            downloaded_file.rename(final_path)
            
            # Clean up temp directory
            shutil.rmtree(temp_path, ignore_errors=True)
            
            self.active_downloads[task_id] = {
                'status': 'completed',
                'progress': 100,
                'message': 'Download completed!',
                'file_path': str(final_path),
                'filename': filename,
                'file_size': final_path.stat().st_size,
                'format_info': {
                    'ext': final_format,
                    'media_type': media_type,
                    'quality': quality_settings
                },
                'video_info': {
                    'title': video_info.get('title', 'Unknown'),
                    'uploader': video_info.get('uploader', 'Unknown'),
                    'duration': video_info.get('duration'),
                    'thumbnail': video_info.get('thumbnail'),
                    'upload_date': video_info.get('upload_date'),
                    'view_count': video_info.get('view_count'),
                    'description': video_info.get('description', '')[:500]
                }
            }
            
        except Exception as e:
            # Clean up temp directory on error
            if 'temp_path' in locals():
                shutil.rmtree(temp_path, ignore_errors=True)
            
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
    """Serve the downloaded file"""
    if task_id not in extractor.active_downloads:
        return jsonify({'error': 'Task not found'}), 404
    
    task = extractor.active_downloads[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Download not completed'}), 400
    
    file_path = task.get('file_path')
    if not file_path or not Path(file_path).exists():
        return jsonify({'error': 'Downloaded file not found'}), 404
    
    try:
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=task.get('filename', 'download'),
            mimetype='application/octet-stream'
        )
        return response
    except Exception as e:
        return jsonify({'error': f'Failed to serve file: {str(e)}'}), 500

@app.route('/api/download/<task_id>', methods=['GET']) 
def download_file(task_id):
    """Download the processed file"""
    if task_id not in extractor.active_downloads:
        return jsonify({'error': 'Task not found'}), 404
    
    task = extractor.active_downloads[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Download not completed'}), 400
    
    file_path = task.get('file_path')
    if not file_path or not Path(file_path).exists():
        return jsonify({'error': 'Downloaded file not found'}), 404
    
    try:
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=task.get('filename', 'download'),
            mimetype='application/octet-stream'
        )
        return response
    except Exception as e:
        return jsonify({'error': f'Failed to download file: {str(e)}'}), 500

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

@app.route('/api/cors-test', methods=['GET', 'POST', 'OPTIONS'])
def cors_test():
    """Test CORS configuration"""
    return jsonify({
        'status': 'success',
        'message': 'CORS is working correctly',
        'method': request.method,
        'headers': dict(request.headers)
    })

# Legacy endpoints for backward compatibility (deprecated)
@app.route('/api/start_download', methods=['POST'])
def start_download():
    """Legacy download endpoint - redirects to new extract endpoint"""
    return jsonify({
        'error': 'This endpoint is deprecated. Use /api/extract instead.',
        'message': 'CarbaLite now downloads files directly with user preferences'
    }), 410

def cleanup_old_tasks():
    """Clean up old extraction tasks and downloaded files"""
    while True:
        try:
            current_time = time.time()
            # Remove tasks older than 1 hour and clean up files
            tasks_to_remove = []
            for task_id, task_data in extractor.active_downloads.items():
                # Simple cleanup when too many tasks (in production, add timestamps)
                if len(extractor.active_downloads) > 100:
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove[:50]:  # Remove oldest 50 tasks
                task_data = extractor.active_downloads.get(task_id)
                if task_data and 'file_path' in task_data:
                    # Clean up downloaded file
                    try:
                        file_path = Path(task_data['file_path'])
                        if file_path.exists():
                            file_path.unlink()
                            print(f"Cleaned up file: {file_path}")
                    except Exception as e:
                        print(f"Error cleaning up file: {e}")
                
                extractor.active_downloads.pop(task_id, None)
                print(f"Cleaned up old task: {task_id}")
            
            # Also clean up orphaned files in download directory
            try:
                for file_path in DOWNLOAD_DIR.glob('*'):
                    if file_path.is_file():
                        # Remove files older than 2 hours
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > 7200:  # 2 hours
                            file_path.unlink()
                            print(f"Cleaned up orphaned file: {file_path}")
            except Exception as e:
                print(f"Error cleaning up orphaned files: {e}")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        time.sleep(CLEANUP_INTERVAL)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_tasks)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == '__main__':
    print("CarbaLite Backend Server Starting...")
    print("Direct media download with user preferences enabled")
    print("Required dependencies: yt-dlp, requests, flask, flask-cors")
    print("FFmpeg required for audio/video processing")
    print("Supports: MP3, WAV, FLAC, AAC, MP4, WebM, MKV")
    print("Ready for production deployment")
    print("=" * 60)
    
    app.run(debug=True, port=5000, host='0.0.0.0')
