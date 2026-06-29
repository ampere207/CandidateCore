from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_route():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

def test_pipeline_missing_payloads_error():
    # Sending empty request without required file multipart raises validation error
    response = client.post("/pipeline/run")
    assert response.status_code == 422
    assert "detail" in response.json()
