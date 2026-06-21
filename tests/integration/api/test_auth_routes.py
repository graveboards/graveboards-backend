import pytest

from app.oauth import OAuth
from app.redis import RedisClient, Namespace
from app.security import create_token_payload, encode_token


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_flow_returns_authorization_url():
    oauth = OAuth()
    authorization_url, state = oauth.create_authorization_url()

    assert "https://osu.ppy.sh/oauth/authorize" in authorization_url
    assert state is not None
    assert len(state) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_csrf_state_is_validated():
    from unittest.mock import AsyncMock
    
    rc = AsyncMock(spec=RedisClient)
    rc.set = AsyncMock(return_value=True)
    rc.get = AsyncMock(return_value="valid")
    rc.delete = AsyncMock(return_value=True)
    
    oauth = OAuth()
    authorization_url, state = oauth.create_authorization_url()

    state_hash_name = Namespace.CSRF_STATE.hash_name(state)
    await rc.set(state_hash_name, "valid", ex=300)

    stored = await rc.get(state_hash_name)
    assert stored == "valid"

    await rc.delete(state_hash_name)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jwt_token_generation():
    payload = create_token_payload(12345678)
    token = encode_token(payload)

    assert token is not None
    assert len(token) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_jwt_token_validation():
    payload = create_token_payload(12345678)
    token = encode_token(payload)

    from app.security import validate_token
    decoded = validate_token(token)

    assert decoded["sub"] == 12345678


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_token_raises_error():
    from app.security import validate_token
    from jwt.exceptions import InvalidTokenError

    with pytest.raises(InvalidTokenError):
        validate_token("invalid.token.here")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expired_token_raises_error():
    from app.security import create_token_payload, encode_token
    import time
    from jwt.exceptions import ExpiredSignatureError

    payload = create_token_payload(12345678)
    payload["exp"] = int(time.time()) - 3600
    token = encode_token(payload)

    from app.security import validate_token

    with pytest.raises(ExpiredSignatureError):
        validate_token(token)
