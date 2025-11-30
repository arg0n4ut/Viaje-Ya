def test_read_root(client):
    """Tests for successful response"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Viaje-Ya"}