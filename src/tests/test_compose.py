import os
import shutil
import subprocess
import time
from pathlib import Path

import httpx
import pytest

_COMPOSE_FILE = Path(__file__).resolve().parents[2] / "compose.yaml"
_SKIP_FLAG = os.getenv("SKIP_DOCKER_TESTS", "0") == "1"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def _compose_cmd(*args: str) -> list[str]:
    return ["docker", "compose", "-f", str(_COMPOSE_FILE), *args]


@pytest.mark.compose
@pytest.mark.skipif(_SKIP_FLAG, reason="Docker compose tests disabled by environment")
@pytest.mark.skipif(not _docker_available(), reason="Docker CLI not available")
def test_compose_cluster_smoke() -> None:
    env = os.environ.copy()
    env.setdefault("COMPOSE_PROJECT_NAME", "viaje_ya_pytest")
    subprocess.run(_compose_cmd("down", "--volumes", "--remove-orphans"), check=False, env=env)

    try:
        subprocess.run(_compose_cmd("up", "-d", "--build"), check=True, env=env)
        _wait_for_api()
        _exercise_api()
    finally:
        subprocess.run(_compose_cmd("down", "--volumes", "--remove-orphans"), check=False, env=env)


def _wait_for_api(timeout_seconds: int = 120) -> None:
    deadline = time.time() + timeout_seconds
    url = "http://localhost:8000/"
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
        except httpx.HTTPError:
            time.sleep(2)
            continue
        if response.status_code == 200:
            return
        time.sleep(2)
    pytest.fail("API failed to become healthy via docker compose")


def _exercise_api() -> None:
    participant_resp = httpx.post(
        "http://localhost:8000/participants/",
        json={"name": "Compose Tester"},
        timeout=5.0,
    )
    assert participant_resp.status_code == 201
    participant_id = participant_resp.json()["id"]

    trip_resp = httpx.post(
        "http://localhost:8000/trips/",
        json={
            "name": "Compose Trip",
            "start_date": "2026-06-10",
            "end_date": "2026-06-15",
            "participant_ids": [participant_id],
        },
        timeout=5.0,
    )
    assert trip_resp.status_code == 201
    body = trip_resp.json()
    assert body["participants"][0]["id"] == participant_id
