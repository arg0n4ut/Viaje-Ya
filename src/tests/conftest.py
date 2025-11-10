from fastapi.testclient import TestClient
import pytest
from app.main import app, get_trip_repository, get_participant_repository
from app.repository import TripRepository, ParticipantRepository
from app import database
from app.models import Trip, Participant
import uuid

@pytest.fixture
def client():
    # init clean db
    if not hasattr(database, "trips") or database.trips is None:
        database.trips = {}
    if not hasattr(database, "participants") or database.participants is None:
        database.participants = {}
    database.trips.clear()
    database.participants.clear()

    # sample participant
    participant = Participant(id=uuid.uuid4(), name="Alice")
    database.participants[participant.id] = participant

    # sample trip w participant
    trip = Trip(id=uuid.uuid4(), name="Test Trip", start_date="2025-12-01", end_date="2025-12-10", participants=[participant])
    database.trips[trip.id] = trip

    def _get_test_trip_repo():
        return TripRepository()

    def _get_test_participant_repo():
        return ParticipantRepository()

    app.dependency_overrides[get_trip_repository] = _get_test_trip_repo
    app.dependency_overrides[get_participant_repository] = _get_test_participant_repo

    with TestClient(app) as c:
        yield c

    # clear everything
    app.dependency_overrides.clear()
    database.trips.clear()
    database.participants.clear()
