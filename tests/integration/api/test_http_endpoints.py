import pytest


@pytest.mark.integration
def test_login_endpoint(TestClient):
    """Test login endpoint via HTTP using minimal TestClient fixture."""
    response = TestClient.get("/api/v1/login")

    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "https://osu.ppy.sh/oauth/authorize" in data["authorization_url"]
    assert "state" in data
