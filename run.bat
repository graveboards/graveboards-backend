@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =========================
REM Step 1: Create .env, .env.test, and .env.docker (once)
REM =========================
if exist ".env.docker" if exist ".env" if exist ".env.test" (
    echo .env, .env.test, and .env.docker already exist. Skipping creation.
) else (
    echo Creating environment files...

    REM Generate a 32-character random alphanumeric JWT_SECRET_KEY
    set "CHARS=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    set "KEY="
    for /L %%i in (1,1,32) do (
        set /A idx=!random! %% 62
        call set "KEY=%%KEY%%%%CHARS:~!idx!,1%%"
    )

    set "KEY_DOTENV="
    for /L %%i in (1,1,32) do (
        set /A idx=!random! %% 62
        call set "KEY_DOTENV=%%KEY_DOTENV%%%%CHARS:~!idx!,1%%"
    )

    set "KEY_TEST="
    for /L %%i in (1,1,32) do (
        set /A idx=!random! %% 62
        call set "KEY_TEST=%%KEY_TEST%%%%CHARS:~!idx!,1%%"
    )

    echo.
    echo You can set up your osu client credentials here: https://osu.ppy.sh/home/account/edit#oauth
    echo Step 1: Click "New OAuth Application +"
    echo Step 2: Type any name and paste ^http://localhost:3000/callback^ for the callback url
    set /p OSU_CLIENT_ID=Please paste your OSU_CLIENT_ID:
    set /p OSU_CLIENT_SECRET=Please paste your OSU_CLIENT_SECRET:
    echo.
    set /p OSU_USER_ID=Enter your osu user ID to add yourself as an admin:
    echo.

    REM Ask to disable security with CHOICE (Y/N)
    set "DISABLE_SECURITY=false"
    echo Disable security for dev convenience?
    choice /C YN /M "Choose Y or N (default: N)"
    if errorlevel 2 set "DISABLE_SECURITY=false"
    if errorlevel 1 set "DISABLE_SECURITY=true"

    > ".env" (
        echo DEBUG=true
        echo DISABLE_SECURITY=!DISABLE_SECURITY!
        echo BASE_URL=http://localhost:3000
        echo JWT_SECRET_KEY=!KEY_DOTENV!
        echo JWT_ALGORITHM=HS256
        echo ADMIN_USER_IDS=!OSU_USER_ID!,5099768
        echo OSU_CLIENT_ID=!OSU_CLIENT_ID!
        echo OSU_CLIENT_SECRET=!OSU_CLIENT_SECRET!
        echo POSTGRESQL_HOST=localhost
        echo POSTGRESQL_PORT=5432
        echo POSTGRESQL_USERNAME=postgres
        echo POSTGRESQL_PASSWORD=
        echo POSTGRESQL_DATABASE=graveboards_dev
        echo REDIS_HOST=localhost
        echo REDIS_PORT=6379
        echo REDIS_USERNAME=
        echo REDIS_PASSWORD=
        echo REDIS_DB=0
    )

    > ".env.test" (
        echo DEBUG=true
        echo DISABLE_SECURITY=true
        echo BASE_URL=http://localhost:3000
        echo JWT_SECRET_KEY=!KEY_TEST!
        echo JWT_ALGORITHM=HS256
        echo ADMIN_USER_IDS=1,2
        echo OSU_CLIENT_ID=test-client-id
        echo OSU_CLIENT_SECRET=test-client-secret
        echo POSTGRESQL_HOST=localhost
        echo POSTGRESQL_PORT=5432
        echo POSTGRESQL_USERNAME=postgres
        echo POSTGRESQL_PASSWORD=
        echo POSTGRESQL_DATABASE=graveboards_test
        echo REDIS_HOST=localhost
        echo REDIS_PORT=6379
        echo REDIS_USERNAME=
        echo REDIS_PASSWORD=
        echo REDIS_DB=15
    )

    > ".env.docker" (
        echo DEBUG=true
        echo DISABLE_SECURITY=!DISABLE_SECURITY!
        echo BASE_URL=http://localhost:3000
        echo JWT_SECRET_KEY=!KEY!
        echo JWT_ALGORITHM=HS256
        echo ADMIN_USER_IDS=!OSU_USER_ID!,5099768
        echo OSU_CLIENT_ID=!OSU_CLIENT_ID!
        echo OSU_CLIENT_SECRET=!OSU_CLIENT_SECRET!
        echo POSTGRESQL_HOST=graveboards-postgresql-dev
        echo POSTGRESQL_PORT=5432
        echo POSTGRESQL_USERNAME=postgres
        echo POSTGRESQL_PASSWORD=
        echo POSTGRESQL_DATABASE=graveboards
        echo REDIS_HOST=graveboards-redis-dev
        echo REDIS_PORT=6379
        echo REDIS_USERNAME=
        echo REDIS_PASSWORD=
        echo REDIS_DB=0
    )

    echo.
    echo [OK] Environment files created:
    echo   - .env (dev mode with localhost DB/Redis)
    echo   - .env.test (test mode with isolated DB/Redis)
    echo   - .env.docker (Docker mode with service names)
    echo.
    echo You have been added to ADMIN_USER_IDS as !OSU_USER_ID!.
)

REM =========================
REM Step 2: Check Docker in PATH
REM =========================
where docker >nul 2>nul
if errorlevel 1 (
    echo [ERR] Docker is not installed or not in PATH. Install Docker Desktop and try again.
    pause
    exit /b 1
)

REM =========================
REM Step 3: Check Docker daemon running
REM =========================
docker info >nul 2>nul
if errorlevel 1 (
    echo [ERR] Docker daemon is not running. Start Docker Desktop and try again.
    pause
    exit /b 1
)

REM =========================
REM Step 4: Pick compose command (v2: "docker compose", fallback: "docker-compose")
REM =========================
set "COMPOSE_CMD="
docker compose version >nul 2>nul && set "COMPOSE_CMD=docker compose"
if not defined COMPOSE_CMD (
    where docker-compose >nul 2>nul && set "COMPOSE_CMD=docker-compose"
)
if not defined COMPOSE_CMD (
    echo [ERR] Neither ^"docker compose^" nor ^"docker-compose^" is available.
    echo      Install Docker Compose v2 or the legacy docker-compose.
    pause
    exit /b 1
)

REM =========================
REM Step 5: Launch
REM =========================
echo.
echo Starting services with: %COMPOSE_CMD% up --build
%COMPOSE_CMD% up --build
set "RC=%ERRORLEVEL%"

echo.
echo Shutting down...
%COMPOSE_CMD% down

exit /b %RC%
