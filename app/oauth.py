from typing import Literal

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.auth import OAuth2Token

from .config import OAUTH_CONFIGURATION


class OAuth(AsyncOAuth2Client):
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        super().__init__(
            client_id=OAUTH_CONFIGURATION["client_id"],
            client_secret=OAUTH_CONFIGURATION["client_secret"],
            token_endpoint_auth_method=OAUTH_CONFIGURATION["token_endpoint_auth_method"],
            redirect_uri=OAUTH_CONFIGURATION["redirect_uri"],
            transport=transport,
        )

        self.authorize_url = OAUTH_CONFIGURATION["authorize_url"]
        self.token_endpoint = OAUTH_CONFIGURATION["token_endpoint"]

    def create_authorization_url(self, *args, **kwargs) -> tuple[Literal[b""], str]:
        return super().create_authorization_url(self.authorize_url, *args, **kwargs)

    async def fetch_token(self, *args, **kwargs) -> OAuth2Token:
        return await super().fetch_token(self.token_endpoint, *args, **kwargs)
