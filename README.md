# Graveboards Backend

## Quickstart (Docker)
1. Close the repository: `git clone https://github.com/graveboards/graveboards-backend.git && cd graveboards`
2. Ensure docker is installed and running on your system
3. Launch the run script
   - `run.bat` (Windows)
   - `run.sh` (Linux)
4. Follow the instructions to automatically fill out `.env.docker`
5. The backend should now be running on http://localhost:8000

## Installation (Non-docker)

### Prerequisites

- Python 3.14+
- PostgreSQL
- Redis

### Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/graveboards/graveboards-backend.git
    cd graveboards
    ```

2. Create and activate a virtual environment:
    ```bash
    python -m venv venv  # On Windows use: py -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Create the `.env` file:
    ```shell
    ENV=dev
    DEBUG=true
    DISABLE_SECURITY=false
    BASE_URL=<frontend-base-url>  # http://localhost:3000
    JWT_SECRET_KEY=<private-encryption-key>
    JWT_ALGORITHM=<symmetric-algorithm>  # HS256
    ADMIN_USER_IDS=<comma-delimmed-osu-user-ids>  # 2,124493,873961 ...
    
    OSU_CLIENT_ID=<osu-oauth-client-id>
    OSU_CLIENT_SECRET=<osu-oauth-client-secret>
    
    POSTGRESQL_HOST=<db-host>  # localhost
    POSTGRESQL_PORT=<db-port>  # 5432
    POSTGRESQL_USERNAME=<db-username>  # postgres
    POSTGRESQL_PASSWORD=<db-password>
    POSTGRESQL_DATABASE=<db-dbname>
    
    REDIS_HOST=<redis-host>  # localhost
    REDIS_PORT=<redis-port>  # 6379
    REDIS_USERNAME=<redis-acl-username>
    REDIS_PASSWORD=<redis-acl-password>
    REDIS_DB=<redis-db-number>  # 0
    ```

5. Run the application:
    ```bash
     python main.py  # On Windows use: py main.py
    ```

## Management (docker)

A Makefile has been provided for quick and convenient maintenance:

```text
-------------Docker-------------
make up        - Start all services
make down      - Stop all services
make build     - Rebuild project image
make logs      - View backend logs
make shell     - Open backend shell
make wipe      - Destroy database volumes
------------Database------------
make status    - View database status
make reset     - Reset database
make seed      - Seed database
make fresh     - Reset & seed database      
```

## Management (non-docker)

Utilize the `manage.py` script to perform maintenance:

```text
usage: manage.py [-h] {status,reset,seed} ...

positional arguments:
  {status,reset,seed}
    status             View database status
    reset              Reset database
    seed               Seed database
```

## Documentation

The API spec can be viewed locally at: http://localhost:8000/api/v1/ui

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
