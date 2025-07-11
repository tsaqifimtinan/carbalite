"use client";

import React from "react";
import Link from "next/link";

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white">
      {/* Header */}
      <header className="bg-white dark:bg-black border-b border-gray-200 dark:border-gray-800 h-16 flex items-center px-4 sticky top-0 z-30">
        <Link 
          href="/"
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md mr-2 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
        </Link>
        <h1 className="text-xl font-bold tracking-tight">carbalite.</h1>
        
        {/* Dark mode toggle placeholder */}
        <div className="ml-auto">
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </button>
        </div>
      </header>

      {/* Main content */}
      <main className="p-6 max-w-4xl mx-auto">
        <div className="animate-fade-in">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-6xl font-bold mb-4">
              About carbalite.
            </h1>
          </div>

          <div className="max-w-3xl mx-auto space-y-8">
            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-8 border border-gray-200 dark:border-gray-800">
              <h2 className="text-2xl font-bold mb-4">What is carbalite?</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                carbalite is a modern web-based tool for downloading and converting media content from popular platforms 
                like YouTube and SoundCloud. Built with cutting-edge web technologies, it provides high-quality downloads 
                while maintaining your privacy and security.
              </p>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-8 border border-gray-200 dark:border-gray-800">
              <h2 className="text-2xl font-bold mb-4">carbalite ethics</h2>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                carbalite is a utility designed to simplify the process of downloading freely available online content. 
                It does not store or cache any data, acting solely as a dynamic passthrough — much like an advanced browser proxy. Users 
                are fully responsible for what they choose to access, download, and share through the tool.
                
                carbalite is not intended for piracy and cannot be used to obtain paid or restricted materials. 
                It only facilitates the downloading of open, publicly accessible content — 
                the same kind of content that can be retrieved through the developer tools of any standard web browser.
              </p>
            </div>

            <div className="text-center">
              <p className="text-gray-500 dark:text-gray-400">
                Version 1.0.1 • Built with ❤️ using Next.js and Python/Flask
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
