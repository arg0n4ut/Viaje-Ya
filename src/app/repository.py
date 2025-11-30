from typing import List, Optional
from uuid import UUID
from pymongo.collection import Collection
from . import database
from .models import Participant, Trip


class ParticipantRepository:
    def __init__(self, collection: Optional[Collection] = None) -> None:
        self._collection = collection or database.get_participant_collection()

    def _participant_from_doc(self, doc: dict) -> Participant:
        return Participant(id=UUID(doc["_id"]), name=doc["name"])

    def get_all_participants(self) -> List[Participant]:
        return [self._participant_from_doc(doc) for doc in self._collection.find()]

    def get_participant_by_id(self, participant_id: UUID) -> Optional[Participant]:
        doc = self._collection.find_one({"_id": str(participant_id)})
        return self._participant_from_doc(doc) if doc else None

    def get_participants_by_ids(self, participant_ids: List[UUID]) -> List[Participant]:
        if not participant_ids:
            return []
        id_strings = [str(pid) for pid in participant_ids]
        docs = self._collection.find({"_id": {"$in": id_strings}})
        participants = {doc["_id"]: self._participant_from_doc(doc) for doc in docs}
        return [participants[id_str] for id_str in id_strings if id_str in participants]

    def create_participant(self, participant: Participant) -> Participant:
        doc = {"_id": str(participant.id), "name": participant.name}
        if self._collection.find_one({"_id": doc["_id"]}):
            raise ValueError("Participant with this ID already exists")
        self._collection.insert_one(doc)
        return self._participant_from_doc(doc)

    def update_participant(self, participant_id: UUID, participant: Participant) -> Optional[Participant]:
        result = self._collection.update_one(
            {"_id": str(participant_id)},
            {"$set": {"name": participant.name}},
        )
        if result.matched_count == 0:
            return None
        return self.get_participant_by_id(participant_id)

    def delete_participant(self, participant_id: UUID) -> bool:
        result = self._collection.delete_one({"_id": str(participant_id)})
        return result.deleted_count == 1


class TripRepository:
    def __init__(
        self,
        trip_collection: Optional[Collection] = None,
        participant_collection: Optional[Collection] = None,
    ) -> None:
        self._trip_collection = trip_collection or database.get_trip_collection()
        self._participant_collection = participant_collection or database.get_participant_collection()

    def _participant_from_doc(self, doc: dict) -> Participant:
        return Participant(id=UUID(doc["_id"]), name=doc["name"])

    def _participants_from_ids(self, participant_ids: List[str]) -> List[Participant]:
        if not participant_ids:
            return []
        docs = self._participant_collection.find({"_id": {"$in": participant_ids}})
        participants = {doc["_id"]: self._participant_from_doc(doc) for doc in docs}
        return [participants[id_str] for id_str in participant_ids if id_str in participants]

    def _trip_from_doc(self, doc: dict) -> Trip:
        participant_ids = doc.get("participant_ids", [])
        participants = self._participants_from_ids(participant_ids)
        return Trip(
            id=UUID(doc["_id"]),
            name=doc["name"],
            start_date=doc["start_date"],
            end_date=doc["end_date"],
            participants=participants,
        )

    def get_all_trips(self) -> List[Trip]:
        return [self._trip_from_doc(doc) for doc in self._trip_collection.find()]

    def get_trip_by_id(self, trip_id: UUID) -> Optional[Trip]:
        doc = self._trip_collection.find_one({"_id": str(trip_id)})
        return self._trip_from_doc(doc) if doc else None

    def create_trip(self, trip: Trip, participant_ids: Optional[List[UUID]] = None) -> Trip:
        participant_ids = participant_ids or [p.id for p in trip.participants]
        participant_id_strings = [str(pid) for pid in participant_ids]
        missing = self._missing_participants(participant_id_strings)
        if missing:
            raise ValueError(f"Unknown participants: {missing}")
        doc = {
            "_id": str(trip.id),
            "name": trip.name,
            "start_date": trip.start_date,
            "end_date": trip.end_date,
            "participant_ids": participant_id_strings,
        }
        if self._trip_collection.find_one({"_id": doc["_id"]}):
            raise ValueError("Trip with this ID already exists")
        self._trip_collection.insert_one(doc)
        return self._trip_from_doc(doc)

    def update_trip(self, trip_id: UUID, trip: Trip, participant_ids: Optional[List[UUID]] = None) -> Optional[Trip]:
        participant_ids = participant_ids or [p.id for p in trip.participants]
        participant_id_strings = [str(pid) for pid in participant_ids]
        missing = self._missing_participants(participant_id_strings)
        if missing:
            raise ValueError(f"Unknown participants: {missing}")
        result = self._trip_collection.update_one(
            {"_id": str(trip_id)},
            {
                "$set": {
                    "name": trip.name,
                    "start_date": trip.start_date,
                    "end_date": trip.end_date,
                    "participant_ids": participant_id_strings,
                }
            },
        )
        if result.matched_count == 0:
            return None
        return self.get_trip_by_id(trip_id)

    def delete_trip(self, trip_id: UUID) -> bool:
        result = self._trip_collection.delete_one({"_id": str(trip_id)})
        return result.deleted_count == 1

    def assign_participant(self, trip_id: UUID, participant_id: UUID) -> Optional[Trip]:
        participant_doc = self._participant_collection.find_one({"_id": str(participant_id)})
        if not participant_doc:
            return None
        trip_doc = self._trip_collection.find_one({"_id": str(trip_id)})
        if not trip_doc:
            return None
        participant_ids = trip_doc.get("participant_ids", [])
        participant_id_str = str(participant_id)
        if participant_id_str not in participant_ids:
            participant_ids.append(participant_id_str)
            self._trip_collection.update_one(
                {"_id": str(trip_id)},
                {"$set": {"participant_ids": participant_ids}},
            )
        trip_doc["participant_ids"] = participant_ids
        return self._trip_from_doc(trip_doc)

    def remove_participant(self, trip_id: UUID, participant_id: UUID) -> Optional[Trip]:
        trip_doc = self._trip_collection.find_one({"_id": str(trip_id)})
        if not trip_doc:
            return None
        participant_ids = trip_doc.get("participant_ids", [])
        participant_id_str = str(participant_id)
        if participant_id_str in participant_ids:
            participant_ids = [pid for pid in participant_ids if pid != participant_id_str]
            self._trip_collection.update_one(
                {"_id": str(trip_id)},
                {"$set": {"participant_ids": participant_ids}},
            )
            trip_doc["participant_ids"] = participant_ids
        return self._trip_from_doc(trip_doc)

    def _missing_participants(self, participant_ids: List[str]) -> List[UUID]:
        if not participant_ids:
            return []
        docs = self._participant_collection.find({"_id": {"$in": participant_ids}}, {"_id": 1})
        found = {doc["_id"] for doc in docs}
        return [UUID(pid) for pid in participant_ids if pid not in found]

