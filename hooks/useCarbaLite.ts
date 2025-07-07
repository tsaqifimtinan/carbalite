// CarbaLite Client Hook - New API Integration
import { useState, useCallback } from 'react';

interface VideoInfo {
  title: string;
  uploader: string;
  duration: number;
  thumbnail: string;
  upload_date: string;
}

interface ProcessingStatus {
  stage: 'idle' | 'validating' | 'extracting' | 'downloading' | 'converting' | 'completed' | 'error';
  progress: number;
  message: string;
  videoInfo?: VideoInfo;
}

interface ConversionOptions {
  type: 'audio' | 'video';
  audioQuality?: '128k' | '256k' | '320k';
  videoQuality?: '480p' | '720p' | '1080p';
}

export const useCarbaLite = () => {
  const [status, setStatus] = useState<ProcessingStatus>({
    stage: 'idle',
    progress: 0,
    message: ''
  });

  const processMedia = useCallback(async (url: string, options: ConversionOptions) => {
    try {
      // Step 1: Validate URL
      setStatus({
        stage: 'validating',
        progress: 10,
        message: 'Validating URL...'
      });

      const validateResponse = await fetch('http://localhost:5000/api/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!validateResponse.ok) {
        throw new Error('Failed to validate URL');
      }

      const validateData = await validateResponse.json();
      
      setStatus(prev => ({
        ...prev,
        progress: 25,
        message: 'URL validated successfully',
        videoInfo: validateData.info
      }));

      // Step 2: Extract media
      setStatus(prev => ({
        ...prev,
        stage: 'extracting',
        progress: 30,
        message: 'Extracting media information...'
      }));

      const extractResponse = await fetch('http://localhost:5000/api/extract', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          url,
          type: options.type,
          quality: options.type === 'audio' ? options.audioQuality : options.videoQuality
        }),
      });

      if (!extractResponse.ok) {
        throw new Error('Failed to extract media');
      }

      const extractData = await extractResponse.json();
      const taskId = extractData.task_id;

      // Step 3: Poll for status and download
      setStatus(prev => ({
        ...prev,
        stage: 'downloading',
        progress: 50,
        message: 'Preparing download...'
      }));

      // Poll for completion
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await fetch(`http://localhost:5000/api/status/${taskId}`);
          if (!statusResponse.ok) {
            throw new Error('Failed to check status');
          }

          const statusData = await statusResponse.json();

          if (statusData.status === 'completed') {
            clearInterval(pollInterval);
            
            // Download the file
            setStatus(prev => ({
              ...prev,
              progress: 90,
              message: 'Downloading file...'
            }));

            const downloadResponse = await fetch(`http://localhost:5000/api/stream/${taskId}`);
            if (!downloadResponse.ok) {
              throw new Error('Failed to download file');
            }

            const blob = await downloadResponse.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            
            // Use filename from backend if available, otherwise generate one
            const filename = statusData.filename || 
              `${validateData.info.title || 'download'}.${options.type === 'audio' ? 'mp3' : 'mp4'}`;
            link.download = filename;
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

            setStatus({
              stage: 'completed',
              progress: 100,
              message: 'Download completed!',
              videoInfo: validateData.info
            });

          } else if (statusData.status === 'error') {
            clearInterval(pollInterval);
            throw new Error(statusData.message || 'Processing failed');
          } else {
            // Update progress
            setStatus(prev => ({
              ...prev,
              progress: Math.min(85, 50 + (statusData.progress || 0) * 0.35),
              message: statusData.message || 'Processing...'
            }));
          }
        } catch (error) {
          clearInterval(pollInterval);
          throw error;
        }
      }, 2000);

    } catch (error) {
      console.error('Processing error:', error);
      setStatus({
        stage: 'error',
        progress: 0,
        message: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    }
  }, []);

  const reset = useCallback(() => {
    setStatus({
      stage: 'idle',
      progress: 0,
      message: ''
    });
  }, []);

  return {
    status,
    processMedia,
    reset
  };
};

// Default export for compatibility
export default useCarbaLite;
