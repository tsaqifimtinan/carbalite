@echo off
echo ===============================================
echo        CarbaLite Backend Installation
echo ===============================================
echo.

echo Installing Python dependencies...
python -m pip install --user flask flask-cors yt-dlp mutagen requests

if %errorlevel% == 0 (
    echo.
    echo ✓ Installation completed successfully!
    echo.
    echo To start the backend server, run:
    echo   python app.py
    echo.
) else (
    echo.
    echo ❌ Installation failed. Trying alternative method...
    echo.
    python -m pip install flask flask-cors yt-dlp mutagen requests
    
    if %errorlevel% == 0 (
        echo ✓ Installation completed successfully!
    ) else (
        echo ❌ Installation failed. Please try:
        echo   1. Run this script as administrator
        echo   2. Or create a virtual environment:
        echo      python -m venv venv
        echo      venv\Scripts\activate
        echo      pip install -r requirements.txt
    )
)

echo.
echo Press any key to continue...
pause >nul
