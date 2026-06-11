"""
Integration tests for POST /api/v1/token endpoint.

Tests the token exchange flow with mocked OAuth and osu! API calls.
"""
import pytest

from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone

from app.redis import Namespace, RedisClient
from app.oauth import OAuth
from app.osu_api import OsuAPIClient


class TestTokenPostEndpoint:
    """Integration tests for POST /api/v1/token endpoint."""

    TEST_USER_ID = 12345678
    TEST_STATE = "test_csrf_state_12345"
    TEST_ACCESS_TOKEN = "test_access_token_xyz"
    TEST_REFRESH_TOKEN = "test_refresh_token_abc"
    TEST_EXPIRES_AT = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())

    @pytest.fixture
    def valid_oauth_token(self):
        """Return a valid OAuth token response."""
        return {
            "access_token": self.TEST_ACCESS_TOKEN,
            "refresh_token": self.TEST_REFRESH_TOKEN,
            "expires_at": self.TEST_EXPIRES_AT,
        }

    @pytest.fixture
    def valid_user_data(self):
        """Return valid osu! user data."""
        return {
            "id": self.TEST_USER_ID,
            "username": "test_user",
            "avatar_url": "https://example.com/avatar.png",
        }

    async def _create_mock_oauth(self, token_response=None):
        """Create a mock OAuth instance for testing."""
        mock_oauth = MagicMock()
        mock_oauth.fetch_token = AsyncMock(return_value=token_response or {
            "access_token": self.TEST_ACCESS_TOKEN,
            "refresh_token": self.TEST_REFRESH_TOKEN,
            "expires_at": self.TEST_EXPIRES_AT,
        })
        return mock_oauth

    async def _create_mock_osu_api_client(self, user_data=None):
        """Create a mock OsuAPIClient for testing."""
        mock_rc = MagicMock(spec=RedisClient)
        mock_client = MagicMock(spec=OsuAPIClient)
        mock_client.rc = mock_rc
        mock_client.get_own_data = AsyncMock(return_value=user_data or {
            "id": self.TEST_USER_ID,
            "username": "test_user",
            "avatar_url": "https://example.com/avatar.png",
        })
        return mock_client

    async def _create_mock_redis(self):
        """Create a mock Redis client."""
        mock_rc = AsyncMock(spec=RedisClient)
        mock_rc.getdel = AsyncMock(return_value="valid")
        return mock_rc

    async def _create_mock_db(self):
        """Create a mock database session."""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock()
        mock_db.add = AsyncMock()
        mock_db.update = AsyncMock()
        return mock_db

    async def _call_post_token(self, body, **kwargs):
        """Call the post token function with dependencies."""
        from api.v1.token import post
        return await post(body=body, **kwargs)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_token_success(
        self,
        TestClient,
        valid_oauth_token,
        valid_user_data,
    ):
        """Test successful token exchange with mocked OAuth and osu! API."""
        mock_oauth = await self._create_mock_oauth(valid_oauth_token)
        mock_osu_client = await self._create_mock_osu_api_client(valid_user_data)
        mock_rc = await self._create_mock_redis()
        mock_db = await self._create_mock_db()

        result = await self._call_post_token(
            body={"code": "test_code", "state": self.TEST_STATE},
            oauth=mock_oauth,
            osu_api_client=mock_osu_client,
            rc=mock_rc,
            db=mock_db,
        )
        
        assert result[1] == 201
        assert "token" in result[0]
        assert len(result[0]["token"]) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_token_missing_code(self):
        """Test POST /api/v1/token with missing code."""
        from api.v1.token import post
        from app.exceptions import BadRequest
        
        mock_oauth = await self._create_mock_oauth()
        mock_osu_client = await self._create_mock_osu_api_client()
        mock_rc = await self._create_mock_redis()
        mock_db = await self._create_mock_db()
        
        try:
            await post(
                body={"state": self.TEST_STATE},
                oauth=mock_oauth,
                osu_api_client=mock_osu_client,
                rc=mock_rc,
                db=mock_db,
            )
            assert False, "Expected BadRequest exception"
        except BadRequest as e:
            assert "Missing code" in str(e)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_token_missing_state(self):
        """Test POST /api/v1/token with missing state."""
        from api.v1.token import post
        from app.exceptions import BadRequest
        
        mock_oauth = await self._create_mock_oauth()
        mock_osu_client = await self._create_mock_osu_api_client()
        mock_rc = await self._create_mock_redis()
        mock_db = await self._create_mock_db()
        
        try:
            await post(
                body={"code": "test_code"},
                oauth=mock_oauth,
                osu_api_client=mock_osu_client,
                rc=mock_rc,
                db=mock_db,
            )
            assert False, "Expected BadRequest exception"
        except BadRequest as e:
            assert "Missing state" in str(e)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_token_invalid_state(self):
        """Test POST /api/v1/token with invalid state."""
        from api.v1.token import post
        from app.exceptions import BadRequest
        
        mock_oauth = await self._create_mock_oauth()
        mock_osu_client = await self._create_mock_osu_api_client()
        mock_rc = await self._create_mock_redis()
        mock_rc.getdel = AsyncMock(return_value=None)
        mock_db = await self._create_mock_db()
        
        try:
            await post(
                body={"code": "test_code", "state": "invalid_state"},
                oauth=mock_oauth,
                osu_api_client=mock_osu_client,
                rc=mock_rc,
                db=mock_db,
            )
            assert False, "Expected BadRequest exception"
        except BadRequest as e:
            assert "Invalid or expired state" in str(e)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_post_token_oauth_error(self, valid_user_data):
        """Test POST /api/v1/token with OAuth error."""
        from api.v1.token import post
        from authlib.integrations.base_client.errors import OAuthError
        from app.exceptions import OsuOAuthError
        
        mock_oauth = AsyncMock()
        mock_oauth.fetch_token.side_effect = OAuthError(
            error="invalid_request",
            description="Authorization code has expired",
        )
        mock_osu_client = await self._create_mock_osu_api_client(valid_user_data)
        mock_rc = await self._create_mock_redis()
        mock_db = await self._create_mock_db()
        
        try:
            await post(
                body={"code": "expired_code", "state": self.TEST_STATE},
                oauth=mock_oauth,
                osu_api_client=mock_osu_client,
                rc=mock_rc,
                db=mock_db,
            )
            assert False, "Expected OsuOAuthError exception"
        except OsuOAuthError:
            pass



