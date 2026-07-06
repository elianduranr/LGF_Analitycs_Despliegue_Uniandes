from fastapi.testclient import TestClient

from app.main import app


def test_health_contract():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "data_dir" in payload
    assert "mlflow_tracking_uri" in payload
