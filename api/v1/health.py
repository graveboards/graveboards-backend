import os
import time
from datetime import datetime, timezone

from app.version import __version__
from app.database import PostgresqlDB
from app.redis import RedisClient
from app.utils import aware_utcnow

__all__ = ["health_check"]


async def health_check() -> dict:
    """Health check endpoint for Graveboards services.
    
    Returns the health status of all Graveboards services including PostgreSQL, Redis, 
    and optional osu! API connectivity.
    
    Returns:
        dict: Health status response
    """
    start_time = aware_utcnow()
    
    checks = {
        "database": {"status": "ok", "response_time_ms": 0, "message": "Connected"},
        "redis": {"status": "ok", "response_time_ms": 0, "message": "Connected"},
        "osu_api": {"status": "ok", "response_time_ms": 0, "message": "Connected"}
    }
    
    has_error = False
    degraded = False
    
    # Check PostgreSQL
    db = None
    db_start = time.time()
    try:
        db = PostgresqlDB()
        await db.test_connection()
        checks["database"]["response_time_ms"] = round((time.time() - db_start) * 1000, 2)
    except Exception as e:
        checks["database"]["status"] = "error"
        checks["database"]["message"] = str(e)
        has_error = True
    finally:
        if db is not None:
            await db.close()

    # Check Redis
    rc = None
    redis_start = time.time()
    try:
        rc = RedisClient()
        await rc.ping()
        checks["redis"]["response_time_ms"] = round((time.time() - redis_start) * 1000, 2)
    except Exception as e:
        checks["redis"]["status"] = "error"
        checks["redis"]["message"] = str(e)
        has_error = True
    finally:
        if rc is not None:
            await rc.aclose()
    
    # Check osu! API (optional - only if credentials available)
    try:
        from app.osu_api import OsuAPIClient
        
        if os.getenv("OSU_CLIENT_ID") and os.getenv("OSU_CLIENT_SECRET"):
            api_start = time.time()
            try:
                async with OsuAPIClient(rc) as client:
                    # Test API connectivity by fetching client credentials token
                    await client.refresh_token()
                    checks["osu_api"]["response_time_ms"] = round((time.time() - api_start) * 1000, 2)
            except Exception as e:
                checks["osu_api"]["status"] = "error"
                checks["osu_api"]["message"] = str(e)
                degraded = True
        else:
            checks["osu_api"]["status"] = "ok"
            checks["osu_api"]["message"] = "Skipped (no credentials)"
    except ImportError:
        checks["osu_api"]["status"] = "ok"
        checks["osu_api"]["message"] = "Not available"
    
    # Determine overall status
    if has_error:
        status = "unhealthy"
    elif degraded:
        status = "degraded"
    else:
        status = "healthy"
    
    return {
        "status": status,
        "timestamp": start_time.isoformat(),
        "version": __version__,
        "checks": checks
    }
