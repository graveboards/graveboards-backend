import pytest


@pytest.mark.e2e
def test_e2e_marker_enabled():
    """Verify that e2e marker works for test categorization."""
    assert True


@pytest.mark.e2e
def test_app_has_openapi_spec(TestClient):
    """Test that OpenAPI spec is available."""
    response = TestClient.get("/api/v1/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    assert "openapi" in spec
    assert "paths" in spec
    assert len(spec["paths"]) > 0


@pytest.mark.e2e
def test_cors_middleware_enabled(TestClient):
    """Test that CORS middleware is properly configured."""
    response = TestClient.options("/api/v1/health", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    })

    assert "access-control-allow-origin" in response.headers


@pytest.mark.e2e
def test_gzip_middleware_enabled(TestClient):
    """Test that GZip middleware is properly configured."""
    response = TestClient.get("/api/v1/openapi.json", headers={
        "Accept-Encoding": "gzip",
    })

    assert response.status_code == 200
    assert "gzip" in response.headers.get("content-encoding", "")
