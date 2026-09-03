"""Base osu! API client with rate limiting and token management."""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any, Self, cast

import httpx
from pydantic import ValidationError

from app.config import CONFIG
from app.exceptions import RateLimitExceededError, RedisLockTimeoutError
from app.oauth import OAuth
from app.observability.logging import get_logger
from app.observability.metrics.osu import (
    osu_api_errors_total,
    osu_api_rate_limited_total,
    osu_api_request_duration_seconds,
    osu_api_requests_total,
)
from app.redis_client import Namespace, RedisClient
from app.redis_client.models import OsuClientOAuthToken

if TYPE_CHECKING:
    from types import TracebackType

MAX_TOKEN_FETCH_RETRIES = 3
logger = get_logger(__name__)


# --- Global outbound osu! API rate gate -------------------------------------
# Every request to osu.ppy.sh flows through OsuAPIMetricsTransport
# (the API client, the OAuth token refresh transport, and .osu downloads), so a
# single in-process gate here enforces a hard minimum interval between any two
# osu! API requests regardless of caller. This is the backstop that keeps
# concurrent services (health checks, daemons, web requests) from piling up.

_osu_api_gate_lock = asyncio.Lock()
_osu_api_last_request_monotonic: float = 0.0


async def _enforce_osu_api_global_interval() -> None:
    """Sleep so consecutive osu! API requests are spaced >= CONFIG's minimum."""
    min_interval = CONFIG.OSU_API_MIN_INTERVAL_SECONDS
    if min_interval <= 0:
        return

    global _osu_api_last_request_monotonic
    async with _osu_api_gate_lock:
        now = time.monotonic()
        wait = _osu_api_last_request_monotonic + min_interval - now
        if wait > 0:
            await asyncio.sleep(wait)
        _osu_api_last_request_monotonic = time.monotonic()


def _get_osu_endpoint(path: str) -> str:
    parts = path.strip("/").split("/")
    return "/".join("{id}" if p.isdigit() else p for p in parts)


def is_rate_limit_response(payload: dict[str, Any]) -> bool:
    """Detect an upstream rate-limit response body.

    osu!'s CDN (Cloudflare) answers with HTTP 429 and a JSON body that omits the
    standard OAuth ``error`` field (e.g. ``error_code: 1015``), so authlib parses
    it as a successful token response. This detects those bodies so callers can
    back off instead of treating them as tokens.

    Args:
        payload:
            A parsed JSON response body.

    Returns:
        ``True`` if the response indicates an upstream rate limit.
    """
    return (
        payload.get("status") == 429
        or payload.get("error_code") is not None
        or payload.get("error_name") == "rate_limited"
        or payload.get("cloudflare_error") is True
    )


class OsuAPIMetricsTransport(httpx.AsyncBaseTransport):
    """HTTP transport that instruments osu! API requests with Prometheus metrics."""

    def __init__(self, transport: httpx.AsyncBaseTransport) -> None:
        """Initialize with an underlying transport.

        Args:
            transport:
                The HTTP transport to wrap.
        """
        self._transport = transport

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """Handle an HTTP request with metrics instrumentation.

        Args:
            request:
                The HTTP request.

        Returns:
            The HTTP response.
        """
        endpoint = _get_osu_endpoint(request.url.path)
        start = time.perf_counter()

        # Global spacing gate: cap osu! API request throughput across all
        # transports/callers in this process (see _enforce_osu_api_global_interval).
        await _enforce_osu_api_global_interval()

        try:
            response = await self._transport.handle_async_request(request)
            duration = time.perf_counter() - start

            osu_api_requests_total.labels(
                endpoint=endpoint,
                status_code=str(response.status_code),
            ).inc()

            osu_api_request_duration_seconds.labels(endpoint=endpoint).observe(duration)

            if response.status_code == 429:
                # Upstream rate limiting is a throttling signal, not a failure:
                # track it separately so it can't inflate the structured-error
                # ratio or fire OsuApiErrorTypeRatioHigh while the app backs off.
                osu_api_rate_limited_total.labels(endpoint=endpoint).inc()
            elif response.is_error:
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
    """Base class for osu! API clients with rate limiting and token management.

    Attributes:
        rc:
            Redis client for caching and distributed locking.
    """

    def __init__(self, rc: RedisClient):
        """Initialize the base client.

        Args:
            rc:
                Redis client for caching and distributed locking.
        """
        self.rc = rc
        # Separate transport/connection pool from _http_client, but instrumented the
        # same way, so oauth/token requests show up in osu_api_* metrics too - a stalled
        # or failing token refresh takes down every other osu! API call with it.
        self._oauth = OAuth(transport=OsuAPIMetricsTransport(httpx.AsyncHTTPTransport()))
        self._token: OsuClientOAuthToken | None = None
        self._http_client = httpx.AsyncClient(
            transport=OsuAPIMetricsTransport(httpx.AsyncHTTPTransport()),
            timeout=httpx.Timeout(10.0, connect=5.0),
        )

    async def get_token(self) -> str:
        """Get a valid access token, refreshing if necessary.

        Returns:
            A valid osu! API access token.
        """

        async def get_valid_token_from_redis() -> OsuClientOAuthToken | None:
            serialized_token = await self.rc.hgetall(Namespace.OSU_CLIENT_OAUTH_TOKEN.value)

            if serialized_token:
                try:
                    token_ = OsuClientOAuthToken.deserialize(serialized_token)

                    if token_.expires_at > time.time():
                        return token_
                except (ValidationError, ValueError) as e:
                    logger.warning(
                        f"Error when deserializing from redis cache: {e}, falling back to refreshing token"
                    )

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

        if self._token is None:
            raise RuntimeError("osu client oauth token is missing after refresh attempts")
        return self._token.access_token

    async def refresh_token(self) -> None:
        """Refresh the OAuth token from the osu! API.

        Raises:
            TimeoutError:
                If token refresh fails after all retries.
            RateLimitExceededError:
                If osu! keeps rate-limiting the client after all retries.
        """
        for attempt in range(MAX_TOKEN_FETCH_RETRIES):
            try:
                token_dict = await self._oauth.fetch_token(
                    grant_type="client_credentials", scope="public"
                )
                if not isinstance(token_dict, dict) or "access_token" not in token_dict:
                    if is_rate_limit_response(token_dict):
                        payload = cast("dict[str, Any]", token_dict)
                        retry_after = int(payload.get("retry_after") or 30)
                        if attempt < MAX_TOKEN_FETCH_RETRIES - 1:
                            logger.warning(
                                f"osu! is rate limiting this client (attempt {attempt + 1}/"
                                f"{MAX_TOKEN_FETCH_RETRIES}); retrying in {retry_after}s"
                            )
                            await asyncio.sleep(retry_after)
                            continue

                        raise RateLimitExceededError from None

                    logger.warning(
                        f"Unexpected osu! token response without access_token: "
                        f"{sorted(token_dict)[:6]}"
                    )
                    if attempt < MAX_TOKEN_FETCH_RETRIES - 1:
                        await asyncio.sleep(2**attempt)
                        continue

                    raise RuntimeError(
                        "Failed to refresh osu! client token: unexpected response"
                    ) from None

                token = OsuClientOAuthToken.model_validate(token_dict)
                await self.rc.hset(
                    Namespace.OSU_CLIENT_OAUTH_TOKEN.value, mapping=token.serialize()
                )
                self._token = token
                return
            except httpx.ReadTimeout:
                if attempt < MAX_TOKEN_FETCH_RETRIES - 1:
                    await asyncio.sleep(2**attempt)
                    continue

                raise TimeoutError(
                    f"Failed to fetch token after {MAX_TOKEN_FETCH_RETRIES} retries due to ReadTimeout"
                ) from None

    async def invalidate_token(self) -> None:
        """Evict the cached client token from memory and Redis.

        Called when osu! rejects the token with 401 so the next request mints a
        fresh one. osu! can revoke outstanding tokens server-side (e.g. when
        the OAuth client is rotated) long before their locally recorded expiry.
        """
        self._token = None
        await self.rc.delete(Namespace.OSU_CLIENT_OAUTH_TOKEN.value)

    async def get_auth_headers(self, access_token: str | None = None) -> dict[str, str]:
        """Build authorization headers with a valid access token.

        Args:
            access_token:
                Optional token to use instead of fetching a new one.

        Returns:
            Dictionary with the Authorization header.
        """
        return {"Authorization": f"Bearer {access_token or await self.get_token()}"}

    async def _authorized_request(
        self,
        method: str,
        url: str,
        *,
        access_token: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Send an authenticated osu! API request.

        When the default client-credentials token is rejected with 401, the
        cached token is evicted (memory + Redis) and the request is retried
        once with a freshly minted token. Without this, a token that was
        revoked server-side while still unexpired locally (e.g. after the
        OAuth client was rotated) poisons every request until the cache
        expires.

        Explicit tokens (the user OAuth flow) are never retried: a 401 there
        means the user must re-authorize, refreshing the client token cannot
        help.

        Args:
            method:
                HTTP method.
            url:
                Target URL.
            access_token:
                Optional explicit token to use instead of the client token.
            **kwargs:
                Forwarded to the HTTP client (e.g. ``json`` for POST bodies).

        Returns:
            The HTTP response.
        """
        request_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(access_token),
        }

        response = await self._http_client.request(method, url, headers=request_headers, **kwargs)

        if access_token is None and response.status_code == 401:
            logger.warning(
                "osu! API rejected the client token with 401; "
                "evicting cached token and retrying once with a fresh one"
            )
            await self.invalidate_token()

            request_headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                **await self.get_auth_headers(),
            }
            response = await self._http_client.request(
                method, url, headers=request_headers, **kwargs
            )

        return response

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http_client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    @staticmethod
    def format_query_parameters(query_parameters: dict[str, Any]) -> str:
        """Format query parameters as a URL query string.

        Args:
            query_parameters:
                Dictionary of query parameters.

        Returns:
            Query string prefixed with ``?``.
        """
        from urllib.parse import urlencode

        return f"?{urlencode(query_parameters)}"
