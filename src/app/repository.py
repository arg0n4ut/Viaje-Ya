from typing import List, Optional
from uuid import UUID
from pymongo.collection import Collection
from . import database
from .models import Participant, Trip, Task, Proposal


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
        tasks = [
            Task(
                id=UUID(task_doc["id"]),
                description=task_doc["description"],
                done=task_doc.get("done", False),
                participant_id=UUID(task_doc["participant_id"]),
            )
            for task_doc in doc.get("tasks", [])
        ]
        proposals = [
            Proposal(
                id=UUID(prop_doc["id"]),
                title=prop_doc["title"],
                description=prop_doc.get("description", ""),
                participant_id=UUID(prop_doc["participant_id"]),
                upvotes=set(UUID(v) for v in prop_doc.get("upvotes", [])),
            )
            for prop_doc in doc.get("proposals", [])
        ]
        return Trip(
            id=UUID(doc["_id"]),
            name=doc["name"],
            start_date=doc["start_date"],
            end_date=doc["end_date"],
            participants=participants,
            tasks=tasks,
            proposals=proposals,
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
            "tasks": [
                {
                    "id": str(task.id),
                    "description": task.description,
                    "done": task.done,
                    "participant_id": str(task.participant_id),
                }
                for task in getattr(trip, "tasks", [])
            ],
            "proposals": [
                {
                    "id": str(proposal.id),
                    "title": proposal.title,
                    "description": proposal.description,
                    "participant_id": str(proposal.participant_id),
                    "upvotes": [str(v) for v in proposal.upvotes],
                }
                for proposal in getattr(trip, "proposals", [])
            ],
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

    def add_task(self, trip_id: UUID, task: Task) -> Optional[Task]:
        update_result = self._trip_collection.update_one(
            {"_id": str(trip_id)},
            {
                "$push": {
                    "tasks": {
                        "id": str(task.id),
                        "description": task.description,
                        "done": task.done,
                        "participant_id": str(task.participant_id),
                    }
                }
            },
        )
        if update_result.matched_count == 0:
            return None
        return task

    def mark_task_done(self, trip_id: UUID, task_id: UUID, done: bool = True) -> Optional[Task]:
        result = self._trip_collection.update_one(
            {"_id": str(trip_id), "tasks.id": str(task_id)},
            {"$set": {"tasks.$.done": done}},
        )
        if result.matched_count == 0:
            return None
        updated_trip = self._trip_collection.find_one({"_id": str(trip_id)})
        if not updated_trip:
            return None
        task_doc = next((t for t in updated_trip.get("tasks", []) if t.get("id") == str(task_id)), None)
        if not task_doc:
            return None
        return Task(
            id=UUID(task_doc["id"]),
            description=task_doc["description"],
            done=task_doc.get("done", False),
            participant_id=UUID(task_doc["participant_id"]),
        )

    def remove_task(self, trip_id: UUID, task_id: UUID) -> bool:
        result = self._trip_collection.update_one(
            {"_id": str(trip_id)},
            {"$pull": {"tasks": {"id": str(task_id)}}},
        )
        return result.matched_count > 0 and result.modified_count > 0

    def add_proposal(self, trip_id: UUID, proposal: Proposal) -> Optional[Proposal]:
        result = self._trip_collection.update_one(
            {"_id": str(trip_id)},
            {
                "$push": {
                    "proposals": {
                        "id": str(proposal.id),
                        "title": proposal.title,
                        "description": proposal.description,
                        "participant_id": str(proposal.participant_id),
                        "upvotes": list(str(v) for v in proposal.upvotes),
                    }
                }
            },
        )
        if result.matched_count == 0:
            return None
        return proposal

    def list_proposals(self, trip_id: UUID) -> Optional[List[Proposal]]:
        doc = self._trip_collection.find_one({"_id": str(trip_id)})
        if not doc:
            return None
        return self._trip_from_doc(doc).proposals

    def remove_proposal(self, trip_id: UUID, proposal_id: UUID) -> bool:
        result = self._trip_collection.update_one(
            {"_id": str(trip_id)},
            {"$pull": {"proposals": {"id": str(proposal_id)}}},
        )
        return result.matched_count > 0 and result.modified_count > 0

    def upvote_proposal(self, trip_id: UUID, proposal_id: UUID, participant_id: UUID) -> Optional[Proposal]:
        trip_doc = self._trip_collection.find_one({"_id": str(trip_id)})
        if not trip_doc:
            return None

        proposals = trip_doc.get("proposals", [])
        for proposal in proposals:
            if proposal.get("id") == str(proposal_id):
                upvotes = set(proposal.get("upvotes", []))
                upvotes.add(str(participant_id))
                proposal["upvotes"] = list(upvotes)
                break
        else:
            return None

        update = self._trip_collection.update_one(
            {"_id": str(trip_id)},
            {"$set": {"proposals": proposals}},
        )
        if update.matched_count == 0:
            return None

        updated = self._trip_collection.find_one({"_id": str(trip_id)})
        if not updated:
            return None
        proposal_doc = next((p for p in updated.get("proposals", []) if p.get("id") == str(proposal_id)), None)
        if not proposal_doc:
            return None
        return Proposal(
            id=UUID(proposal_doc["id"]),
            title=proposal_doc["title"] or "",
            description=proposal_doc.get("description", ""),
            participant_id=UUID(proposal_doc["participant_id"]),
            upvotes=set(UUID(v) for v in proposal_doc.get("upvotes", [])),
        )

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

    def remove_participant_from_all_trips(self, participant_id: UUID) -> None:
        self._trip_collection.update_many(
            {},
            {"$pull": {"participant_ids": str(participant_id)}}
        )

    def _missing_participants(self, participant_ids: List[str]) -> List[UUID]:
        if not participant_ids:
            return []
        docs = self._participant_collection.find({"_id": {"$in": participant_ids}}, {"_id": 1})
        found = {doc["_id"] for doc in docs}
        return [UUID(pid) for pid in participant_ids if pid not in found]

