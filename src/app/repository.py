from typing import List, Optional
from uuid import UUID
from . import database
from .models import *

# init db
if not hasattr(database, "trips") or database.trips is None:
    database.trips = {}
if not hasattr(database, "participants") or database.participants is None:
    database.participants = {}

class TripRepository:
    def get_all_trips(self) -> List[Trip]:
        return list(database.trips.values())

    def get_trip_by_id(self, trip_id: UUID) -> Optional[Trip]:
        return database.trips.get(trip_id)

    def create_trip(self, trip: Trip) -> Trip:
        database.trips[trip.id] = trip
        return trip
    
    def update_trip(self, trip_id: UUID, trip: Trip) -> Trip:
        database.trips[trip_id] = trip
        return trip

    def delete_trip(self, trip_id: UUID) -> None:
        del database.trips[trip_id]

class ParticipantRepository:
    def get_all_participants(self) -> List[Participant]:
        return list(database.participants.values())
    
    def get_participant_by_id(self, participant_id: UUID) -> Optional[Participant]:
        return database.participants.get(participant_id)
    
    def create_participant(self, participant: Participant) -> Participant:
        database.participants[participant.id] = participant
        return participant

    def update_participant(self, participant_id: UUID, participant: Participant) -> Participant:
        database.participants[participant_id] = participant
        return participant

    def delete_participant(self, participant_id: UUID) -> None:
        del database.participants[participant_id]

