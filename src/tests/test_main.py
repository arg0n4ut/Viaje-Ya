from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

def test_read_root():
    """Tests for successful response"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Viaje-Ya"}