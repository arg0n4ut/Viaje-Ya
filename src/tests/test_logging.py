import logging

# tests use the 'client' fixture from conftest.py

def test_request_id_header(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert resp.headers["X-Request-ID"]


def test_logging_records(caplog, client):
    caplog.set_level(logging.INFO, logger="viaje_ya")
    # perform a request
    resp = client.get("/")
    assert resp.status_code == 200

    messages = [r.getMessage() for r in caplog.records]
    assert any("request_start" in m for m in messages), f"start messages: {messages}"
    assert any("request_end" in m for m in messages), f"end messages: {messages}"

    # find end record
    end_record = next((r for r in caplog.records if r.getMessage() == "request_end"), None)
    assert end_record is not None
    assert hasattr(end_record, "request_id")
    assert hasattr(end_record, "duration_ms")
    assert hasattr(end_record, "status_code")
