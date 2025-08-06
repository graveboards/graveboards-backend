@echo off
setlocal EnableDelayedExpansion

REM Step 1: Create .env.docker if not exists
if exist ".env.docker" (
    echo .env.docker already exists. Skipping creation.
) else (
    echo Creating .env.docker...

    REM Generate a 32-character random alphanumeric JWT_SECRET_KEY
    set CHARS=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789
    set KEY=

    for /L %%i in (1,1,32) do (
        set /A idx=!random! %% 62
        call set "KEY=!KEY!!CHARS:~!idx!,1!"
    )

    REM Prompt for OSU credentials
    echo.
    echo You can set up your osu client credentials here: https://osu.ppy.sh/home/account/edit#oauth
    echo Step 1: Click "New OAuth Application +"
    echo Step 2: Type any name and paste `http://localhost:3000/callback` for the callback url
    set /p OSU_CLIENT_ID=Please paste your OSU_CLIENT_ID:
    set /p OSU_CLIENT_SECRET=Please paste your OSU_CLIENT_SECRET:
    echo.
    set /p OSU_USER_ID=Enter your osu! user ID to add yourself as an admin:
    echo.

    REM Prompt for DISABLE_SECURITY (accepts y/n or true/false, defaults to false)
    set "DISABLE_SECURITY=false"
    :ask_security
    set /p DISABLE_SECURITY_INPUT=Disable security for dev convenience? (y/n) [default: n]:
    set "DISABLE_SECURITY_INPUT=!DISABLE_SECURITY_INPUT: =!"  REM trim spaces
    set "DISABLE_SECURITY_INPUT=!DISABLE_SECURITY_INPUT:"=!"  REM remove quotes

    if "!DISABLE_SECURITY_INPUT!"=="" (
        REM user pressed Enter, default to false
        goto end_security
    )

    REM Normalize input
    set "input_lc="
    for %%A in (!DISABLE_SECURITY_INPUT!) do set "input_lc=%%~A"
    set "input_lc=!input_lc:~0,1!"

    if /I "!input_lc!"=="y" (
        set "DISABLE_SECURITY=true"
    ) else if /I "!input_lc!"=="n" (
        set "DISABLE_SECURITY=false"
    ) else (
        echo Invalid input. Please enter y or n.
        goto ask_security
    )

    :end_security

    > ".env.docker" (
        echo DEBUG=true
        echo DISABLE_SECURITY=!DISABLE_SECURITY!
        echo BASE_URL=http://localhost:3000
        echo JWT_SECRET_KEY=!KEY!
        echo JWT_ALGORITHM=HS256
        echo ADMIN_USER_IDS=!OSU_USER_ID!
        echo PRIVILEGED_USER_IDS=
        echo OSU_CLIENT_ID=!OSU_CLIENT_ID!
        echo OSU_CLIENT_SECRET=!OSU_CLIENT_SECRET!
        echo POSTGRESQL_HOST=graveboards-postgresql-dev
        echo POSTGRESQL_PORT=5432
        echo POSTGRESQL_USERNAME=postgres
        echo POSTGRESQL_PASSWORD=
        echo POSTGRESQL_DATABASE=
        echo REDIS_HOST=graveboards-redis-dev
        echo REDIS_PORT=6379
        echo REDIS_USERNAME=
        echo REDIS_PASSWORD=
        echo REDIS_DB=0
    )

    echo.
    echo ✅ .env.docker created with your credentials and a secure JWT secret.
    echo You have been added to ADMIN_USER_IDS as !OSU_USER_ID!.
    echo.
    pause
)

REM Step 2: Check Docker installation
where docker >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker is not installed or not in PATH. Please install Docker Desktop and try again.
    pause
    exit /b
)

REM Step 3: Check if Docker is running
docker info >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker daemon is not running. Please start Docker Desktop and try again.
    pause
    exit /b
)

REM Step 4: Start Docker Compose
echo.
echo 🚀 Starting Docker Compose...
docker-compose up --build

REM Step 5: Clean up on exit (this section is only reached if not streaming logs interactively)
echo.
echo 🧹 Shutting down Docker Compose...
docker-compose down
pause