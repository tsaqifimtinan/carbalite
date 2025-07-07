'use client';

import dynamic from 'next/dynamic';
import { ComponentType } from 'react';

// Dynamically import the main page component with no SSR
const HomePage: ComponentType<any> = dynamic(
  () => import('./HomePage'),
  { 
    ssr: false,
    loading: () => (
      <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-black dark:border-white border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Loading CarbaLite...</p>
        </div>
      </div>
    )
  }
);

export default HomePage;
