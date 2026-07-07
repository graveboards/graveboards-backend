# Docker Architecture

## Components

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  PostgreSQL  │      │    Redis     │      │    Backend   │
│    (DB)      │──────│   (Cache)    │──────│   Connexion  │
│   Port 5432  │      │   Port 6379  │      │   Port 8000  │
└──────────────┘      └──────────────┘      └──────┬───────┘
                                                    │
                                                    │
                                               ┌───────────┐
                                               │  Frontend │
                                               │  Next.js  │
                                               │ Port 3000 │
                                               └───────────┘
```

## Network

All services communicate via the `app` network (bridge driver).

**Service Hostnames:**
- Backend: `backend` (port 8000)
- Frontend: `frontend` (port 3000)
- Database: `postgresql` (port 5432)
- Redis: `redis` (port 6379)

## Modes

| Mode | Compose File | Frontend Target | Database | Redis DB | Ports Exposed |
|------|-------------|-----------------|----------|----------|---------------|
| `dev` | `docker-compose.yml` | `development` (hot-reload) | `graveboards_dev` | 0 | 5432, 6379, 8000, 3000 |
| `prod` | `docker-compose.prod.yml` | `production` (standalone) | `graveboards_prod` | 0 | None (behind reverse proxy) |
| `prod-nas` | `prod.yml` + `prod-nas.yml` | `production` (standalone) | `graveboards_prod` | 0 | None (behind reverse proxy) |
| `test` | `docker-compose.test.yml` | N/A | `graveboards_test` | 15 | 5432, 6379 |

## Volumes

### Dev Mode

| Volume / Mount | Purpose | Type |
|----------------|---------|------|
| `postgresql-data` | PostgreSQL database | Named |
| `redis-data` | Redis cache | Named |
| `../graveboards-backend/instance` | Backend runtime files | Bind mount |
| `../graveboards-backend/docker-init` | DB init scripts | Bind mount (read-only) |

### Production Mode

| Volume / Mount | Purpose | Type |
|----------------|---------|------|
| `postgresql-prod-data` | PostgreSQL database | Named |
| `redis-prod-data` | Redis cache | Named |
| `instance-prod-data` | Backend instance | Named |
| `../graveboards-backend/docker-init` | DB init scripts | Bind mount (read-only) |

### NAS Override (prod-nas mode)

Overrides production volumes with external paths via environment variables:
- `POSTGRESQL_DATA_PATH` → PostgreSQL data
- `REDIS_DATA_PATH` → Redis data
- `INSTANCE_DATA_PATH` → Backend instance

### Test Mode

| Volume / Mount | Purpose | Type |
|----------------|---------|------|
| `postgresql-test-data` | PostgreSQL database | Named |
| `redis-test-data` | Redis cache | Named |
| `instance-test-data` | Backend instance | Named |
| `../graveboards-backend/docker-init` | DB init scripts | Bind mount (read-only) |

## Quick Start

```bash
cd graveboards-deploy
./deploy.sh up dev
```

## Access

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/api/v1/ui

## View Logs

```bash
cd graveboards-deploy
./deploy.sh logs [dev|prod|prod-nas|test] [backend|frontend|postgres|redis|all]
```

## Backend Security Hardening

The backend container runs with:
- `read_only: true` filesystem
- `no-new-privileges: true`
- tmpfs mounts for `/tmp` and `/app/instance/logs`

## Resource Limits

| Service | CPU Limit | Memory Limit |
|---------|-----------|-------------|
| PostgreSQL | 2 | 4G |
| Redis | 1 | 1G |
| Backend | 2 | 4G |
| Frontend | 1 | 2G |
