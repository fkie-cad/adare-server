# adare-server

## Prerequisites

- Docker & Docker Compose
- Node.js 20+

## Quick Start

```bash
# 1. Set up environment
cp backend_django/.env.example backend_django/.env

# 2. Start backend services
cd backend_django
make up

# 3. (Optional) Seed sample data
make seed

# 4. Start React dev server (in a separate terminal)
make react
```

The backend runs at `http://localhost:8000`, the React frontend at `http://localhost:5173`.

## Dev Login

In development mode, a **Dev Login** button appears on the login page (localhost only). It creates a local user with a Knox auth token — no Gitea instance required. This lets you test the full frontend flow locally.

## Makefile Commands

Run from `backend_django/`:

| Command | Description |
|---------|-------------|
| `make up` | Start all services (docker compose up --build) |
| `make down` | Stop all services |
| `make migrate` | Run Django migrations |
| `make shell` | Open Django shell |
| `make logs` | Follow web container logs |
| `make seed` | Load sample dev data |
| `make react` | Start React dev server |