"""
Setup script for CarbaLite Backend
This script helps set up the Python environment for client-side media processing
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    return True

def install_requirements():
    """Install Python requirements"""
    print("📦 Installing Python dependencies...")
    try:
        # Try with --user flag first to avoid permission issues
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "-r", "requirements.txt"])
        print("✓ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Python dependencies: {e}")
        print("💡 Trying alternative installation method...")
        try:
            # Alternative: Try without --user flag (in case of virtual environment)
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✓ Python dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"❌ Alternative installation also failed: {e2}")
            print("\n🔧 Manual installation options:")
            print("   1. Run as administrator: Right-click Command Prompt -> 'Run as administrator'")
            print("   2. Use virtual environment:")
            print("      python -m venv venv")
            print("      venv\\Scripts\\activate")
            print("      pip install -r requirements.txt")
            print("   3. Install manually:")
            print("      pip install --user flask flask-cors yt-dlp requests")
            return False

def create_directories():
    """Create necessary directories"""
    dirs = ['logs']  # Removed downloads dir as we no longer store files
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        print(f"✓ Created directory: {dir_name}")

def main():
    """Main setup function"""
    print("🎵 CarbaLite Backend Setup (Client-Side Processing)")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install requirements
    if not install_requirements():
        print("\n" + "=" * 50)
        print("⚠️  Automatic installation failed!")
        print("Please try manual installation:")
        print("\n📋 Manual Installation Commands:")
        print("pip install --user flask flask-cors yt-dlp requests")
        print("\nOr run the install.bat script as administrator")
        print("Or see INSTALL.md for more options")
        
        # Ask if user wants to continue anyway
        try:
            response = input("\nContinue with setup anyway? (y/n): ").lower()
            if response != 'y':
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nSetup cancelled.")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("✅ Backend ready for client-side processing")
    
    print("\n🔄 Key Changes in This Version:")
    print("• No server-side ffmpeg required")
    print("• Client-side processing with ffmpeg.wasm")
    print("• Vercel-compatible deployment")
    print("• Reduced server resource usage")
    
    print("\n🚀 To start the backend server, run:")
    print("   python app.py")
    
    print("\n🌐 Endpoints:")
    print("• Backend: http://localhost:5000")
    print("• Frontend: http://localhost:3000")
    
    print("\n📁 Files created:")
    print("- logs/ (for log files)")
    
    print("\n🔗 New API Endpoints:")
    print("• POST /api/validate - Validate URL and get media info")
    print("• POST /api/extract - Extract raw media stream")
    print("• GET /api/status/<task_id> - Check extraction status")
    print("• GET /api/stream/<task_id> - Stream raw media")
    print("• GET /api/thumbnail/<task_id> - Get video thumbnail")
    
    # Test import
    try:
        print("\n🧪 Testing imports...")
        import flask
        print("✓ Flask imported successfully")
        try:
            import yt_dlp
            print("✓ yt-dlp imported successfully")
        except ImportError:
            print("❌ yt-dlp import failed - manual installation needed")
        try:
            import requests
            print("✓ Requests imported successfully")
        except ImportError:
            print("❌ Requests import failed - manual installation needed")
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        print("Please install dependencies manually")
    
    print("\n✨ Ready for deployment on Vercel!")
    print("💡 No server-side ffmpeg dependency means easier deployment")

if __name__ == "__main__":
    main()
