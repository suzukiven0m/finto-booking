@echo off
rem accende database, api e dashboard con un solo comando (windows): avvia.bat
rem PROVVISORIO: quando il docker compose accendera' anche api e dashboard si toglie.
rem la prima volta bisogna fare l'installazione (backend\lavoro_svolto.md)
rem le api si aprono in un'altra finestra: per spegnerle basta chiuderla.
rem ctrl+c qui spegne la dashboard, il database resta acceso

cd /d "%~dp0"

if not exist backend\.venv (
  echo manca backend\.venv: fai prima l'installazione, vedi backend\lavoro_svolto.md
  exit /b 1
)
if not exist frontend\node_modules (
  echo manca frontend\node_modules: fai prima npm install nella cartella frontend
  exit /b 1
)

rem se api o dashboard sono gia' accese (es. lanciate a mano) mi fermo
netstat -ano | findstr /r /c:":8000 .*LISTENING" >nul
if not errorlevel 1 (
  echo la porta 8000 e' gia' occupata: spegni prima quello che e' acceso
  exit /b 1
)
netstat -ano | findstr /r /c:":5173 .*LISTENING" >nul
if not errorlevel 1 (
  echo la porta 5173 e' gia' occupata: spegni prima quello che e' acceso
  exit /b 1
)

echo accendo il database...
docker compose -f infra/docker-compose.yml up -d --wait
if errorlevel 1 exit /b 1

echo accendo le api su http://localhost:8000 in un'altra finestra...
start "Buby API" cmd /k "cd backend && .venv\Scripts\uvicorn app.main:app --reload --port 8000"

echo accendo la dashboard su http://localhost:5173 ...
cd frontend
set VITE_API_BASE_URL=http://localhost:8000
rem --strictPort: se la 5173 e' occupata non cambia porta da solo (le api accettano solo la 5173)
npm run dev -- --strictPort
