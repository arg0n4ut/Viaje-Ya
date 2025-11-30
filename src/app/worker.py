import logging
import os
import time
from typing import NoReturn

from .repository import ParticipantRepository, TripRepository

logger = logging.getLogger("viaje_ya.worker")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def _summarise() -> None:
    trip_repo = TripRepository()
    participant_repo = ParticipantRepository()
    trips = trip_repo.get_all_trips()
    participants = participant_repo.get_all_participants()
    logger.info("cluster_status", extra={
        "trip_count": len(trips),
        "participant_count": len(participants),
    })

def main() -> NoReturn:
    sleep_seconds = int(os.getenv("WORKER_SLEEP_SECONDS", "30"))
    while True:
        try:
            _summarise()
        except Exception: 
            logger.exception("worker_iteration_failed")
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
