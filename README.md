# adare-server

## Prerequisites

- Docker & Docker Compose
- Node.js 20+
- [pre-commit](https://pre-commit.com/) and [gitleaks](https://github.com/gitleaks/gitleaks) (`brew install pre-commit gitleaks`, then run `pre-commit install` once per clone to enable the secret-scanning hook)

## Quick Start

```bash
# 1. Set up environment
cp backend_django/.env.example backend_django/.env

# 2. Start backend services
cd backend_django
make up

# 3. (Optional) Seed sample data
make seed          # generic dev sample data
make seed-paper    # the paper's §5.1-§5.5 case studies, for demos/screenshots

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
| `make seed-paper` | Seed paper-evaluation demo data (local dev only) — 42 experiments / 13 environments from the paper's §5.1–§5.5 case studies, plus a printed demo login |
| `make unseed-paper` | Remove paper-evaluation demo data (leaves `make seed` data untouched) |
| `make react` | Start React dev server |