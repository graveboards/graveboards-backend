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

All services communicate via `graveboards-network` (bridge driver).

**Service Hostnames:**
- Backend: `graveboards-backend` (port 8000)
- Frontend: `graveboards-frontend` (port 3000)
- Database: `postgres` (port 5432)
- Redis: `redis` (port 6379)

## Volumes

| Volume          | Purpose               |
|-----------------|-----------------------|
| `postgres-data` | PostgreSQL database   |
| `redis-data`    | Redis cache           |
| `./instance`    | Backend runtime files |

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
./deploy.sh logs dev [backend|frontend|postgres|redis|all]
```
