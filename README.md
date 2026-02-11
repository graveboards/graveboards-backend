# Graveboards Backend

## Quickstart (Docker)

1. Close the repository: `git clone https://github.com/graveboards/graveboards.git && cd graveboards`
2. Ensure docker is installed and running on your system
3. Launch `run.bat`
4. Follow the instructions to automatically fill out `.env.docker`
5. The backend should now be running on http://localhost:8000

## Installation (Non-docker)

### Prerequisites

- Python 3.14+

### Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/pianosuki/graveboards.git
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
    ```
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
    # Development mode:
     python main.py  # On Windows use: py main.py
    ```

## Documentation

The API spec can be viewed locally at: http://localhost:8000/api/v1/ui

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
