@echo off
echo ===============================================
echo            CarbaLite Startup Script
echo ===============================================
echo.

echo Checking if backend is already running...
netstat -an | find "5000" | find "LISTENING" >nul
if %errorlevel% == 0 (
    echo Backend is already running on port 5000
) else (
    echo Starting backend server...
    start cmd /k "cd backend && python app.py"
    timeout /t 3 >nul
)

echo.
echo Starting frontend development server...
start cmd /k "npm run dev"

echo.
echo ===============================================
echo  Both servers are starting up!
echo  
echo  Frontend: http://localhost:3000
echo  Backend:  http://localhost:5000
echo ===============================================
echo.
echo Press any key to exit...
pause >nul
