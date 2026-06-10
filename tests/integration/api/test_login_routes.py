import pytest



@pytest.mark.integration
@pytest.mark.skip(reason="Requires Redis in request.state (full app setup needed)")
def test_login_endpoint_returns_authorization_url(TestClient):
    response = TestClient.get("/api/v1/login")

    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "https://osu.ppy.sh/oauth/authorize" in data["authorization_url"]
    assert "state" in data
