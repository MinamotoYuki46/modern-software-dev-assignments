def test_create_list_and_patch_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"
    assert "created_at" in data and "updated_at" in data

    r = client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.get("/notes/", params={"q": "Hello", "limit": 10, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    note_id = data["id"]
    r = client.patch(f"/notes/{note_id}", json={"title": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["title"] == "Updated"


def test_note_delete_and_validation(client):
    payload = {"title": "Sample", "content": "x"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201
    note_id = r.json()["id"]

    r = client.delete(f"/notes/{note_id}")
    assert r.status_code == 204

    r = client.delete(f"/notes/{note_id}")
    assert r.status_code == 404

    r = client.post("/notes/", json={"title": "", "content": "text"})
    assert r.status_code == 422

    r = client.post("/notes/", json={"title": "   ", "content": "text"})
    assert r.status_code == 422

    r = client.post("/notes/", json={"title": "t", "content": "   "})
    assert r.status_code == 422


def test_note_extract_endpoint(client):
    payload = {"title": "Extract test", "content": "TODO: add docs\nPlease deploy by Monday\nThis is fine"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201
    note_id = r.json()["id"]

    r = client.post(f"/notes/{note_id}/extract")
    assert r.status_code == 200
    extracted = r.json()
    texts = [item["text"] for item in extracted]
    kinds = [item["kind"] for item in extracted]
    assert "TODO: add docs" in texts
    assert "Please deploy by Monday" in texts
    assert "TODO" in kinds or "TRIGGER_PHRASE" in kinds

    r = client.post("/notes/999999/extract")
    assert r.status_code == 404


