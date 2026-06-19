# Graveboards Backend

> Python/Connextion backend for Graveboards

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
- `dev` - Development (default)
- `prod` - Production
- `test` - Testing

**Services:**
- `all` - All services (default)
- `backend` - Backend service
- `frontend` - Frontend service
- `postgres` - PostgreSQL database
- `redis` - Redis cache

```
### Backend (Docker)

```bash
cd graveboards-backend
make status    # Database status
make reset     # Reset database
make seed      # Seed database
make logs      # View logs
make shell     # Open shell
make clean     # Remove Docker resources
```

### Backend (manage.py)

```bash
cd graveboards-backend
python manage.py <command> [options]
```

**Available commands:**
- `status <target>` - View database status
- `reset [--seed <target>]` - Reset database
- `seed <target>` - Seed database
- `fixtures <subcommand>` - Manage test fixtures
  - `fetch` - Fetch data from osu! API
  - `promote` - Promote fixtures to tests
  - `demote` - Demote fixtures to instance
  - `wipe` - Delete all fixtures
  - `status` - Show fixture status
  - `refresh` - Refresh fixture metadata

---

## Configuration

### Environment Files

| File           | Purpose                      |
|----------------|------------------------------|
| `.env`         | Primary config               |
| `.env.test`    | Test-specific overrides      |
| `.env.example` | Template for creating `.env` |

Copy `.env.example` to `.env` (and optionally `.env.test`) and fill in the appropriate values

**Required Variables:**
- `JWT_SECRET_KEY` - JWT signing key (32+ chars)
- `OSU_CLIENT_ID`, `OSU_CLIENT_SECRET` - osu! OAuth credentials
- `ADMIN_USER_IDS` - Comma-separated osu! user IDs
- `POSTGRESQL_*` - PostgreSQL connection
- `REDIS_*` - Redis connection

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

## Documentation

- [Frontend README](../graveboards-frontend/README.md)
- [Architecture Docs](./docs)
- [Production Deployment Guide](../graveboards-deploy/docs/PRODUCTION_DEPLOYMENT.md)

---

## License

MIT License
