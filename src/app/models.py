from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4

class Participant(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str

class Trip(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    start_date: str
    end_date: str
    participants: List[Participant] = []
