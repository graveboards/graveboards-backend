#!/usr/bin/env bash

set -e
DOCKER_PREFIX=""

# =========================
# Step 1: Create .env.docker (once)
# =========================

if [ -f ".env.docker" ]; then
    echo ".env.docker already exists. Skipping creation."
else
    echo "Creating .env.docker..."

    # Generate 32-character random alphanumeric JWT_SECRET_KEY
    JWT_SECRET_KEY=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32)

    echo
    echo "You can set up your osu client credentials here:"
    echo "https://osu.ppy.sh/home/account/edit#oauth"
    echo "Step 1: Click 'New OAuth Application +'"
    echo "Step 2: Use http://localhost:3000/callback as callback URL"
    echo

    read -p "Please paste your OSU_CLIENT_ID: " OSU_CLIENT_ID
    read -p "Please paste your OSU_CLIENT_SECRET: " OSU_CLIENT_SECRET
    echo
    read -p "Enter your osu user ID to add yourself as an admin: " OSU_USER_ID
    echo

    DISABLE_SECURITY="false"
    read -p "Disable security for dev convenience? (y/N): " choice
    case "$choice" in
        y|Y) DISABLE_SECURITY="true" ;;
        *) DISABLE_SECURITY="false" ;;
    esac

    cat > .env.docker <<EOF
DEBUG=true
DISABLE_SECURITY=$DISABLE_SECURITY
BASE_URL=http://localhost:3000
JWT_SECRET_KEY=$JWT_SECRET_KEY
JWT_ALGORITHM=HS256
ADMIN_USER_IDS=$OSU_USER_ID,5099768
OSU_CLIENT_ID=$OSU_CLIENT_ID
OSU_CLIENT_SECRET=$OSU_CLIENT_SECRET
POSTGRESQL_HOST=graveboards-postgresql-dev
POSTGRESQL_PORT=5432
POSTGRESQL_USERNAME=postgres
POSTGRESQL_PASSWORD=
POSTGRESQL_DATABASE=
REDIS_HOST=graveboards-redis-dev
REDIS_PORT=6379
REDIS_USERNAME=
REDIS_PASSWORD=
REDIS_DB=0
EOF

    echo
    echo "[OK] .env.docker created with your credentials and secure JWT secret."
    echo "You have been added to ADMIN_USER_IDS as $OSU_USER_ID."
fi

# =========================
# Step 2: Check Docker in PATH
# =========================

if ! command -v docker >/dev/null 2>&1; then
    echo "[ERR] Docker is not installed or not in PATH."
    echo "Install Docker and try again."
    exit 1
fi

# =========================
# Step 3: Check Docker daemon / permissions
# =========================

if ! docker info >/dev/null 2>&1; then
    echo "[WARN] Cannot access Docker daemon."

    # Check if sudo works
    if sudo -n docker info >/dev/null 2>&1; then
        echo
        echo "Docker requires sudo on this system."
        echo "You can either:"
        echo "  1) Run this script with sudo"
        echo "  2) Add your user to the docker group:"
        echo "    sudo usermod -aG docker \$USER"
        echo "    (then log out and back in)"
        echo
        read -p "Run docker commands with sudo automatically? (y/N): " use_sudo
        case "$use_sudo" in
            y|Y)
                DOCKER_PREFIX="sudo"
                ;;
            *)
                echo "Exiting."
                exit 1
                ;;
        esac
    else
        echo "[ERR] Docker daemon is not running."
        echo "Start Docker and try again."
        exit 1
    fi
fi

# =========================
# Step 4: Pick compose command
# =========================

if $DOCKER_PREFIX docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="$DOCKER_PREFIX docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD="$DOCKER_PREFIX docker-compose"
else
    echo "[ERR] Neither 'docker compose' nor 'docker-compose' is available."
    exit 1
fi

# =========================
# Step 5: Launch
# =========================

echo
echo "Starting services with: $COMPOSE_CMD up --build"
$COMPOSE_CMD up --build
RC=$?

echo
echo "Shutting down..."
$COMPOSE_CMD down

exit $RC