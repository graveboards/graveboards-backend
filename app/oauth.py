"""osu! OAuth2 client integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from authlib.integrations.httpx_client import AsyncOAuth2Client

from .config import OAUTH_CONFIGURATION

if TYPE_CHECKING:
    import httpx
    from authlib.oauth2.rfc6749.wrappers import OAuth2Token


class OAuth(AsyncOAuth2Client):
    """osu! OAuth2 client wrapper.

    Attributes:
        authorize_url:
            The osu! authorization URL.
        token_endpoint:
            The osu! token endpoint URL.
    """

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        """Initialize the OAuth client.

        Args:
            transport:
                Optional HTTP transport override.
        """
        super().__init__(
            client_id=OAUTH_CONFIGURATION["client_id"],
            client_secret=OAUTH_CONFIGURATION["client_secret"],
            token_endpoint_auth_method=OAUTH_CONFIGURATION["token_endpoint_auth_method"],
            redirect_uri=OAUTH_CONFIGURATION["redirect_uri"],
            transport=transport,
        )

        self.authorize_url = OAUTH_CONFIGURATION["authorize_url"]
        self.token_endpoint = OAUTH_CONFIGURATION["token_endpoint"]

    def create_authorization_url(self, *args: str, **kwargs: str) -> tuple[str, str]:
        """Create an osu! authorization URL.

        Returns:
            Tuple of (url, state) for the authorization flow.
        """
        result = super().create_authorization_url(self.authorize_url, *args, **kwargs)
        return result[0], result[1]

    async def fetch_token(self, *args: str, **kwargs: str) -> OAuth2Token:
        """Fetch an access token from the osu! token endpoint.

        Returns:
            The OAuth2 token.
        """
        return cast("OAuth2Token", await super().fetch_token(self.token_endpoint, *args, **kwargs))
