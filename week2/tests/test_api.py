import os
import pytest

from fastapi.testclient import TestClient

from ..app import main, db


@pytest.fixture(autouse=True)
def reset_db(tmp_path, monkeypatch):
    # make sure each test run uses a fresh database file in tmp_path
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "app.db")
    db.init_db()


@pytest.fixture

def client():
    return TestClient(main.app)


def test_notes_list_and_create(client):
    # initially empty
    r = client.get("/notes")
    assert r.status_code == 200
    assert r.json() == []

    # create a note
    r = client.post("/notes", json={"content": "remember coffee"})
    assert r.status_code == 200
    note = r.json()
    assert note["content"] == "remember coffee"

    # listing returns the note
    r = client.get("/notes")
    notes = r.json()
    assert len(notes) == 1
    assert notes[0]["content"] == "remember coffee"


def test_action_item_endpoints(client, monkeypatch):
    # mock the LLM call so extract-llm doesn't hit a model
    fake = "[\"a\", \"b\"]"
    monkeypatch.setattr("week2.app.services.extract.chat", lambda **kw: fake)

    # heuristic extraction uses bullets
    text = "- one\n- two"
    r = client.post("/action-items/extract", json={"text": text, "save_note": False})
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(it["text"] == "one" for it in items)

    # llm endpoint returns the mocked result
    r2 = client.post("/action-items/extract-llm", json={"text": "whatever", "save_note": False})
    assert r2.status_code == 200
    # do not rely on specific ids; just verify the texts match in order
    returned = r2.json()["items"]
    assert [it["text"] for it in returned] == ["a", "b"]
