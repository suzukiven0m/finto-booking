# D18 (WP14): immagine API. Solo codice: migrazioni e seed sono passi manuali
# documentati (README «Run with Docker»), i dataset non entrano nell'immagine.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]