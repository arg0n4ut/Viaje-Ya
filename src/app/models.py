from uuid import UUID, uuid4
from typing import List, Set
from pydantic import BaseModel, Field

class ParticipantBase(BaseModel):
    name: str

class ParticipantCreate(ParticipantBase):
    pass

class Participant(ParticipantBase):
    id: UUID = Field(default_factory=uuid4)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class TripBase(BaseModel):
    name: str
    start_date: str
    end_date: str


class TaskBase(BaseModel):
    description: str


class TaskCreate(TaskBase):
    participant_id: UUID


class Task(TaskBase):
    id: UUID = Field(default_factory=uuid4)
    done: bool = False
    participant_id: UUID

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class TripCreate(TripBase):
    participant_ids: List[UUID] = Field(default_factory=list)


class ProposalBase(BaseModel):
    title: str
    description: str


class ProposalCreate(ProposalBase):
    participant_id: UUID


class Proposal(ProposalBase):
    id: UUID = Field(default_factory=uuid4)
    participant_id: UUID
    upvotes: Set[UUID] = Field(default_factory=set)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class Trip(TripBase):
    id: UUID = Field(default_factory=uuid4)
    participants: List[Participant] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)
    proposals: List[Proposal] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
