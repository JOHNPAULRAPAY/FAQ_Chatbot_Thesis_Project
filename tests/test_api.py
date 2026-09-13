"""
Integration tests for the /chat API endpoint.
"""
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_root_endpoint_returns_status():
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()


def test_chat_endpoint_returns_valid_response():
    response = client.post("/chat", json={"conversation_id": None, "message": "hi"})
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "reply" in data
    assert isinstance(data["conversation_id"], int)


def test_chat_endpoint_rejects_missing_message():
    # 'message' is a required field - omitting it should fail validation
    response = client.post("/chat", json={"conversation_id": None})
    assert response.status_code == 422


def test_chat_conversation_persists_across_requests():
    first = client.post("/chat", json={"conversation_id": None, "message": "hi"})
    conv_id = first.json()["conversation_id"]

    second = client.post("/chat", json={"conversation_id": conv_id, "message": "tuition"})
    assert second.status_code == 200
    assert second.json()["conversation_id"] == conv_id