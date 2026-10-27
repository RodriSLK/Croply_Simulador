"""Arranque del simulador: espera Postgres, aplica migraciones y levanta Uvicorn."""

from __future__ import annotations

import os
import subprocess
import sys
import time

import psycopg


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        sys.exit("DATABASE_URL no está definida")
    return url


def psycopg_url(url: str) -> str:
    # SQLAlchemy usa el esquema postgresql+psycopg://; psycopg espera postgresql://.
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def wait_for_postgres(url: str, attempts: int = 30) -> None:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with psycopg.connect(psycopg_url(url), connect_timeout=3) as conn:
                conn.execute("SELECT 1")
            print("PostgreSQL disponible", flush=True)
            return
        except Exception as exc:
            last_error = exc
            print(f"Esperando PostgreSQL ({attempt}/{attempts}): {exc}", flush=True)
            time.sleep(2)
    sys.exit(f"PostgreSQL no respondió a tiempo: {last_error}")


def main() -> None:
    wait_for_postgres(database_url())
    subprocess.check_call([sys.executable, "-m", "alembic", "upgrade", "head"])
    os.execvp(
        sys.executable,
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
    )


if __name__ == "__main__":
    main()
