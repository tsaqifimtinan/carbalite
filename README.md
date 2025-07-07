# CarbaLite

A modern, full-stack YouTube and SoundCloud downloader with client-side processing using ffmpeg.wasm. No server-side dependencies, ready for serverless deployment.

## 🎵 Features

- **YouTube & SoundCloud Support**: Download from both platforms seamlessly
- **Client-Side Processing**: Uses ffmpeg.wasm for browser-based conversion
- **Multiple Formats**: Audio (MP3) and Video (MP4, WebM, etc.)
- **Quality Options**: Choose from different quality settings (320kbps audio, 1080p video)
- **Real-time Progress**: Live extraction and conversion progress tracking
- **Modern UI**: Clean, responsive black-and-white design
- **Serverless Ready**: Compatible with Vercel and other platforms
- **No Server Dependencies**: No ffmpeg installation required on server

## 🏗️ Architecture

- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, and ffmpeg.wasm
- **Backend**: Python Flask with yt-dlp for stream extraction
- **Processing**: Client-side conversion with WebAssembly
- **Deployment**: Vercel-compatible serverless functions

## 🚀 Quick Start

### Prerequisites

1. **Node.js 18+** for the frontend
2. **Python 3.8+** for the backend
3. **Modern browser** with WebAssembly support

### Installation & Development

```bash
# Clone the repository
git clone <repository-url>
cd carbalite

# Install dependencies and setup backend
npm run setup

# Start both frontend and backend simultaneously
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

### Available Scripts

- `npm run dev` - Start both frontend and backend
- `npm run frontend` - Start only Next.js frontend
- `npm run backend` - Start only Python backend
- `npm run setup` - Install all dependencies
- `npm run build` - Build for production
- `npm run start:prod` - Start production servers

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd carbalite
   ```

2. **Setup Frontend:**
   ```bash
   npm install
   ```

3. **Setup Backend:**
   ```bash
   cd backend
   python setup.py
   ```

### Running the Application

1. **Start the backend server:**
   ```bash
   cd backend
   python app.py
   ```
   Backend will be available at `http://localhost:5000`

2. **Start the frontend (in a new terminal):**
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000`

## 📱 Usage

1. **Navigate to the Save page** (default)
2. **Paste a YouTube or SoundCloud URL**
3. **Choose Audio or Video download**
4. **Configure quality in Preferences** (optional)
5. **Click Download** and wait for completion
6. **File will automatically download** to your device

## 🛠️ Development

### Frontend Structure
```
app/
├── page.tsx          # Main application component
├── layout.tsx        # Root layout
├── globals.css       # Global styles
└── favicon.ico       # App icon
```

### Backend Structure
```
backend/
├── app.py            # Flask application
├── setup.py          # Setup script
├── requirements.txt  # Python dependencies
└── README.md         # Backend documentation
```

### Key Technologies

**Frontend:**
- Next.js 15 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- React hooks for state management

**Backend:**
- Flask for API endpoints
- yt-dlp for media extraction
- FFmpeg for media processing
- Mutagen for metadata handling

## 🎨 Design Philosophy

- **Minimalist**: Clean black-and-white interface
- **Responsive**: Works on desktop and mobile
- **Intuitive**: Simple navigation with sidebar
- **Fast**: Optimized for performance

## 📋 API Endpoints

- `POST /api/validate` - Validate and get video info
- `POST /api/download` - Start download process
- `GET /api/status/{task_id}` - Check download progress
- `GET /api/download/{task_id}` - Download completed file
- `GET /api/health` - Health check

## ⚡ Performance Features

- **Background Processing**: Downloads run in separate threads
- **Progress Tracking**: Real-time progress updates
- **Auto Cleanup**: Old files are automatically removed
- **Efficient Polling**: Smart status checking

## 🔒 Security & Privacy

- **No Data Storage**: Files are temporarily processed and removed
- **Client-Side Logic**: Minimal data sent to server
- **CORS Enabled**: Secure cross-origin requests
- **Local Processing**: All conversion happens locally

## 🐛 Troubleshooting

### Common Issues

1. **Backend not starting:**
   - Check Python version: `python --version`
   - Install dependencies: `pip install -r backend/requirements.txt`

2. **FFmpeg not found:**
   - Install FFmpeg and add to PATH
   - Test with: `ffmpeg -version`

3. **Download failures:**
   - Check URL validity
   - Some content may be region-locked
   - Update yt-dlp: `pip install --upgrade yt-dlp`

4. **CORS errors:**
   - Ensure backend is running on port 5000
   - Check browser developer tools for errors

## 📝 License

This project is for educational purposes. Please respect copyright laws and platform terms of service when downloading content.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🔮 Future Enhancements

- [ ] Batch downloads
- [ ] Playlist support
- [ ] Additional platforms (Instagram, TikTok)
- [ ] Advanced format conversion
- [ ] Download history
- [ ] Dark/light mode toggle
- [ ] Drag-and-drop URL input
