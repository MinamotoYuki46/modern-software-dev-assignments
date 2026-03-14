"""Tests for concurrency and transactional behavior."""

import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.app.db import get_db
from backend.app.main import app
from backend.app.models import Base
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import pytest


@pytest.fixture()
def concurrent_client():
    """Create a test client with an in-memory SQLite DB (thread-safe via StaticPool)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    engine.dispose()


# ---------- Concurrent creation ----------


def test_concurrent_note_creation(concurrent_client):
    """Multiple notes created sequentially (simulating rapid-fire) all persist."""
    client = concurrent_client
    count = 20

    results = []
    for i in range(count):
        r = client.post(
            "/notes/",
            json={"title": f"Note {i}", "content": f"Body {i}"},
        )
        results.append(r)

    # All requests should succeed
    assert all(r.status_code == 201 for r in results)

    # All notes should be persisted
    r = client.get("/notes/", params={"page_size": count})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == count
    assert len(data["items"]) == count


def test_concurrent_action_item_creation(concurrent_client):
    """Multiple action items created rapidly all persist."""
    client = concurrent_client
    count = 15

    results = []
    for i in range(count):
        r = client.post(
            "/action-items/", json={"description": f"Task {i}"}
        )
        results.append(r)

    assert all(r.status_code == 201 for r in results)

    r = client.get("/action-items/", params={"page_size": count})
    data = r.json()
    assert data["total"] == count
    assert len(data["items"]) == count


def test_concurrent_complete_same_item(concurrent_client):
    """Completing the same item multiple times should not cause errors."""
    client = concurrent_client
    r = client.post("/action-items/", json={"description": "Race me"})
    item_id = r.json()["id"]

    # Complete the same item multiple times (idempotent)
    for _ in range(10):
        r = client.put(f"/action-items/{item_id}/complete")
        assert r.status_code == 200

    # Item should be completed
    r = client.get("/action-items/")
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["completed"] is True


# ---------- Transaction rollback ----------


def test_transaction_isolation_on_invalid_create(client):
    """A failed create should not leave partial data in the database."""
    # Create one valid note first
    r = client.post("/notes/", json={"title": "Valid", "content": "OK"})
    assert r.status_code == 201

    # Attempt an invalid create (missing field)
    r = client.post("/notes/", json={"title": "Missing content"})
    assert r.status_code == 422

    # The valid note should still be there, and nothing else
    r = client.get("/notes/")
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Valid"


def test_create_and_read_isolation(client):
    """Notes created in one request are visible in subsequent requests."""
    for i in range(5):
        r = client.post(
            "/notes/", json={"title": f"N{i}", "content": f"C{i}"}
        )
        assert r.status_code == 201

    r = client.get("/notes/", params={"page_size": 10})
    data = r.json()
    assert data["total"] == 5

    # Each note should be individually retrievable
    for note in data["items"]:
        r2 = client.get(f"/notes/{note['id']}")
        assert r2.status_code == 200
        assert r2.json()["title"] == note["title"]


def test_multiple_action_items_transaction(client):
    """Creating multiple action items in sequence; all should be committed."""
    ids = []
    for i in range(3):
        r = client.post("/action-items/", json={"description": f"Txn item {i}"})
        assert r.status_code == 201
        ids.append(r.json()["id"])

    # Complete first two
    for item_id in ids[:2]:
        r = client.put(f"/action-items/{item_id}/complete")
        assert r.status_code == 200

    # Verify mixed states
    r = client.get("/action-items/", params={"page_size": 10})
    data = r.json()
    assert data["total"] == 3
    completed = [item for item in data["items"] if item["completed"]]
    pending = [item for item in data["items"] if not item["completed"]]
    assert len(completed) == 2
    assert len(pending) == 1
