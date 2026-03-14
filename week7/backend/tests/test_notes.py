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


def test_note_extract_endpoint_structured(client):
    payload = {"title": "Extract test", "content": "TODO: add docs\nPlease deploy by Monday\nThis is fine"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201
    note_id = r.json()["id"]

    r = client.post(f"/notes/{note_id}/extract")
    assert r.status_code == 200
    extracted = r.json()
    assert isinstance(extracted, list)
    assert any(item["kind"] == "TODO" for item in extracted)
    assert any(item["text"] == "Please deploy by Monday" for item in extracted)
    assert any(item["deadline"] == "Monday" for item in extracted if item.get("deadline"))

    r = client.post("/notes/999999/extract")
    assert r.status_code == 404


def test_notes_pagination_and_sorting(client):
    # Create five notes with distinct titles
    titles = ["delta", "alpha", "echo", "beta", "charlie"]
    ids = []
    for t in titles:
        r = client.post("/notes/", json={"title": t, "content": "x"})
        assert r.status_code == 201
        ids.append(r.json()["id"])

    # Page 1/2 with limit=2 and sort by created_at ascending
    r1 = client.get("/notes/", params={"limit": 2, "skip": 0, "sort": "created_at"})
    assert r1.status_code == 200
    p1 = r1.json()
    assert len(p1) == 2

    r2 = client.get("/notes/", params={"limit": 2, "skip": 2, "sort": "created_at"})
    assert r2.status_code == 200
    p2 = r2.json()
    assert len(p2) == 2

    # No overlap between pages
    p1_ids = {item["id"] for item in p1}
    p2_ids = {item["id"] for item in p2}
    assert p1_ids.isdisjoint(p2_ids)

    # Skip > total returns empty
    r_empty = client.get("/notes/", params={"limit": 2, "skip": 999, "sort": "created_at"})
    assert r_empty.status_code == 200
    assert r_empty.json() == []

    # limit=0 returns empty reliably
    r_limit0 = client.get("/notes/", params={"limit": 0, "skip": 0, "sort": "created_at"})
    assert r_limit0.status_code == 200
    assert r_limit0.json() == []

    # limit > max returns 422
    r_limit_too_high = client.get("/notes/", params={"limit": 201, "skip": 0, "sort": "created_at"})
    assert r_limit_too_high.status_code == 422

    # Alphabetical sorting by title
    r_alpha = client.get("/notes/", params={"limit": 5, "skip": 0, "sort": "title"})
    assert r_alpha.status_code == 200
    sorted_titles = [note["title"] for note in r_alpha.json()]
    assert sorted_titles == sorted(sorted_titles)

    # Invalid sort field falls back to created_at desc
    r_invalid_sort = client.get("/notes/", params={"limit": 5, "skip": 0, "sort": "invalid_field"})
    assert r_invalid_sort.status_code == 200
    listed = r_invalid_sort.json()
    created = [note["created_at"] for note in listed]
    assert created == sorted(created, reverse=True)

    # Combined sort + pagination (title desc + limit 3)
    r_combined = client.get("/notes/", params={"limit": 3, "skip": 1, "sort": "-title"})
    assert r_combined.status_code == 200
    combo = r_combined.json()
    assert len(combo) == 3
    combo_titles = [note["title"] for note in combo]
    assert combo_titles == sorted([note["title"] for note in combo], reverse=True)


