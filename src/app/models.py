from uuid import UUID, uuid4
from typing import List
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


class TripCreate(TripBase):
    participant_ids: List[UUID] = Field(default_factory=list)


class Trip(TripBase):
    id: UUID = Field(default_factory=uuid4)
    participants: List[Participant] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }
