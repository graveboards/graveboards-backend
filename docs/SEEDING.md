# Seeding the Database

This guide covers how to populate the Graveboards database with data using the seeding system.

## Overview

Seeding reads fixture data from `instance/fixtures/` and inserts it into the database. The system supports two modes:

1. **Manual mode** (default): Seeds only what's currently in `instance/fixtures/`
2. **Auto mode** (`--ensure-fixtures`): Fetches/generates missing fixtures before seeding

## Quick Start

### One-Command Seed (Recommended)

```bash
cd graveboards-backend
make seed
```

This runs `seed all --ensure-fixtures --profile default`, which:
1. Fetches 30 beatmapsets from osu! API (if missing)
2. Fetches beatmapset owner users (if missing)
3. Generates 10 queues and 100 requests (if missing)
4. Seeds the database

### Manual Mode (Seed Only What Exists)

```bash
python manage.py seed all
```

Only seeds data currently in `instance/fixtures/`. Use this when you've already populated fixtures manually or want full control.

## Profiles

Profiles define default counts for fetching/generating fixtures. Configure them in `app/database/seeding/profiles.py`.

### Built-in Profiles

| Profile | Beatmapsets | Queues | Requests | Use Case |
|---------|-------------|--------|----------|----------|
| `default` | 30 | 10 | 100 | Balanced for most testing |
| `minimal` | 10 | 5 | 25 | Quick testing, CI |
| `comprehensive` | 100 | 30 | 300 | Full search engine testing |

### Using a Profile

```bash
# Use minimal profile for quick testing
python manage.py seed all --ensure-fixtures --profile minimal

# Use comprehensive profile for search testing
python manage.py seed all --ensure-fixtures --profile comprehensive
```

### Creating Custom Profiles

Edit `app/database/seeding/profiles.py`:

```python
PROFILES = {
    "default": SeedProfile(
        name="default",
        beatmapsets_count=30,
        queue_count=10,
        request_count=100,
    ),
    "my-custom": SeedProfile(
        name="my-custom",
        beatmapsets_count=50,
        queue_count=20,
        request_count=200,
    ),
}
```

## How It Works

### Data Flow

```
osu! API
    |
    v
beatmapsets/ (30 sets, each with embedded beatmaps)
    |
    +---> users/ (owner users extracted from beatmapsets)
    |
    v
queues/ (generated, reference users)
    |
    v
requests/ (generated, reference queues + beatmapsets)
    |
    v
Database (seeded in dependency order)
```

### Seeding Order

The seeder respects FK dependencies:

```
Layer 0: [users]
Layer 1: [beatmaps, queues]      (concurrent)
Layer 2: [requests]
```

- **users** must be seeded first (referenced by beatmapsets, queues, requests)
- **beatmaps** (from beatmapsets) and **queues** can be seeded concurrently
- **requests** require both beatmaps and queues

### Fixture Sources

| Category | Source | Notes |
|----------|--------|-------|
| `beatmapsets` | osu! API | Contains embedded beatmap difficulties |
| `users` | osu! API | Extracted from beatmapset owners |
| `queues` | Generated | Synthetic, reference fetched users |
| `requests` | Generated | Synthetic, reference queues + beatmapsets |
| `beatmap_tags` | Committed | Reference data, no fetching needed |

**Note:** Individual `beatmaps` fixtures are not needed. The osu! API's `beatmapset` endpoint returns all difficulties embedded in a single response.

## CLI Reference

### `seed` Command

```bash
python manage.py seed <target> [options]
```

**Targets:** `all`, `users`, `beatmaps`, `queues`, `requests`

**Options:**
- `--ensure-fixtures` - Auto-fetch/generate missing fixtures before seeding
- `--profile NAME` - Profile for fixture counts (default, minimal, comprehensive)

**Examples:**

```bash
# Seed everything with auto-fetch (default profile)
python manage.py seed all --ensure-fixtures

# Seed only users (no auto-fetch)
python manage.py seed users

# Seed with custom profile
python manage.py seed all --ensure-fixtures --profile comprehensive

# Seed queues/requests only (assumes users/beatmaps exist)
python manage.py seed queues requests
```

### `fixtures` Commands

```bash
# Fetch beatmapsets from osu! API
python manage.py fixtures fetch --beatmapsets 30

# Fetch users from beatmapset owners
python manage.py fixtures fetch-users-from-beatmapsets

# Generate queues and requests
python manage.py fixtures generate --queue-count 10 --request-count 100

# Promote fixtures from instance/ to tests/
python manage.py fixtures promote

# Demote fixtures from tests/ to instance/
python manage.py fixtures demote

# Refresh top player IDs from osu! API
python manage.py fixtures refresh-top-players

# Refresh archive index from osu.sh
python manage.py fixtures refresh-archives

# Reconcile fixture metadata with disk state
python manage.py fixtures reconcile

# Check fixture status
python manage.py fixtures status

# Clean all fixtures
python manage.py fixtures clean --force
```

## Fixture Locations

| Location | Purpose | Contents |
|----------|---------|----------|
| `instance/fixtures/` | Working fixtures (source of truth) | `users/`, `beatmapsets/`, `queues/`, `requests/`, `beatmap_tags.json` |
| `tests/fixtures/` | Promoted fixtures (for test suite) | Same structure, promoted via `fixtures promote` |

## Workflow Examples

### Fresh Setup

```bash
# One-command setup
make seed

# Or step-by-step
python manage.py fixtures fetch --beatmapsets 30
python manage.py fixtures fetch-users-from-beatmapsets
python manage.py fixtures generate --queue-count 10 --request-count 100
python manage.py seed all
```

### Incremental Updates

```bash
# Re-fetch only what's missing
python manage.py seed all --ensure-fixtures

# Regenerate queues/requests with new data
python manage.py fixtures generate --queue-count 20 --request-count 200
python manage.py seed queues requests
```

### Search Engine Testing

```bash
# Comprehensive profile for full coverage
python manage.py seed all --ensure-fixtures --profile comprehensive

# Or fetch search-test fixtures separately
python manage.py fixtures fetch --criteria search-test
python manage.py seed all
```

## Troubleshooting

### "No fixture data found"

Run with `--ensure-fixtures` to auto-populate, or manually fetch:

```bash
python manage.py fixtures fetch --beatmapsets 30
python manage.py fixtures fetch-users-from-beatmapsets
```

### Foreign Key Violations

Ensure users exist before seeding beatmapsets:

```bash
python manage.py seed users
python manage.py seed beatmaps
```

Or use `--ensure-fixtures` to handle dependencies automatically.

### Stale Data

Re-run the full pipeline:

```bash
python manage.py fixtures clean --force
make seed
```

## Architecture

### Components

- **`SeedProfile`** - Defines default counts for fetching/generating
- **`FixtureOrchestrator`** - Coordinates osu! API fetching
- **`QueueRequestFixtureGenerator`** - Generates synthetic queues/requests
- **`SeederOrchestrator`** - Coordinates dependency-aware database seeding

### Key Design Decisions

1. **Beatmapsets contain all beatmap data** - No need for separate `beatmaps/` fixtures
2. **Users derived from beatmapset owners** - Guarantees FK integrity
3. **Profiles centralize defaults** - Easy to adjust counts in one place
4. **Separate manual/auto modes** - Flexibility for different workflows
