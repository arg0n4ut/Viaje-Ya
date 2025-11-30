import uuid
import pytest
import mongomock
from fastapi.testclient import TestClient

from app.main import app
from app import database
from app.models import Participant, Trip
from app.repository import ParticipantRepository, TripRepository


@pytest.fixture
def client():
    mongo_client = mongomock.MongoClient(uuidRepresentation="standard")
    database.set_client(mongo_client)
    database.clear_database()

    participant_repo = ParticipantRepository()
    trip_repo = TripRepository()

    participant = Participant(id=uuid.uuid4(), name="Alice")
    participant_repo.create_participant(participant)

    trip = Trip(
        id=uuid.uuid4(),
        name="Test Trip",
        start_date="2025-12-01",
        end_date="2025-12-10",
    )
    trip_repo.create_trip(trip, participant_ids=[participant.id])

    with TestClient(app) as test_client:
        yield test_client

    database.set_client(None)
