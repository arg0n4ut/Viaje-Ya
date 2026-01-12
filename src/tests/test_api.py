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


def test_add_task_to_trip(client):
    trip = client.get("/trips/").json()[0]
    participant = trip["participants"][0]
    payload = {"description": "Pack tent", "participant_id": participant["id"]}

    resp = client.post(f"/trips/{trip['id']}/tasks/", json=payload)
    assert resp.status_code == 201
    task = resp.json()
    assert task["description"] == "Pack tent"
    assert task["participant_id"] == participant["id"]
    assert task["done"] is False


def test_mark_task_done(client):
    trip = client.get("/trips/").json()[0]
    participant_id = trip["participants"][0]["id"]
    create_resp = client.post(
        f"/trips/{trip['id']}/tasks/",
        json={"description": "Pack food", "participant_id": participant_id},
    )
    task_id = create_resp.json()["id"]

    mark_resp = client.post(
        f"/trips/{trip['id']}/tasks/{task_id}/done",
        json={"participant_id": participant_id},
    )
    assert mark_resp.status_code == 200
    task = mark_resp.json()
    assert task["id"] == task_id
    assert task["done"] is True


def test_remove_task_from_trip(client):
    trip = client.get("/trips/").json()[0]
    participant_id = trip["participants"][0]["id"]
    create_resp = client.post(
        f"/trips/{trip['id']}/tasks/",
        json={"description": "Pack stove", "participant_id": participant_id},
    )
    task_id = create_resp.json()["id"]

    delete_resp = client.delete(
        f"/trips/{trip['id']}/tasks/{task_id}",
        params={"participant_id": participant_id},
    )
    assert delete_resp.status_code == 204

    updated_trip = client.get(f"/trips/{trip['id']}").json()
    assert all(t.get("id") != task_id for t in updated_trip.get("tasks", []))


def test_task_participant_not_found(client):
    trip = client.get("/trips/").json()[0]
    payload = {"description": "Pack water", "participant_id": str(uuid.uuid4())}
    resp = client.post(f"/trips/{trip['id']}/tasks/", json=payload)
    assert resp.status_code == 404


def test_list_tasks_for_trip(client):
    trip = client.get("/trips/").json()[0]
    tasks_resp = client.get(f"/trips/{trip['id']}/tasks/")
    assert tasks_resp.status_code == 200
    tasks = tasks_resp.json()
    assert isinstance(tasks, list)


def test_list_tasks_trip_not_found(client):
    missing_trip = str(uuid.uuid4())
    resp = client.get(f"/trips/{missing_trip}/tasks/")
    assert resp.status_code == 404


def test_propose_destination_and_list(client):
    trip = client.get("/trips/").json()[0]
    participant_id = trip["participants"][0]["id"]
    payload = {"title": "Paris", "description": "City trip", "participant_id": participant_id}

    create_resp = client.post(f"/trips/{trip['id']}/proposals/", json=payload)
    assert create_resp.status_code == 201
    proposal = create_resp.json()
    assert proposal["title"] == "Paris"
    assert proposal["participant_id"] == participant_id
    assert proposal["upvotes"] == []

    list_resp = client.get(f"/trips/{trip['id']}/proposals/")
    assert list_resp.status_code == 200
    proposals = list_resp.json()
    assert any(p["id"] == proposal["id"] for p in proposals)


def test_upvote_proposal_once_per_participant(client):
    trip = client.get("/trips/").json()[0]
    participant_id = trip["participants"][0]["id"]
    create_resp = client.post(
        f"/trips/{trip['id']}/proposals/",
        json={"title": "Berlin", "description": "Food tour", "participant_id": participant_id},
    )
    proposal_id = create_resp.json()["id"]

    first_vote = client.post(
        f"/trips/{trip['id']}/proposals/{proposal_id}/upvote",
        json={"participant_id": participant_id},
    )
    assert first_vote.status_code == 200
    assert len(first_vote.json()["upvotes"]) == 1

    second_vote = client.post(
        f"/trips/{trip['id']}/proposals/{proposal_id}/upvote",
        json={"participant_id": participant_id},
    )
    assert second_vote.status_code == 200
    assert len(second_vote.json()["upvotes"]) == 1  # no duplicate vote


def test_delete_proposal(client):
    trip = client.get("/trips/").json()[0]
    participant_id = trip["participants"][0]["id"]
    create_resp = client.post(
        f"/trips/{trip['id']}/proposals/",
        json={"title": "Rome", "description": "Colosseum", "participant_id": participant_id},
    )
    proposal_id = create_resp.json()["id"]

    delete_resp = client.delete(
        f"/trips/{trip['id']}/proposals/{proposal_id}",
        params={"participant_id": participant_id},
    )
    assert delete_resp.status_code == 204

    proposals = client.get(f"/trips/{trip['id']}/proposals/").json()
    assert all(p["id"] != proposal_id for p in proposals)


def test_proposal_participant_validation(client):
    trip = client.get("/trips/").json()[0]
    payload = {"title": "Tokyo", "description": "Sushi tour", "participant_id": str(uuid.uuid4())}

    resp = client.post(f"/trips/{trip['id']}/proposals/", json=payload)
    assert resp.status_code == 404
