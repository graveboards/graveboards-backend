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


@pytest.mark.integration
def test_health_endpoint(TestClient):
    """Test GET /api/v1/health returns 200 with status field."""
    response = TestClient.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "checks" in data
    assert isinstance(data["checks"], dict)
