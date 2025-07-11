"use client";

import React, { useState } from "react";
import Link from "next/link";
import useCarbaLite from "../hooks/useCarbaLite";
import usePreferences from "../hooks/usePreferences";

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState("save");
  const [url, setUrl] = useState("");

  const { status, processMedia, reset } = useCarbaLite();
  const { 
    preferences, 
    isLoaded: preferencesLoaded,
    setSelectedVideoFormat,
    setSelectedAudioFormat, 
    setVideoQuality, 
    setAudioQuality,
    resetPreferences 
  } = usePreferences();

  const { selectedVideoFormat, selectedAudioFormat, videoQuality, audioQuality } = preferences;

  const videoFormats = ["mp4", "avi", "mov", "mkv", "webm", "flv"];
  const audioFormats = ["mp3", "wav", "flac", "aac", "ogg", "m4a"];

  const menuItems = [
    {
      category: "Download",
      items: [
        { name: "Save", href: "#", active: currentPage === "save", onClick: () => setCurrentPage("save") },
      ]
    },
    {
      category: "Settings",
      items: [
        { name: "Preferences", href: "#", active: currentPage === "preferences", onClick: () => setCurrentPage("preferences") },
      ]
    },
    {
      category: "Info",
      items: [
        { name: "About", href: "/about", active: false, onClick: null },
      ]
    }
  ];

  const isValidUrl = (url: string) => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)\/(watch\?v=|embed\/|v\/|.+\?v=)?([^&=%\?]{11})/;
    const soundcloudRegex = /^(https?:\/\/)?(www\.)?soundcloud\.com\/[\w\-\.]+/;
    return youtubeRegex.test(url) || soundcloudRegex.test(url);
  };

  const handleUrlSubmit = async (type: 'audio' | 'video') => {
    if (!url.trim()) {
      alert("Please enter a valid URL");
      return;
    }

    if (!isValidUrl(url)) {
      alert("Please enter a valid YouTube or SoundCloud URL");
      return;
    }

    try {
      reset(); // Reset any previous status
      
      const options = {
        type,
        audioQuality: audioQuality as '128k' | '256k' | '320k',
        videoQuality: videoQuality as '480p' | '720p' | '1080p',
        preferences: {
          selectedAudioFormat,
          selectedVideoFormat,
          audioQuality,
          videoQuality
        }
      };

      await processMedia(url, options);
      
    } catch (error) {
      console.error("Error processing URL:", error);
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";
      alert(`Error: ${errorMessage}`);
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white flex">
      {/* Sidebar */}
      <div className={`w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-transform duration-300 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:static inset-y-0 left-0 z-50 lg:z-auto`}>
        <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 dark:border-gray-800">
          <h1 className="text-xl font-extrabold tracking-tight">carbalite.</h1>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <nav className="p-4 space-y-6">
          {menuItems.map((section, sectionIndex) => (
            <div key={sectionIndex} className="space-y-2">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                {section.category}
              </h3>
              <div className="space-y-1">
                {section.items.map((item, itemIndex) => (
                  item.href === "/about" ? (
                    <Link
                      key={itemIndex}
                      href={item.href}
                      className={`w-full text-left block px-3 py-2 rounded-md text-sm transition-colors ${
                        item.active
                          ? 'bg-black dark:bg-white text-white dark:text-black font-medium'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-black dark:hover:text-white'
                      }`}
                    >
                      {item.name}
                    </Link>
                  ) : (
                    <button
                      key={itemIndex}
                      onClick={item.onClick!}
                      className={`w-full text-left block px-3 py-2 rounded-md text-sm transition-colors ${
                        item.active
                          ? 'bg-black dark:bg-white text-white dark:text-black font-medium'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-black dark:hover:text-white'
                      }`}
                    >
                      {item.name}
                    </button>
                  )
                ))}
              </div>
            </div>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="absolute bottom-0 w-full p-4 border-t border-gray-200 dark:border-gray-800">
          <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
            Powered by FFmpeg.wasm
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white dark:bg-black border-b border-gray-200 dark:border-gray-800 h-16 flex items-center px-4 sticky top-0 z-30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md mr-2 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h2 className="text-lg font-bold">
            {currentPage === "save" ? "Save Content" : "Preferences"}
          </h2>
          
          {/* Dark mode toggle placeholder */}
          <div className="ml-auto">
            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </button>
          </div>
        </header>

        {/* Main content area */}
        <main className="p-6 max-w-4xl mx-auto">
          {currentPage === "save" && (
            <div className="animate-fade-in">
              {/* Hero section */}
              <div className="text-center mb-12">
                <h1 className="text-4xl md:text-6xl font-extrabold mb-4">
                  Save Content
                </h1>
                <p className="text-lg md:text-xl text-gray-600 dark:text-gray-400 mb-8 font-medium">
                  Download and convert YouTube videos and SoundCloud tracks using client-side processing
                </p>
              </div>

              {/* URL Input area */}
              <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-8 md:p-12 border border-gray-200 dark:border-gray-800 mb-8">
                <div className="space-y-6">
                  <div className="mx-auto w-20 h-20 flex items-center justify-center mb-6">
                    <div className="vinyl-record animate-vinyl-spin">
                      <div className="vinyl-label">♪</div>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <h3 className="text-xl font-bold mb-2">Enter YouTube or SoundCloud URL</h3>
                  </div>

                  <div className="max-w-2xl mx-auto">
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="Paste the link here..."
                      className="w-full px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-black text-black dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-black dark:focus:ring-white focus:border-transparent"
                      disabled={status.stage !== 'idle' && status.stage !== 'completed' && status.stage !== 'error'}
                    />
                  </div>

                  <div className="flex gap-4 justify-center">
                    <button
                      onClick={() => handleUrlSubmit('audio')}
                      disabled={status.stage !== 'idle' && status.stage !== 'completed' && status.stage !== 'error' || !url.trim()}
                      className="bg-black dark:bg-white text-white dark:text-black px-8 py-3 rounded-lg hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {status.stage !== 'idle' && status.stage !== 'completed' && status.stage !== 'error' ? (
                        <svg className="animate-spin w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                        </svg>
                      )}
                      Download Audio
                    </button>
                    
                    <button
                      onClick={() => handleUrlSubmit('video')}
                      disabled={status.stage !== 'idle' && status.stage !== 'completed' && status.stage !== 'error' || !url.trim()}
                      className="bg-gray-100 dark:bg-gray-800 text-black dark:text-white px-8 py-3 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors font-bold disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {status.stage !== 'idle' && status.stage !== 'completed' && status.stage !== 'error' ? (
                        <svg className="animate-spin w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      ) : (
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      )}
                      Download Video
                    </button>
                  </div>

                  {(status.stage !== 'idle' && status.stage !== 'completed') && (
                    <div className="max-w-2xl mx-auto">
                      <div className="bg-white dark:bg-black border border-gray-300 dark:border-gray-600 rounded-lg p-4">
                        <div className="flex items-center gap-3 mb-3">
                          <svg className="animate-spin w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          <span className="text-sm font-bold">{status.message}</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div 
                            className="bg-black dark:bg-white h-2 rounded-full transition-all duration-300"
                            style={{ width: `${status.progress}%` }}
                          ></div>
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center font-medium">
                          {Math.round(status.progress)}% complete
                        </div>
                        {status.videoInfo && (
                          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                            <div className="text-sm">
                              <div className="font-bold truncate">{status.videoInfo.title}</div>
                              <div className="text-gray-500 dark:text-gray-400 text-xs font-medium">{status.videoInfo.uploader}</div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="text-center text-sm text-gray-500 dark:text-gray-400 font-medium">
                    <p>Supported platforms: YouTube, SoundCloud</p>
                    <p>Audio quality: Up to 320kbps | Video quality: Up to 1080p</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {currentPage === "preferences" && (
            <div className="animate-fade-in">
              {!preferencesLoaded ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <svg className="animate-spin w-8 h-8 mx-auto mb-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <p className="text-gray-500 dark:text-gray-400">Loading preferences...</p>
                  </div>
                </div>
              ) : (
                <>
              <div className="text-center mb-12">
                <h1 className="text-4xl md:text-6xl font-extrabold mb-4">
                  Preferences
                </h1>
                <p className="text-lg md:text-xl text-gray-600 dark:text-gray-400 mb-8 font-medium">
                  Configure your download and conversion settings
                </p>
              </div>

              {/* Format selection */}
              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800">
                  <h3 className="font-bold mb-4 flex items-center">
                    <div className="w-8 h-8 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center mr-3">
                      <svg className="w-4 h-4 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </div>
                    Video Formats
                  </h3>
                  <div className="grid grid-cols-3 gap-2">
                    {videoFormats.map((format) => (
                      <button
                        key={format}
                        onClick={() => setSelectedVideoFormat(format)}
                        className={`p-2 rounded-md text-sm font-mono transition-colors ${
                          selectedVideoFormat === format
                            ? 'bg-black dark:bg-white text-white dark:text-black'
                            : 'bg-white dark:bg-black border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800'
                        }`}
                      >
                        {format.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800">
                  <h3 className="font-bold mb-4 flex items-center">
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mr-3">
                      <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                      </svg>
                    </div>
                    Audio Formats
                  </h3>
                  <div className="grid grid-cols-3 gap-2">
                    {audioFormats.map((format) => (
                      <button
                        key={format}
                        onClick={() => setSelectedAudioFormat(format)}
                        className={`p-2 rounded-md text-sm font-mono transition-colors ${
                          selectedAudioFormat === format
                            ? 'bg-black dark:bg-white text-white dark:text-black'
                            : 'bg-white dark:bg-black border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800'
                        }`}
                      >
                        {format.toUpperCase()}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-6 border border-gray-200 dark:border-gray-800">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="font-bold">Quality Settings</h3>
                  <div className="flex gap-2">
                    <button
                      onClick={resetPreferences}
                      className="text-xs px-3 py-1 rounded-md bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                    >
                      Reset to Defaults
                    </button>
                    {preferencesLoaded && (
                      <div className="text-xs px-3 py-1 rounded-md bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400">
                        Saved ✓
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Current Selection Summary */}
                <div className="mb-6 p-4 bg-white dark:bg-black rounded-lg border border-gray-200 dark:border-gray-700">
                  <h4 className="text-sm font-bold mb-2">Current Selections</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400 font-medium">Video:</span>
                      <span className="ml-2 font-mono font-bold">{selectedVideoFormat.toUpperCase()}</span>
                      <span className="ml-1 text-gray-500 dark:text-gray-400 font-medium">@ {videoQuality}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400 font-medium">Audio:</span>
                      <span className="ml-2 font-mono font-bold">{selectedAudioFormat.toUpperCase()}</span>
                      <span className="ml-1 text-gray-500 dark:text-gray-400 font-medium">@ {audioQuality}</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-bold mb-2">Video Quality</label>
                    <select 
                      value={videoQuality}
                      onChange={(e) => setVideoQuality(e.target.value as '480p' | '720p' | '1080p')}
                      className="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-black text-black dark:text-white"
                    >
                      <option value="1080p">1080p (High)</option>
                      <option value="720p">720p (Medium)</option>
                      <option value="480p">480p (Low)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-bold mb-2">Audio Quality</label>
                    <select 
                      value={audioQuality}
                      onChange={(e) => setAudioQuality(e.target.value as '128k' | '256k' | '320k')}
                      className="w-full px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-black text-black dark:text-white"
                    >
                      <option value="320k">320 kbps (High)</option>
                      <option value="256k">256 kbps (Medium)</option>
                      <option value="128k">128 kbps (Low)</option>
                    </select>
                  </div>
                </div>
                
                <div className="text-xs text-gray-500 dark:text-gray-400 mb-4 text-center font-medium">
                  Your preferences are automatically saved and will be remembered for future visits
                </div>
              </div>
                </>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
