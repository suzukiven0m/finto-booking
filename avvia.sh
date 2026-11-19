#!/usr/bin/env bash
# accende database, api e dashboard con un solo comando (mac e linux): ./avvia.sh
# PROVVISORIO: quando il docker compose accendera' anche api e dashboard si toglie.
# la prima volta bisogna fare l'installazione (backend/lavoro_svolto.md)
# ctrl+c spegne api e dashboard, il database resta acceso

set -e
cd "$(dirname "$0")"

if [ ! -d backend/.venv ]; then
  echo "manca backend/.venv: fai prima l'installazione (backend/lavoro_svolto.md)"
  exit 1
fi
if [ ! -d frontend/node_modules ]; then
  echo "manca frontend/node_modules: fai prima npm install nella cartella frontend"
  exit 1
fi

# se api o dashboard sono gia' accese (es. lanciate a mano) mi fermo
for porta in 8000 5173; do
  if lsof -iTCP:$porta -sTCP:LISTEN >/dev/null 2>&1; then
    echo "la porta $porta e' gia' occupata: spegni prima quello che e' acceso (ctrl+c nel suo terminale)"
    exit 1
  fi
done

echo "accendo il database..."
docker compose -f infra/docker-compose.yml up -d --wait

echo "accendo le api su http://localhost:8000 (elenco su /docs)..."
(cd backend && exec .venv/bin/uvicorn app.main:app --reload --port 8000) &
API=$!
# quando lo script finisce (anche con ctrl+c) spengo anche le api
trap 'kill $API 2>/dev/null' EXIT

echo "accendo la dashboard su http://localhost:5173 ..."
cd frontend
# --strictPort: se la 5173 e' occupata non cambia porta da solo (le api accettano solo la 5173)
VITE_API_BASE_URL=http://localhost:8000 npm run dev -- --strictPort
