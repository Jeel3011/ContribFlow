#!/bin/bash

echo "========================================"
echo "ContribFlow - Starting Application"
echo "========================================"
echo ""

echo "[1/3] Starting FastAPI Backend..."
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
sleep 3

echo "[2/3] Waiting for backend to start..."
sleep 5

echo "[3/3] Starting Streamlit Frontend..."
python -m streamlit run app.py &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "ContribFlow is running!"
echo "========================================"
echo ""
echo "Backend API: http://localhost:8000"
echo "Frontend UI: http://localhost:8501"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all services..."

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait

# Made with Bob
