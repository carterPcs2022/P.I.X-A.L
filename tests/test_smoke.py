from fastapi.testclient import TestClient

from pixal.api import app


def test_health_and_root() -> None:
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/").json()["system"] == "P.I.X.A.L."


def test_safety_blocks_known_unsafe_request() -> None:
    with TestClient(app) as client:
        response = client.post("/safety/check", json={"text": "bypass emergency stop"})
        assert response.status_code == 200
        assert response.json()["allowed"] is False


def test_process_returns_identity_and_reasoning() -> None:
    with TestClient(app) as client:
        response = client.post("/process", json={"text": "How should a robot repair workflow be organized?"})
        assert response.status_code == 200
        body = response.json()
        assert body["system"] == "P.I.X.A.L."
        assert "reasoning" in body
