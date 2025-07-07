// CarbaLite Frontend Integration Example
// This shows how to integrate the new client-side processing backend

import { createFFmpeg, fetchFile } from '@ffmpeg/ffmpeg';

class CarbaLiteClient {
  constructor(backendUrl = 'http://localhost:5000') {
    this.backendUrl = backendUrl;
    this.ffmpeg = null;
    this.isFFmpegLoaded = false;
  }

  async initFFmpeg() {
    if (this.isFFmpegLoaded) return;
    
    this.ffmpeg = createFFmpeg({
      log: true,
      corePath: 'https://unpkg.com/@ffmpeg/core@0.12.2/dist/ffmpeg-core.js'
    });
    
    await this.ffmpeg.load();
    this.isFFmpegLoaded = true;
    console.log('FFmpeg loaded successfully');
  }

  async validateUrl(url) {
    const response = await fetch(`${this.backendUrl}/api/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url })
    });
    
    if (!response.ok) {
      throw new Error(`Validation failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async extractMedia(url, type = 'audio', formatId = null) {
    const response = await fetch(`${this.backendUrl}/api/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url,
        type,
        format_id: formatId
      })
    });
    
    if (!response.ok) {
      throw new Error(`Extraction failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async getStatus(taskId) {
    const response = await fetch(`${this.backendUrl}/api/status/${taskId}`);
    
    if (!response.ok) {
      throw new Error(`Status check failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async waitForExtraction(taskId, onProgress = null) {
    while (true) {
      const status = await this.getStatus(taskId);
      
      if (onProgress) {
        onProgress(status);
      }
      
      if (status.status === 'completed') {
        return status;
      } else if (status.status === 'error') {
        throw new Error(status.message);
      }
      
      // Wait 1 second before checking again
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  async downloadRawMedia(taskId) {
    const response = await fetch(`${this.backendUrl}/api/stream/${taskId}`);
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }
    
    return await response.arrayBuffer();
  }

  async convertToMp3(audioData, quality = '320k', onProgress = null) {
    if (!this.isFFmpegLoaded) {
      await this.initFFmpeg();
    }

    // Generate unique filenames
    const inputFile = `input_${Date.now()}.webm`;
    const outputFile = `output_${Date.now()}.mp3`;

    try {
      // Write input file
      this.ffmpeg.FS('writeFile', inputFile, new Uint8Array(audioData));

      // Set up progress tracking
      if (onProgress) {
        this.ffmpeg.setProgress(({ ratio }) => {
          onProgress(Math.round(ratio * 100));
        });
      }

      // Convert to MP3
      await this.ffmpeg.run(
        '-i', inputFile,
        '-acodec', 'libmp3lame',
        '-b:a', quality,
        '-metadata', 'title=CarbaLite Download',
        outputFile
      );

      // Read output file
      const data = this.ffmpeg.FS('readFile', outputFile);

      // Clean up
      this.ffmpeg.FS('unlink', inputFile);
      this.ffmpeg.FS('unlink', outputFile);

      return data.buffer;
    } catch (error) {
      // Clean up on error
      try {
        this.ffmpeg.FS('unlink', inputFile);
        this.ffmpeg.FS('unlink', outputFile);
      } catch (cleanupError) {
        // Ignore cleanup errors
      }
      throw error;
    }
  }

  async convertToMp4(videoData, quality = '720p', onProgress = null) {
    if (!this.isFFmpegLoaded) {
      await this.initFFmpeg();
    }

    const inputFile = `input_${Date.now()}.webm`;
    const outputFile = `output_${Date.now()}.mp4`;

    try {
      this.ffmpeg.FS('writeFile', inputFile, new Uint8Array(videoData));

      if (onProgress) {
        this.ffmpeg.setProgress(({ ratio }) => {
          onProgress(Math.round(ratio * 100));
        });
      }

      // Convert to MP4 with quality settings
      const scaleFilter = quality === '1080p' ? 'scale=1920:1080' : 
                         quality === '720p' ? 'scale=1280:720' : 
                         'scale=854:480';

      await this.ffmpeg.run(
        '-i', inputFile,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-vf', scaleFilter,
        '-crf', '23',
        '-preset', 'medium',
        outputFile
      );

      const data = this.ffmpeg.FS('readFile', outputFile);

      // Clean up
      this.ffmpeg.FS('unlink', inputFile);
      this.ffmpeg.FS('unlink', outputFile);

      return data.buffer;
    } catch (error) {
      try {
        this.ffmpeg.FS('unlink', inputFile);
        this.ffmpeg.FS('unlink', outputFile);
      } catch (cleanupError) {
        // Ignore cleanup errors
      }
      throw error;
    }
  }

  async downloadMedia(url, options = {}) {
    const {
      type = 'audio',
      quality = type === 'audio' ? '320k' : '720p',
      onValidation = null,
      onExtraction = null,
      onDownload = null,
      onConversion = null
    } = options;

    try {
      // Step 1: Validate URL
      if (onValidation) onValidation({ status: 'validating' });
      const validation = await this.validateUrl(url);
      if (onValidation) onValidation({ status: 'validated', data: validation });

      // Step 2: Extract media stream
      if (onExtraction) onExtraction({ status: 'extracting' });
      const extraction = await this.extractMedia(url, type);
      
      // Wait for extraction to complete
      const result = await this.waitForExtraction(
        extraction.task_id,
        (status) => {
          if (onExtraction) onExtraction(status);
        }
      );

      // Step 3: Download raw media
      if (onDownload) onDownload({ status: 'downloading' });
      const rawMedia = await this.downloadRawMedia(extraction.task_id);
      if (onDownload) onDownload({ status: 'downloaded', size: rawMedia.byteLength });

      // Step 4: Convert with ffmpeg.wasm
      if (onConversion) onConversion({ status: 'converting' });
      
      let convertedMedia;
      if (type === 'audio') {
        convertedMedia = await this.convertToMp3(rawMedia, quality, (progress) => {
          if (onConversion) onConversion({ status: 'converting', progress });
        });
      } else {
        convertedMedia = await this.convertToMp4(rawMedia, quality, (progress) => {
          if (onConversion) onConversion({ status: 'converting', progress });
        });
      }

      if (onConversion) onConversion({ status: 'completed' });

      return {
        data: convertedMedia,
        filename: this.generateFilename(result.video_info.title, type),
        videoInfo: result.video_info
      };

    } catch (error) {
      console.error('Download failed:', error);
      throw error;
    }
  }

  generateFilename(title, type) {
    const cleanTitle = title.replace(/[<>:"/\\|?*]/g, '').substring(0, 100);
    const extension = type === 'audio' ? 'mp3' : 'mp4';
    return `${cleanTitle}.${extension}`;
  }

  downloadBlob(data, filename) {
    const blob = new Blob([data], { 
      type: filename.endsWith('.mp3') ? 'audio/mpeg' : 'video/mp4' 
    });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

// Usage Example
export default CarbaLiteClient;

// Example usage:
/*
const client = new CarbaLiteClient('http://localhost:5000');

// Download audio
client.downloadMedia('https://www.youtube.com/watch?v=dQw4w9WgXcQ', {
  type: 'audio',
  quality: '320k',
  onValidation: (status) => console.log('Validation:', status),
  onExtraction: (status) => console.log('Extraction:', status),
  onDownload: (status) => console.log('Download:', status),
  onConversion: (status) => console.log('Conversion:', status)
})
.then(result => {
  console.log('Download completed:', result.filename);
  client.downloadBlob(result.data, result.filename);
})
.catch(error => {
  console.error('Download failed:', error);
});
*/
