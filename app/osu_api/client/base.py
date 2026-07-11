import asyncio
import time

import httpx
from pydantic import ValidationError

from app.oauth import OAuth
from app.redis import RedisClient, Namespace
from app.redis.models import OsuClientOAuthToken
from app.exceptions import RedisLockTimeoutError
from app.logging import get_logger
from app.observability.metrics.osu import (
    osu_api_requests_total,
    osu_api_request_duration_seconds,
    osu_api_errors_total,
)

MAX_TOKEN_FETCH_RETRIES = 3
logger = get_logger(__name__)


def _get_osu_endpoint(path: str) -> str:
    parts = path.strip("/").split("/")
    return "/".join("{id}" if p.isdigit() else p for p in parts)


class OsuAPIMetricsTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport: httpx.AsyncBaseTransport) -> None:
        self._transport = transport

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        endpoint = _get_osu_endpoint(request.url.path)
        start = time.perf_counter()

        try:
            response = await self._transport.handle_async_request(request)
            duration = time.perf_counter() - start

            osu_api_requests_total.labels(
                endpoint=endpoint,
                status_code=str(response.status_code),
            ).inc()

            osu_api_request_duration_seconds.labels(endpoint=endpoint).observe(duration)

            if response.is_error:
                # Callers raise_for_status() well after the transport returns, so a
                # 4xx/5xx from osu! itself never reaches the `except` clause below.
                # Record it here, using the same error_type that raise_for_status()
                # would itself raise, so this lines up with the transport-exception case.
                osu_api_errors_total.labels(
                    endpoint=endpoint,
                    error_type="HTTPStatusError",
                ).inc()

            return response
        except Exception as exc:
            duration = time.perf_counter() - start
            osu_api_errors_total.labels(
                endpoint=endpoint,
                error_type=type(exc).__name__,
            ).inc()
            raise


class OsuAPIClientBase:
    def __init__(self, rc: RedisClient):
        self.rc = rc
        # Separate transport/connection pool from _http_client, but instrumented the
        # same way, so oauth/token requests show up in osu_api_* metrics too - a stalled
        # or failing token refresh takes down every other osu! API call with it.
        self._oauth = OAuth(transport=OsuAPIMetricsTransport(httpx.AsyncHTTPTransport()))
        self._token: OsuClientOAuthToken | None = None
        self._http_client = httpx.AsyncClient(
            transport=OsuAPIMetricsTransport(httpx.AsyncHTTPTransport()),
            timeout=httpx.Timeout(10.0, connect=5.0)
        )

    async def get_token(self) -> str:
        async def get_valid_token_from_redis() -> OsuClientOAuthToken | None:
            serialized_token = await self.rc.hgetall(Namespace.OSU_CLIENT_OAUTH_TOKEN.value)

            if serialized_token:
                try:
                    token_ = OsuClientOAuthToken.deserialize(serialized_token)

                    if token_.expires_at > time.time():
                        return token_
                except (ValidationError, ValueError) as e:
                    logger.warning(f"Error when deserializing from redis cache: {e}, falling back to refreshing token")

            return None

        if self._token and self._token.expires_at > time.time():
            return self._token.access_token

        lock_hash_name = Namespace.LOCK.hash_name(Namespace.OSU_CLIENT_OAUTH_TOKEN.value)

        try:
            async with self.rc.lock_ctx(lock_hash_name):
                if token := await get_valid_token_from_redis():
                    self._token = token
                    return token.access_token

                await self.refresh_token()
        except RedisLockTimeoutError:
            # Prevent stampede: wait briefly and re-check Redis before refreshing
            await asyncio.sleep(0.5)

            if token := await get_valid_token_from_redis():
                self._token = token
                return token.access_token

            await self.refresh_token()

        return self._token.access_token

    async def refresh_token(self):
        for attempt in range(MAX_TOKEN_FETCH_RETRIES):
            try:
                token_dict = await self._oauth.fetch_token(grant_type="client_credentials", scope="public")
                token = OsuClientOAuthToken.model_validate(token_dict)
                await self.rc.hset(Namespace.OSU_CLIENT_OAUTH_TOKEN.value, mapping=token.serialize())
                self._token = token
                return
            except httpx.ReadTimeout:
                if attempt < MAX_TOKEN_FETCH_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue

                raise TimeoutError(f"Failed to fetch token after {MAX_TOKEN_FETCH_RETRIES} retries due to ReadTimeout")

    async def get_auth_headers(self, access_token: str = None) -> dict:
        return {"Authorization": f"Bearer {access_token or await self.get_token()}"}

    async def close(self) -> None:
        await self._http_client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    @staticmethod
    def format_query_parameters(query_parameters: dict) -> str:
        from urllib.parse import urlencode

        return f"?{urlencode(query_parameters)}"
