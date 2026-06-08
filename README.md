# Server Side Events Learning App

Learning app with a FastAPI backend, SQLAlchemy-managed SQLite database,
Redis-backed notification fanout, server-sent events, and a Vue + TypeScript
frontend.

## Structure

```text
backend/
  Dockerfile
  app/
    main.py
    database.py
    models.py
    notifications.py
    schemas.py
  requirements.txt
compose.yml
frontend/
  Dockerfile
  src/
    App.vue
    main.ts
    style.css
  package.json
  tsconfig.json
  vite.config.ts
```

## Docker Compose

Use Docker Compose to run the backend, frontend, and Redis together:

```bash
docker compose up --build
```

Services are exposed at:

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

Redis is available to the backend on the internal Compose hostname `redis`.
It is not published to the host, which avoids conflicts with a local Redis
already using port `6379`.

Useful commands:

```bash
docker compose up --build
docker compose up -d
docker compose logs backend
docker compose down
docker compose down --volumes
```

Compose uses named volumes for backend SQLite data, frontend dependencies, and
Redis data:

- `backend_data` stores `/app/data/app.db`
- `frontend_node_modules` stores `/app/node_modules`
- `redis_data` stores Redis data

The Compose frontend uses `VITE_API_BASE_URL=http://127.0.0.1:8001`, because
the backend container listens on port `8000` internally but is published as
host port `8001`. The Compose backend sets `REDIS_URL=redis://redis:6379/0`,
so notification events are published through Redis and can be received by every
subscribed backend process. Without `REDIS_URL`, the backend falls back to
in-process SSE subscribers for local development.

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

The backend uses `backend/app.db` by default. Override this with
`DATABASE_URL` when running in another environment. If `REDIS_URL` is set,
notifications are published through Redis so SSE updates can fan out across
backend processes.

Backend environment variables:

- `DATABASE_URL`: SQLAlchemy database URL. Defaults to `sqlite:///backend/app.db`.
- `REDIS_URL`: Redis connection URL. Omit it to use the in-memory fallback.
- `REDIS_CHANNEL`: Redis pub/sub channel. Defaults to `notifications`.
- `CORS_ORIGINS`: comma-separated frontend origins allowed by CORS.

Format backend Python code with:

```bash
cd backend
python -m black app
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://127.0.0.1:5173`.

The frontend calls `http://127.0.0.1:8000` by default. Override this with
`VITE_API_BASE_URL`.
