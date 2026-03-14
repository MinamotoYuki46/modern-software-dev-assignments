def test_create_and_list_notes(client):
    payload = {"title": "Test", "content": "Hello world"}
    r = client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"

    r = client.get("/notes/")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

    r = client.get("/notes/search/")
    assert r.status_code == 200

    r = client.get("/notes/search/", params={"q": "Hello"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1


def test_notes_pagination(client):
    # Seed 3 notes
    for i in range(3):
        client.post("/notes/", json={"title": f"Note {i}", "content": f"Content {i}"})

    # page_size=2, first page returns 2 items
    r = client.get("/notes/", params={"page": 1, "page_size": 2})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2

    # second page returns 1 item
    r = client.get("/notes/", params={"page": 2, "page_size": 2})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert len(data["items"]) == 1

    # empty last page (beyond total)
    r = client.get("/notes/", params={"page": 10, "page_size": 2})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert data["items"] == []

    # too-large page_size still works
    r = client.get("/notes/", params={"page": 1, "page_size": 1000})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


# ---------- 404 scenarios ----------

def test_get_note_not_found(client):
    """GET /notes/{id} with non-existent ID returns 404."""
    r = client.get("/notes/9999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_get_note_not_found_zero_id(client):
    """GET /notes/0 should also return 404 since no row has id=0."""
    r = client.get("/notes/0")
    assert r.status_code == 404


# ---------- 400 / 422 (validation) scenarios ----------

def test_create_note_missing_title(client):
    """POST /notes/ without title returns 422."""
    r = client.post("/notes/", json={"content": "only content"})
    assert r.status_code == 422


def test_create_note_missing_content(client):
    """POST /notes/ without content returns 422."""
    r = client.post("/notes/", json={"title": "only title"})
    assert r.status_code == 422


def test_create_note_empty_body(client):
    """POST /notes/ with empty JSON body returns 422."""
    r = client.post("/notes/", json={})
    assert r.status_code == 422


def test_create_note_no_json(client):
    """POST /notes/ with no JSON body at all returns 422."""
    r = client.post("/notes/")
    assert r.status_code == 422


def test_create_note_wrong_type(client):
    """POST /notes/ with non-string fields returns 422 or succeeds with coercion."""
    r = client.post("/notes/", json={"title": 123, "content": True})
    # Pydantic v2 may coerce scalars to str; either 201 or 422 is acceptable
    assert r.status_code in (201, 422)


# ---------- Search edge cases ----------

def test_search_notes_no_match(client):
    """Search with a query that matches nothing returns empty list."""
    r = client.get("/notes/search/", params={"q": "nonexistentrandomxyz"})
    assert r.status_code == 200
    assert r.json() == []


def test_search_notes_empty_query(client):
    """Search with empty string returns all notes (same as no query)."""
    client.post("/notes/", json={"title": "A", "content": "B"})
    r = client.get("/notes/search/", params={"q": ""})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------- GET single note success ----------

def test_get_note_success(client):
    """GET /notes/{id} returns correct note after creation."""
    r = client.post("/notes/", json={"title": "Fetch me", "content": "body"})
    note_id = r.json()["id"]

    r = client.get(f"/notes/{note_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == note_id
    assert data["title"] == "Fetch me"
    assert data["content"] == "body"


# ---------- List empty ----------

def test_list_notes_empty(client):
    """GET /notes/ on fresh DB returns empty paginated response."""
    r = client.get("/notes/")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0
