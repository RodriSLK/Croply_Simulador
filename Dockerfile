# Croply IoT Simulator — FastAPI
#   docker compose up --build   (desde esta carpeta, stack completo)

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY scripts/entrypoint.py ./scripts/entrypoint.py

EXPOSE 8000

CMD ["python", "scripts/entrypoint.py"]
