import { useState, useEffect } from 'react';
import Cookies from 'js-cookie';

export interface UserPreferences {
  selectedVideoFormat: string;
  selectedAudioFormat: string;
  videoQuality: '480p' | '720p' | '1080p';
  audioQuality: '128k' | '256k' | '320k';
}

const DEFAULT_PREFERENCES: UserPreferences = {
  selectedVideoFormat: 'mp4',
  selectedAudioFormat: 'mp3',
  videoQuality: '720p',
  audioQuality: '320k',
};

const COOKIE_NAME = 'carbalite_preferences';
const COOKIE_EXPIRY_DAYS = 365; // 1 year

export const usePreferences = () => {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load preferences from cookies on mount
  useEffect(() => {
    try {
      const savedPreferences = Cookies.get(COOKIE_NAME);
      if (savedPreferences) {
        const parsed = JSON.parse(savedPreferences) as UserPreferences;
        // Validate the parsed data to ensure it has all required fields
        const validatedPreferences: UserPreferences = {
          selectedVideoFormat: (parsed as any).selectedVideoFormat || (parsed as any).selectedFormat || DEFAULT_PREFERENCES.selectedVideoFormat,
          selectedAudioFormat: (parsed as any).selectedAudioFormat || DEFAULT_PREFERENCES.selectedAudioFormat,
          videoQuality: ['480p', '720p', '1080p'].includes(parsed.videoQuality) 
            ? parsed.videoQuality 
            : DEFAULT_PREFERENCES.videoQuality,
          audioQuality: ['128k', '256k', '320k'].includes(parsed.audioQuality)
            ? parsed.audioQuality
            : DEFAULT_PREFERENCES.audioQuality,
        };
        setPreferences(validatedPreferences);
      }
    } catch (error) {
      console.warn('Failed to load preferences from cookies:', error);
      // If parsing fails, use defaults
      setPreferences(DEFAULT_PREFERENCES);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  // Save preferences to cookies whenever they change
  const updatePreferences = (newPreferences: Partial<UserPreferences>) => {
    const updatedPreferences = { ...preferences, ...newPreferences };
    setPreferences(updatedPreferences);
    
    try {
      Cookies.set(COOKIE_NAME, JSON.stringify(updatedPreferences), {
        expires: COOKIE_EXPIRY_DAYS,
        sameSite: 'strict',
        secure: process.env.NODE_ENV === 'production',
      });
    } catch (error) {
      console.warn('Failed to save preferences to cookies:', error);
    }
  };

  // Individual setters for convenience
  const setSelectedVideoFormat = (format: string) => {
    updatePreferences({ selectedVideoFormat: format });
  };

  const setSelectedAudioFormat = (format: string) => {
    updatePreferences({ selectedAudioFormat: format });
  };

  const setVideoQuality = (quality: '480p' | '720p' | '1080p') => {
    updatePreferences({ videoQuality: quality });
  };

  const setAudioQuality = (quality: '128k' | '256k' | '320k') => {
    updatePreferences({ audioQuality: quality });
  };

  // Reset to defaults
  const resetPreferences = () => {
    setPreferences(DEFAULT_PREFERENCES);
    try {
      Cookies.remove(COOKIE_NAME);
    } catch (error) {
      console.warn('Failed to remove preferences cookie:', error);
    }
  };

  return {
    preferences,
    isLoaded,
    updatePreferences,
    setSelectedVideoFormat,
    setSelectedAudioFormat,
    setVideoQuality,
    setAudioQuality,
    resetPreferences,
  };
};

export default usePreferences;
