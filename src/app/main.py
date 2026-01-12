from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from uuid import UUID, uuid4
from . import database
from .models import Participant, ParticipantCreate, Trip, TripCreate, Task, TaskCreate, Proposal, ProposalCreate
from .repository import ParticipantRepository, TripRepository

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from pydantic import BaseModel


from pythonjsonlogger import json
from prometheus_fastapi_instrumentator import Instrumentator

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        database.set_client(None)


app = FastAPI(lifespan=lifespan)
STATIC_DIR = Path(__file__).parent / "static"

# serve static assets for the lightweight UI
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# expose prometheus metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False, should_gzip=True)

# configure logger
logger = logging.getLogger("viaje_ya")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
fmt = "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(method)s %(path)s %(status_code)s %(duration_ms)s"
formatter = json.JsonFormatter(fmt)
handler.setFormatter(formatter)
logger.handlers = []
logger.addHandler(handler)

# logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        request_id = request.headers.get("X-Request-ID") or str(uuid4())

        # log request start
        logger.info("request_start", extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
        })

        response: Response = await call_next(request)
        duration_ms = (time.time() - start) * 1000

        # attach request id to response for tracing
        response.headers["X-Request-ID"] = request_id

        # log request end with status and duration
        logger.info("request_end", extra={
            "request_id": request_id,
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        })

        return response

# add middleware to app
app.add_middleware(LoggingMiddleware)

@app.get("/")
def read_root():
    return {"message": "Welcome to Viaje-Ya"}


@app.get("/ui")
def serve_ui():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="UI not found")
    return FileResponse(index_file)

# Dependency
def get_trip_repository() -> TripRepository:
    return TripRepository()

def get_participant_repository() -> ParticipantRepository:
    return ParticipantRepository()

@app.post("/trips/", response_model=Trip, status_code=201)
def create_trip(
    trip_data: TripCreate,
    repo: TripRepository = Depends(get_trip_repository),
    participant_repo: ParticipantRepository = Depends(get_participant_repository),
):
    participant_ids = trip_data.participant_ids
    if participant_ids:
        existing = participant_repo.get_participants_by_ids(participant_ids)
        found_ids = {participant.id for participant in existing}
        missing = [pid for pid in participant_ids if pid not in found_ids]
        if missing:
            raise HTTPException(status_code=400, detail={"unknown_participants": [str(mid) for mid in missing]})

    new_trip = Trip(
        id=uuid4(),
        name=trip_data.name,
        start_date=trip_data.start_date,
        end_date=trip_data.end_date,
    )

    try:
        created = repo.create_trip(new_trip, participant_ids=participant_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return created

@app.get("/trips/", response_model=List[Trip])
def get_all_trips(repo: TripRepository = Depends(get_trip_repository)):
    return repo.get_all_trips()

@app.get("/trips/{trip_id}", response_model=Trip)
def get_trip(trip_id: UUID, repo: TripRepository = Depends(get_trip_repository)):
    trip = repo.get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


@app.delete("/trips/{trip_id}", status_code=204)
def delete_trip(trip_id: UUID, repo: TripRepository = Depends(get_trip_repository)):
    deleted = repo.delete_trip(trip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Trip not found")
    return Response(status_code=204)

@app.post("/participants/", response_model=Participant, status_code=201)
def create_participant(
    participant_data: ParticipantCreate,
    repo: ParticipantRepository = Depends(get_participant_repository)
):
    participant = Participant(id=uuid4(), name=participant_data.name)
    try:
        return repo.create_participant(participant)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@app.get("/participants/", response_model=List[Participant])
def get_all_participants(repo: ParticipantRepository = Depends(get_participant_repository)):
    return repo.get_all_participants()

@app.get("/participants/{participant_id}", response_model=Participant)
def get_participant(participant_id: UUID, repo: ParticipantRepository = Depends(get_participant_repository)):
    participant = repo.get_participant_by_id(participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    return participant


@app.delete("/participants/{participant_id}", status_code=204)
def delete_participant(
    participant_id: UUID,
    repo: ParticipantRepository = Depends(get_participant_repository),
    trip_repo: TripRepository = Depends(get_trip_repository),
):
    deleted = repo.delete_participant(participant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Participant not found")
    trip_repo.remove_participant_from_all_trips(participant_id)
    return Response(status_code=204)

@app.post("/trips/{trip_id}/participants/{participant_id}", response_model=Trip)
def assign_participant_to_trip(
    trip_id: UUID,
    participant_id: UUID,
    trip_repo: TripRepository = Depends(get_trip_repository),
    participant_repo: ParticipantRepository = Depends(get_participant_repository),
):
    if not participant_repo.get_participant_by_id(participant_id):
        raise HTTPException(status_code=404, detail="Participant not found")
    updated = trip_repo.assign_participant(trip_id, participant_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Trip not found")
    return updated

@app.delete("/trips/{trip_id}/participants/{participant_id}", response_model=Trip)
def remove_participant_from_trip(
    trip_id: UUID,
    participant_id: UUID,
    repo: TripRepository = Depends(get_trip_repository),
):
    updated = repo.remove_participant(trip_id, participant_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Trip not found")
    return updated


class TaskActor(BaseModel):
    participant_id: UUID


class VoteActor(BaseModel):
    participant_id: UUID


@app.post("/trips/{trip_id}/tasks/", response_model=Task, status_code=201)
def add_task_to_trip(
    trip_id: UUID,
    task_data: TaskCreate,
    trip_repo: TripRepository = Depends(get_trip_repository),
    participant_repo: ParticipantRepository = Depends(get_participant_repository),
):
    if not participant_repo.get_participant_by_id(task_data.participant_id):
        raise HTTPException(status_code=404, detail="Participant not found")

    task = Task(
        id=uuid4(),
        description=task_data.description,
        done=False,
        participant_id=task_data.participant_id,
    )

    created = trip_repo.add_task(trip_id, task)
    if not created:
        raise HTTPException(status_code=404, detail="Trip not found")
    return task


@app.post("/trips/{trip_id}/tasks/{task_id}/done", response_model=Task)
def mark_task_done(
    trip_id: UUID,
    task_id: UUID,
    actor: TaskActor,
    done: bool = True,
    participant_repo: ParticipantRepository = Depends(get_participant_repository),
    trip_repo: TripRepository = Depends(get_trip_repository),
):
    if not participant_repo.get_participant_by_id(actor.participant_id):
        raise HTTPException(status_code=404, detail="Participant not found")

    updated = trip_repo.mark_task_done(trip_id, task_id, done=done)
    if not updated:
        raise HTTPException(status_code=404, detail="Task or trip not found")
    return updated


@app.delete("/trips/{trip_id}/tasks/{task_id}", status_code=204)
def delete_task_from_trip(
    trip_id: UUID,
    task_id: UUID,
    participant_id: UUID,
    participant_repo: ParticipantRepository = Depends(get_participant_repository),
    trip_repo: TripRepository = Depends(get_trip_repository),
):
    if not participant_repo.get_participant_by_id(participant_id):
        raise HTTPException(status_code=404, detail="Participant not found")

    removed = trip_repo.remove_task(trip_id, task_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Task or trip not found")
    return Response(status_code=204)


@app.get("/trips/{trip_id}/tasks/", response_model=List[Task])
def list_tasks_for_trip(
    trip_id: UUID,
    repo: TripRepository = Depends(get_trip_repository),
):
    trip = repo.get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip.tasks


@app.post("/trips/{trip_id}/proposals/", response_model=Proposal, status_code=201)
def propose_destination(
    trip_id: UUID,
    proposal_data: ProposalCreate,
    trip_repo: TripRepository = Depends(get_trip_repository),
    participant_repo: ParticipantRepository = Depends(get_participant_repository),
):
    if not participant_repo.get_participant_by_id(proposal_data.participant_id):
        raise HTTPException(status_code=404, detail="Participant not found")

    proposal = Proposal(
        id=uuid4(),
        title=proposal_data.title,
        description=proposal_data.description,
        participant_id=proposal_data.participant_id,
        upvotes=set(),
    )

    created = trip_repo.add_proposal(trip_id, proposal)
    if not created:
        raise HTTPException(status_code=404, detail="Trip not found")
    return proposal


@app.get("/trips/{trip_id}/proposals/", response_model=List[Proposal])
def list_proposals(
    trip_id: UUID,
    trip_repo: TripRepository = Depends(get_trip_repository),
):
    proposals = trip_repo.list_proposals(trip_id)
    if proposals is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return proposals


@app.post("/trips/{trip_id}/proposals/{proposal_id}/upvote", response_model=Proposal)
def upvote_proposal(
    trip_id: UUID,
    proposal_id: UUID,
    actor: VoteActor,
    participant_repo: ParticipantRepository = Depends(get_participant_repository),
    trip_repo: TripRepository = Depends(get_trip_repository),
):
    if not participant_repo.get_participant_by_id(actor.participant_id):
        raise HTTPException(status_code=404, detail="Participant not found")

    updated = trip_repo.upvote_proposal(trip_id, proposal_id, actor.participant_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Trip or proposal not found")
    return updated


@app.delete("/trips/{trip_id}/proposals/{proposal_id}", status_code=204)
def delete_proposal(
    trip_id: UUID,
    proposal_id: UUID,
    participant_id: UUID,
    participant_repo: ParticipantRepository = Depends(get_participant_repository),
    trip_repo: TripRepository = Depends(get_trip_repository),
):
    if not participant_repo.get_participant_by_id(participant_id):
        raise HTTPException(status_code=404, detail="Participant not found")

    removed = trip_repo.remove_proposal(trip_id, proposal_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Trip or proposal not found")
    return Response(status_code=204)
