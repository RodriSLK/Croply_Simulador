# Croply IoT Simulator

Servicio independiente que simula sensores agrícolas de una parcela. Toma el clima real de [Open-Meteo](https://open-meteo.com/) y genera lecturas de temperatura y humedad ambiente, humedad de suelo, radiación solar, precipitación y pH. Las guarda en su propia base PostgreSQL y las expone por HTTP.

Croply lo usa como si fueran sensores físicos. El backend crea, actualiza y da de baja parcelas en el simulador, y cada cierto tiempo lee `GET /parcelas/{id}/estado`. El simulador no llama al backend ni al servicio de recomendación, y no comparte la base de datos de Croply.

El contrato de la API, los modelos de cada sensor y las decisiones de diseño están en `Croply_IoT_Simulator_Documentacion_Tecnica.md`.

## Entorno completo con Docker

Un solo `docker compose` levanta el simulador junto con Croply y el servicio de recomendación:

| Servicio | URL |
| --- | --- |
| Frontend Croply | http://localhost:5173 |
| API Croply | http://localhost:3000/api/v1 |
| Swagger de la API | http://localhost:3000/api/v1/docs |
| Panel del simulador | http://localhost:8000 |
| Swagger del simulador | http://localhost:8000/docs |
| Servicio de recomendación | http://localhost:8001/docs |

Postgres queda solo en la red interna. Tiene dos bases: `croply_db` (Croply) y `croply_simulator` (este servicio).

### Requisitos

- Docker Desktop con Compose v2.
- Salida a internet. El simulador consulta Open-Meteo en cada ciclo.
- Las carpetas hermanas `../backend`, `../frontend` y `../../../Croply-ml-research` en su lugar. El compose las construye tal cual están; no hace falta modificarlas.

No arranques al mismo tiempo el `docker-compose.yml` de la raíz de Croply ni el del servicio de IA. Usan los mismos nombres de contenedor (`croply_postgres`, `croply_backend`, `croply_frontend`) y los puertos 3000, 5173 y 8000.

### Arranque

Desde esta carpeta:

```bash
docker compose up --build
```

La primera vez tarda: el backend y el frontend instalan dependencias con pnpm, y el servicio de recomendación instala LightGBM. Cuando el frontend responde en el puerto 5173, el stack está listo.

Para parar y conservar los datos:

```bash
docker compose down
```

`docker compose down -v` borra también el volumen `croply_stack_pgdata` (parcelas, lecturas y datos de Croply).

### Cómo probarlo junto con Croply

1. Entrá a http://localhost:5173 e iniciá sesión con `diego@croply.app` y la contraseña `CroplyAdmin123!`. También sirven `rodrigo@croply.app` y `paula@croply.app`, con la misma contraseña. El backend las crea al arrancar.
2. Creá una finca con latitud y longitud, y una parcela activa con al menos un controlador y sensores.
3. Croply hace `POST /parcelas` en el simulador. En http://localhost:8000, el botón **Cargar / actualizar parcelas** muestra esa parcela, los valores de cada sensor y el estado del scheduler.
4. Cada 5 minutos el simulador calcula un ciclo nuevo y Croply vuelve a leer el estado. En el diseño del producto ese intervalo es de 25 minutos; este compose usa 5 para poder ver datos sin esperar tanto. Se cambia con `SCHEDULER_INTERVAL_MINUTES` (simulador) y `SIMULADOR_SYNC_INTERVAL_MINUTES` (backend) en `docker-compose.yml`. Conviene que los dos coincidan.

Desde el panel de una parcela podés registrar riego, lluvia o una helada (se aplican en el próximo ciclo), forzar `SIN_SEÑAL` o reconectar un controlador, y ver las últimas 50 lecturas.

### Recomendaciones

El servicio de IA clasifica la parcela con LightGBM y, si no puede redactar con un modelo de lenguaje, responde con el texto de respaldo del INTA. Croply lo consulta en `http://recomendacion:8000`. En el host el puerto publicado es el **8001**, porque el 8000 es el simulador.

Ollama y el modelo Gemma quedan fuera del arranque: la imagen pesa varios GB. Para levantarlo:

```bash
docker compose --profile llm up --build
docker compose exec ollama ollama pull gemma4:e4b
```

El compose limita la espera del modelo a 8 segundos. El cliente HTTP de Croply corta a los 10 segundos; con ese tope el servicio alcanza a devolver el respaldo INTA en lugar de un error. La redacción de Gemma se prueba directo en http://localhost:8001/docs.

Para usar Gemini, cambiá `LLM_PROVIDER` a `gemini` en el servicio `recomendacion` de `docker-compose.yml` y definí `GEMINI_API_KEY` antes de `docker compose up`. El compose ya lee esa variable. En PowerShell: `$env:GEMINI_API_KEY = "tu-clave"`.

### Credenciales de desarrollo

Son las de `backend/.env.example`. Alcanzan para un entorno local:

- Postgres: usuario `croply_admin`, contraseña `croply_password`, bases `croply_db` y `croply_simulator`.
- JWT y contraseña de los admins: los valores de ese ejemplo (`SEED_ADMIN_PASSWORD=CroplyAdmin123!`).

La imagen del backend es la de producción (código ya compilado, sin recarga). El proceso arranca con `NODE_ENV=development` para que el seed, Swagger y el correo por consola funcionen sin una clave de Resend. El esquema de Croply se crea con `DB_SYNCHRONIZE=true` porque el backend todavía no trae migraciones.

## Uso local, sin Docker

Hace falta Python 3.11 o superior y un PostgreSQL con la base `croply_simulator`.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

`.env.example` deja el ciclo del scheduler en 2 minutos. El panel queda en http://localhost:8000 y la documentación interactiva en http://localhost:8000/docs.

Los tests usan pytest contra PostgreSQL en `localhost:5432` (`postgres` / `postgres`, base `croply_simulator`):

```bash
pytest
```
