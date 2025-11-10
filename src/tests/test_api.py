import uuid
import pytest

# tests use the 'client' fixture defined in conftest.py

def test_read_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Welcome to Viaje-Ya"}

def test_get_all_trips(client):
    resp = client.get("/trips/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # fixture inserts one trip
    assert len(data) >= 1
    assert all("id" in t and "name" in t for t in data)

def test_get_trip_by_id(client):
    resp = client.get("/trips/")
    trip_list = resp.json()
    trip_id = trip_list[0]["id"]

    resp = client.get(f"/trips/{trip_id}")
    assert resp.status_code == 200
    trip = resp.json()
    assert trip["id"] == trip_id
    assert "name" in trip

def test_get_trip_not_found(client):
    missing = str(uuid.uuid4())
    resp = client.get(f"/trips/{missing}")
    assert resp.status_code == 404

def test_create_trip(client):
    payload = {
        "name": "New Test Trip",
        "start_date": "2026-01-01",
        "end_date": "2026-01-05"
    }
    resp = client.post("/trips/", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == payload["name"]
    assert "id" in created

def test_get_all_participants(client):
    resp = client.get("/participants/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # fixture inserts one sample participant
    assert len(data) >= 1
    assert all("id" in p and "name" in p for p in data)

def test_get_participant_by_id(client):
    resp = client.get("/participants/")
    participants = resp.json()
    participant_id = participants[0]["id"]

    resp = client.get(f"/participants/{participant_id}")
    assert resp.status_code == 200
    p = resp.json()
    assert p["id"] == participant_id
    assert "name" in p

def test_get_participant_not_found(client):
    missing = str(uuid.uuid4())
    resp = client.get(f"/participants/{missing}")
    assert resp.status_code == 404

def test_create_participant(client):
    payload = {"name": "Bob"}
    resp = client.post("/participants/", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == "Bob"
    assert "id" in created
