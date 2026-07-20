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


def test_forecast_contract():
    client = TestClient(app)
    response = client.post("/forecast/solidos", json={"horizon_weeks": 4, "lookback_weeks": 8})
    assert response.status_code == 200
    payload = response.json()
    assert payload["model"]
    assert payload["horizon_weeks"] == 4
    assert len(payload["predictions"]) == 4
    assert {"week_start", "tallos_estimados", "modelo"} <= set(payload["predictions"][0])
