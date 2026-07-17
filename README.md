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

### Orchestrator (deploy.sh)

```bash
cd graveboards-deploy
./deploy.sh up [mode] [--build] [--no-monitoring] [--nas] [--traefik] [--monitoring-ports] [--monitoring-traefik] [--no-frontend] [service...]  # Start services
./deploy.sh down [mode] [--no-monitoring] [--nas] [--traefik] [--monitoring-traefik] [--no-frontend] [service...]              # Stop services
./deploy.sh build [mode] [--no-monitoring] [--nas] [--traefik] [--no-frontend] [service...]             # Build images
./deploy.sh deploy [mode] [--follow|-f] [--no-monitoring] [--nas] [--traefik] [--monitoring-traefik] [--no-frontend]  # Full pipeline: down + pull + build + up
./deploy.sh pull [repo...]                        # Git pull repositories
./deploy.sh force-pull [repo...]                  # Force reset repositories to origin
./deploy.sh logs [mode] [--no-monitoring] [--nas] [--traefik] [--monitoring-traefik] [--no-frontend] [service]  # View logs
./deploy.sh test [--log-file <path>] [--no-cleanup] [--no-log] [--quiet]  # Run tests
./deploy.sh status                                  # Show status
./deploy.sh clean                                   # Remove volumes and images
./deploy.sh help                                    # Show help
```

**Modes:**
- `dev`      - Development (default, hot-reload, monitoring enabled)
- `prod`     - Production (Docker named volumes, monitoring enabled)
- `test`     - Testing (isolated DB/Redis, runs pytest, no monitoring)

**Flags:**
- `--build` - Rebuild images before starting (up only)
- `--no-monitoring` - Skip the monitoring stack
- `--nas`           - Include NAS volume overrides (prod only)
- `--traefik`       - Include Traefik overrides for frontend + Grafana (prod only, requires traefik-proxy network)
- `--monitoring-ports` - Publish monitoring ports to host (dev only, for local access)
- `--monitoring-traefik` - Include Traefik routes for monitoring services (prod only)
- `--no-frontend` - Exclude frontend service

**Services (for up/down/build/logs):**
- `all` - All services (default)
- `backend` - Backend service
- `frontend` - Frontend service
- `postgres` / `postgresql` - PostgreSQL database
- `redis` - Redis cache

### Backend (Makefile)

The Makefile wraps `docker compose` commands referencing the deploy repo's compose files.

```bash
cd graveboards-backend
make up        # Start all services (dev compose stack)
make down      # Stop all services
make build     # Build all services in dev compose stack
make logs      # Follow backend logs
make shell     # Open backend shell
make status    # View database status
make reset     # Reset database (with confirmation)
make seed      # Seed database (with auto-fetch/generate, default profile)
make fresh     # Reset database and seed (with confirmation)
make test      # Run tests in isolated test stack (Postgres + Redis + backend)
make clean     # Tear down dev and test compose stacks
```

### Backend (manage.py)

```bash
cd graveboards-backend
python -m manage <command> [options]
```

**Available commands:**
- `status [target]` - View database status (`summary`, `users`, `beatmaps`, `beatmapsets`, `queues`, `requests`)
- `reset [--force] [--seed <target>]` - Reset database (drop/recreate, optionally seed)
- `seed <target> [--ensure-fixtures] [--profile NAME]` - Seed database (`all`, `users`, `beatmaps`, `queues`, `requests`)
- `generate-api-key <user_id> [--expires-days N]` - Generate a new API key for a user
- `migrate <subcommand>` - Database migration commands
  - `run [--dry-run]` - Run all pending migrations
  - `downgrade [revision]` - Rollback migrations
  - `history` - Show migration history
  - `current` - Show current revision
  - `stamp <revision>` - Mark DB as current without running
- `fixtures <subcommand>` - Manage test fixtures
  - `fetch` - Fetch fixture data from osu! API
  - `fetch-users-from-beatmapsets` - Fetch users from beatmapset owners
  - `promote` - Promote fixtures from instance to tests
  - `demote` - Demote fixtures from tests to instance
  - `status` - Show fixture status
  - `clean [--force]` - Delete all fixtures
  - `refresh-top-players` - Fetch top players from osu! API
  - `refresh-archives` - Refresh archive index from osu.sh
  - `reconcile` - Reconcile fixture metadata with disk state
  - `generate --queue-count N --request-count N` - Generate diverse queue/request fixtures

### Seeding the Database

Seeding populates the database with fixture data from `instance/fixtures/`.

**Quick start:**

```bash
# One-command seed with auto-fetch (recommended)
make seed

# Or manual mode (seed only what exists)
python manage.py seed all
```

**Profiles:** Configure fixture counts in `app/database/seeding/profiles.py`. Built-in: `default` (30 beatmapsets, 10 queues, 100 requests), `minimal`, `comprehensive`.

See [docs/SEEDING.md](./docs/SEEDING.md) for the full seeding guide.

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

The backend exposes Prometheus-compatible metrics at `/metrics` (internal only). Enable the full monitoring stack (Prometheus, Grafana, Alertmanager, Loki, Promtail) via the deploy script:

```bash
# Dev or prod (monitoring enabled by default)
./deploy.sh up dev
./deploy.sh up prod

# Disable monitoring if needed
./deploy.sh up dev --no-monitoring

# Expose Prometheus/Alertmanager via Traefik (prod only)
./deploy.sh up prod --monitoring-traefik
```

**Access (dev):**

Publish monitoring ports to the host:

```bash
./deploy.sh up dev --monitoring-ports
```

- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

**Access (prod):**

Only Grafana is publicly reachable via Traefik:

```bash
./deploy.sh up prod --traefik
```

- Grafana: https://grafana.graveboards.net (Grafana login required)
- Prometheus, Loki, Alertmanager: internal-only (no host ports)

**Available metrics:** `http_requests_total`, `http_request_duration_seconds`, `db_pool_*`, `db_query_duration_seconds`, `redis_commands_*`, `osu_api_*`, `rate_limit_*`, `daemon_*`, `process_*`, `errors_total`

Every request includes a `request_id` (UUID) injected into all log lines via `structlog.contextvars` for correlation with Loki logs.

---

## Documentation

- [Frontend README](../graveboards-frontend/README.md)
- [Architecture Docs](./docs)
- [Production Deployment Guide](../graveboards-deploy/docs/PRODUCTION_DEPLOYMENT.md)

---

## License

MIT License
