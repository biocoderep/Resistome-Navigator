@echo off
echo ========================================================
echo       AMR Platform Unified Startup Script
echo ========================================================
echo.

:: 1. Start FastAPI Backend
echo [1/4] Starting FastAPI Backend (Port 8000)...
start "FastAPI Backend" cmd /k ""C:\Users\dell2\AppData\Local\Programs\Python\Python313\Scripts\uvicorn.exe" backend.main:app --reload --port 8000"

:: 2. Start Celery Worker
echo [2/4] Starting Celery Worker...
start "Celery Worker" cmd /k ""C:\Users\dell2\AppData\Local\Programs\Python\Python313\python.exe" -m celery -A backend.tasks.batch_tasks worker --loglevel=info -P solo"

:: 3. Start R Shiny Server
echo [3/4] Starting R Shiny Server (Port 8080)...
start "R Shiny Server" cmd /k ""C:\Program Files\R\R-4.3.2\bin\Rscript.exe" -e "shiny::runApp('r_dashboard/app.R', port=8080, launch.browser=FALSE)""

:: 4. Start React Frontend
echo [4/4] Starting React Frontend...
start "React Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo All services have been launched in separate windows!
echo Once Vite is ready, you can access the platform at: http://localhost:5173
echo.
pause
