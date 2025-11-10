from typing import Dict
from uuid import UUID
from .models import *

# in-memory db
trips: Dict[UUID, Trip] = {}
participants: Dict[UUID, Participant] = {}

