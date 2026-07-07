# Graveboards Backend

> Python/Connexion async REST API backend for Graveboards

## Quick Start

### Prerequisites

- Docker Engine 24+
- Docker Compose 2.0+
- Git

### Installation

```bash
# Clone all repositories
git clone https://github.com/graveboards/graveboards-frontend.git
git clone https://github.com/graveboards/graveboards-backend.git
git clone https://github.com/graveboards/graveboards-deploy.git

# Start all services
cd graveboards-deploy
./deploy.sh up dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/ui

---

## Management

### Orchestrator (Docker)

```bash
cd graveboards-deploy
./deploy.sh up [mode]               # Start services
./deploy.sh down [mode]             # Stop services
./deploy.sh logs [mode] [service]   # View logs
./deploy.sh test                    # Run tests
./deploy.sh build [mode]            # Build images
./deploy.sh status                  # Show status
./deploy.sh clean                   # Remove volumes and images
```

**Modes:**
- `dev`      - Development (default)
- `prod`     - Production (Docker volumes)
- `prod-nas` - Production (NAS volumes)
- `test`     - Testing (isolated DB/Redis, runs pytest)

**Services:**
- `all` - All services (default)
- `backend` - Backend service
- `frontend` - Frontend service
- `postgres` - PostgreSQL database
- `redis` - Redis cache

### Backend (Docker/Make)

```bash
cd graveboards-backend
make up        # Start all services
make down      # Stop all services
make build     # Rebuild project image
make logs      # View backend logs
make shell     # Open backend shell
make status    # View database status
make reset     # Reset database (with confirmation)
make seed      # Seed database
make fresh     # Reset & seed database
make test      # Run test suite
make clean     # Remove Docker resources
```

### Backend (manage.py)

```bash
cd graveboards-backend
python manage.py <command> [options]
```

**Available commands:**
- `status [target]` - View database status (default: `summary`)
- `reset [--force] [--seed <target>]` - Reset database (drop/recreate, optionally seed)
- `seed <target>` - Seed database (e.g. `all`, `users`, `beatmaps`, `queues`, `requests`)
- `fixtures <subcommand>` - Manage test fixtures
  - `fetch` - Fetch fixture data from osu! API
  - `promote` - Promote fixtures from instance to tests
  - `demote` - Demote fixtures from tests to instance
  - `status` - Show fixture status
  - `wipe` - Delete all fixtures
  - `refresh-top-players` - Fetch top players from osu! API
  - `refresh-archives` - Refresh archive index from osu.sh
  - `reconcile` - Reconcile fixture metadata with disk state
  - `generate` - Generate diverse queue/request fixtures

---

## Configuration

### Environment Files

| File           | Purpose                      |
|----------------|------------------------------|
| `.env`         | Primary config               |
| `.env.test`    | Test-specific overrides      |
| `.env.example` | Template for creating `.env` |

Copy `.env.example` to `.env` (and optionally `.env.test`) and fill in the appropriate values.

**Required Variables:**
- `JWT_SECRET_KEY` - JWT signing key (32+ chars)
- `JWT_ALGORITHM` - JWT algorithm (default: `HS256`)
- `OSU_CLIENT_ID`, `OSU_CLIENT_SECRET` - osu! OAuth credentials
- `ADMIN_USER_IDS` - Comma-separated osu! user IDs
- `POSTGRESQL_HOST`, `POSTGRESQL_PORT`, `POSTGRESQL_USERNAME`, `POSTGRESQL_PASSWORD`, `POSTGRESQL_DATABASE` - PostgreSQL connection
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_USERNAME`, `REDIS_PASSWORD`, `REDIS_DB` - Redis connection

**Optional Variables:**
- `DEBUG` - Enable debug mode (default: `false`)
- `DISABLE_SECURITY` - Disable security (dev only, default: `false`)
- `BASE_URL` - Frontend base URL (default: `http://localhost:3000`)
- `ENV` - Environment mode: `prod`, `dev`, `test` (default: `prod`)
- `DEBUG_API_KEY` - Fixed debug API key

---

## Development

### Without Docker

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure environment

# Run
python main.py

# Manage
python manage.py
```

---

## Monitoring

The backend exposes Prometheus-compatible metrics at `/api/v1/metrics`. Enable the full monitoring stack (Prometheus, Grafana, Alertmanager, Loki, Promtail) via the deploy script:

```bash
# Dev or prod (monitoring enabled by default)
./deploy.sh up dev
./deploy.sh up prod

# Disable monitoring if needed
./deploy.sh up dev disable-monitoring
```

**Access:**
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

**Available metrics:** `http_requests_total`, `http_request_duration_seconds`, `db_pool_*`, `db_query_duration_seconds`, `redis_commands_*`, `osu_api_*`, `rate_limit_*`, `daemon_*`, `process_*`, `errors_total`

Every request includes a `request_id` (UUID) injected into all log lines for correlation between metrics and logs.

---

## Documentation

- [Frontend README](../graveboards-frontend/README.md)
- [Architecture Docs](./docs)
- [Production Deployment Guide](../graveboards-deploy/docs/PRODUCTION_DEPLOYMENT.md)

---

## License

MIT License
