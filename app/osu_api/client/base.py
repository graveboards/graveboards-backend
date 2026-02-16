import asyncio
import time

import httpx
from pydantic import ValidationError

from app.oauth import OAuth
from app.redis import RedisClient, Namespace
from app.redis.models import OsuClientOAuthToken
from app.exceptions import RedisLockTimeoutError
from app.logging import get_logger

MAX_TOKEN_FETCH_RETRIES = 3
logger = get_logger(__name__)


class OsuAPIClientBase:
    def __init__(self, rc: RedisClient):
        self.rc = rc
        self._oauth = OAuth()
        self._token: OsuClientOAuthToken | None = None

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
                if attempt < MAX_TOKEN_FETCH_RETRIES:
                    await asyncio.sleep(2 ** attempt)
                    continue

                raise TimeoutError(f"Failed to fetch token after {MAX_TOKEN_FETCH_RETRIES} retries due to ReadTimeout")

    async def get_auth_headers(self, access_token: str = None) -> dict:
        return {"Authorization": f"Bearer {access_token or await self.get_token()}"}

    @staticmethod
    def format_query_parameters(query_parameters: dict) -> str:
        parameter_strings = [f"{key}={value}" for key, value in query_parameters.items()]

        return f"?{"&".join(parameter_strings)}"
