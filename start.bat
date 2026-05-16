@echo off
echo ========================================
echo ContribFlow - Starting Application
echo ========================================
echo.

echo [1/3] Starting FastAPI Backend...
start "ContribFlow Backend" cmd /k "uvicorn main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

echo [2/3] Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo [3/3] Starting Streamlit Frontend...
start "ContribFlow Frontend" cmd /k "python -m streamlit run app.py"

echo.
echo ========================================
echo ContribFlow is starting!
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:8501
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit this window...
pause >nul

@REM Made with Bob
