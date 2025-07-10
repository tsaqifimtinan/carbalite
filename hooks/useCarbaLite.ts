import { useState, useCallback } from 'react';

// Types for the hook
export interface VideoInfo {
  title: string;
  uploader: string;
  duration?: number;
  view_count?: number;
}

export interface DownloadStatus {
  stage: 'idle' | 'validating' | 'extracting' | 'downloading' | 'converting' | 'completed' | 'error';
  message: string;
  progress: number;
  videoInfo?: VideoInfo;
  error?: string;
}

export interface ProcessMediaOptions {
  type: 'audio' | 'video';
  audioQuality: '128k' | '256k' | '320k';
  videoQuality: '480p' | '720p' | '1080p';
  preferences: {
    selectedAudioFormat: string;
    selectedVideoFormat: string;
    audioQuality: string;
    videoQuality: string;
  };
}

// CarbaLite Client class (adapted from frontend-integration-example.js)
class CarbaLiteClient {
  private backendUrl: string;

  constructor(backendUrl = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:5000') {
    this.backendUrl = backendUrl;
  }

  async validateUrl(url: string): Promise<any> {
    const response = await fetch(`${this.backendUrl}/validate`, {
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

  async extractMedia(url: string, options: ProcessMediaOptions): Promise<any> {
    const response = await fetch(`${this.backendUrl}/extract`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url,
        type: options.type,
        preferences: options.preferences
      })
    });
    
    if (!response.ok) {
      throw new Error(`Extraction failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async getStatus(taskId: string): Promise<any> {
    const response = await fetch(`${this.backendUrl}/status/${taskId}`);
    
    if (!response.ok) {
      throw new Error(`Status check failed: ${response.statusText}`);
    }
    
    return await response.json();
  }

  async downloadFile(taskId: string): Promise<ArrayBuffer> {
    const response = await fetch(`${this.backendUrl}/download/${taskId}`);
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }
    
    return await response.arrayBuffer();
  }

  downloadBlob(data: ArrayBuffer, filename: string): void {
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

  generateFilename(title: string, type: 'audio' | 'video'): string {
    const cleanTitle = title.replace(/[<>:"/\\|?*]/g, '').substring(0, 100);
    const extension = type === 'audio' ? 'mp3' : 'mp4';
    return `${cleanTitle}.${extension}`;
  }
}

const useCarbaLite = () => {
  const [status, setStatus] = useState<DownloadStatus>({
    stage: 'idle',
    message: 'Ready to download',
    progress: 0
  });

  const client = new CarbaLiteClient();

  const updateStatus = useCallback((newStatus: Partial<DownloadStatus>) => {
    setStatus(prev => ({ ...prev, ...newStatus }));
  }, []);

  const reset = useCallback(() => {
    setStatus({
      stage: 'idle',
      message: 'Ready to download',
      progress: 0
    });
  }, []);

  const processMedia = useCallback(async (url: string, options: ProcessMediaOptions) => {
    try {
      // Step 1: Validate URL
      updateStatus({
        stage: 'validating',
        message: 'Validating URL...',
        progress: 10
      });

      const validation = await client.validateUrl(url);
      
      updateStatus({
        stage: 'extracting',
        message: 'Extracting media information...',
        progress: 20,
        videoInfo: validation.video_info
      });

      // Step 2: Start extraction
      const extraction = await client.extractMedia(url, options);
      const taskId = extraction.task_id;

      updateStatus({
        stage: 'extracting',
        message: 'Processing media...',
        progress: 30
      });

      // Step 3: Poll for completion
      let extractionComplete = false;
      while (!extractionComplete) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        try {
          const statusResponse = await client.getStatus(taskId);
          
          updateStatus({
            stage: 'extracting',
            message: statusResponse.message || 'Processing...',
            progress: Math.min(statusResponse.progress || 30, 80)
          });

          if (statusResponse.status === 'completed') {
            extractionComplete = true;
            
            updateStatus({
              stage: 'downloading',
              message: 'Downloading file...',
              progress: 90
            });

            // Step 4: Download the file
            const fileData = await client.downloadFile(taskId);
            const filename = client.generateFilename(
              validation.video_info.title, 
              options.type
            );

            // Step 5: Trigger download
            client.downloadBlob(fileData, filename);

            updateStatus({
              stage: 'completed',
              message: 'Download completed successfully!',
              progress: 100
            });

          } else if (statusResponse.status === 'error') {
            throw new Error(statusResponse.message || 'Extraction failed');
          }
        } catch (statusError) {
          console.error('Status check error:', statusError);
          // Continue polling, might be a temporary network issue
        }
      }

    } catch (error: any) {
      console.error('Process media error:', error);
      updateStatus({
        stage: 'error',
        message: error.message || 'An error occurred during processing',
        progress: 0,
        error: error.message
      });
      throw error;
    }
  }, [updateStatus]);

  return {
    status,
    processMedia,
    reset
  };
};

export default useCarbaLite;
