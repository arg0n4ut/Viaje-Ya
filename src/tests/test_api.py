import uuid


def test_read_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Welcome to Viaje-Ya"}


def test_get_all_trips(client):
    resp = client.get("/trips/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all("participants" in trip for trip in data)


def test_get_trip_by_id(client):
    trip_list = client.get("/trips/").json()
    trip_id = trip_list[0]["id"]

    resp = client.get(f"/trips/{trip_id}")
    assert resp.status_code == 200
    trip = resp.json()
    assert trip["id"] == trip_id
    assert isinstance(trip.get("participants"), list)


def test_get_trip_not_found(client):
    missing = str(uuid.uuid4())
    resp = client.get(f"/trips/{missing}")
    assert resp.status_code == 404


def test_create_trip(client):
    payload = {
        "name": "New Test Trip",
        "start_date": "2026-01-01",
        "end_date": "2026-01-05",
    }
    resp = client.post("/trips/", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == payload["name"]
    assert created["participants"] == []


def test_create_trip_with_participants(client):
    new_participant = client.post("/participants/", json={"name": "Bob"}).json()
    payload = {
        "name": "Trip With Participant",
        "start_date": "2026-02-01",
        "end_date": "2026-02-07",
        "participant_ids": [new_participant["id"]],
    }
    resp = client.post("/trips/", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert len(created["participants"]) == 1
    assert created["participants"][0]["id"] == new_participant["id"]


def test_get_all_participants(client):
    resp = client.get("/participants/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_participant_by_id(client):
    participant_id = client.get("/participants/").json()[0]["id"]
    resp = client.get(f"/participants/{participant_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == participant_id


def test_get_participant_not_found(client):
    missing = str(uuid.uuid4())
    resp = client.get(f"/participants/{missing}")
    assert resp.status_code == 404


def test_create_participant(client):
    payload = {"name": "Carol"}
    resp = client.post("/participants/", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == "Carol"
    assert "id" in created


def test_assign_participant_to_trip(client):
    trip = client.get("/trips/").json()[0]
    participant = client.post("/participants/", json={"name": "Dave"}).json()

    resp = client.post(f"/trips/{trip['id']}/participants/{participant['id']}")
    assert resp.status_code == 200
    updated = resp.json()
    assert any(p["id"] == participant["id"] for p in updated["participants"])


def test_assign_participant_missing_entities(client):
    existing_trip = client.get("/trips/").json()[0]["id"]
    missing_participant = uuid.uuid4()

    resp = client.post(f"/trips/{existing_trip}/participants/{missing_participant}")
    assert resp.status_code == 404

    missing_trip = uuid.uuid4()
    existing_participant = client.get("/participants/").json()[0]["id"]

    resp = client.post(f"/trips/{missing_trip}/participants/{existing_participant}")
    assert resp.status_code == 404


def test_remove_participant_from_trip(client):
    trip = client.get("/trips/").json()[0]
    participant_id = trip["participants"][0]["id"]

    resp = client.delete(f"/trips/{trip['id']}/participants/{participant_id}")
    assert resp.status_code == 200
    updated = resp.json()
    assert all(p["id"] != participant_id for p in updated["participants"])


def test_create_trip_with_unknown_participant(client):
    payload = {
        "name": "Invalid Trip",
        "start_date": "2026-03-01",
        "end_date": "2026-03-05",
        "participant_ids": [str(uuid.uuid4())],
    }
    resp = client.post("/trips/", json=payload)
    assert resp.status_code == 400
