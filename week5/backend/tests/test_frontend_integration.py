"""Lightweight frontend integration tests.

These verify that the API endpoints return response shapes matching
what the frontend JavaScript (app.js) expects, and that static
assets are served correctly.
"""


# ---------- Static file serving ----------


def test_root_serves_html(client):
    """GET / should serve the frontend index.html."""
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    # The HTML should contain expected elements that app.js targets
    body = r.text
    assert "notes" in body.lower()


def test_static_js_served(client):
    """Static JS file should be accessible via /static/app.js."""
    r = client.get("/static/app.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    assert "fetchJSON" in r.text


def test_static_css_served(client):
    """Static CSS file should be accessible via /static/styles.css."""
    r = client.get("/static/styles.css")
    assert r.status_code == 200
    assert "css" in r.headers["content-type"]


def test_static_nonexistent_returns_404(client):
    """Requesting a non-existent static file returns 404."""
    r = client.get("/static/does_not_exist.xyz")
    assert r.status_code == 404


# ---------- API response shapes for notes (what app.js expects) ----------


def test_notes_list_shape_for_frontend(client):
    """GET /notes/ returns paginated envelope; each item has id, title, content."""
    client.post("/notes/", json={"title": "FE Note", "content": "FE Body"})
    r = client.get("/notes/")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data
    assert data["total"] >= 1
    note = data["items"][0]
    # app.js accesses n.title and n.content
    assert "id" in note
    assert "title" in note
    assert "content" in note


def test_notes_create_shape_for_frontend(client):
    """POST /notes/ returns the created note with id, title, content."""
    r = client.post("/notes/", json={"title": "New", "content": "Body"})
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["title"] == "New"
    assert data["content"] == "Body"


# ---------- API response shapes for action items (what app.js expects) ----------


def test_action_items_list_shape_for_frontend(client):
    """GET /action-items/ returns paginated envelope; items have id, description, completed."""
    client.post("/action-items/", json={"description": "FE Task"})
    r = client.get("/action-items/")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data
    assert data["total"] >= 1
    item = data["items"][0]
    # app.js accesses a.description, a.completed, a.id
    assert "id" in item
    assert "description" in item
    assert "completed" in item


def test_action_items_create_shape_for_frontend(client):
    """POST /action-items/ returns created item with correct shape."""
    r = client.post("/action-items/", json={"description": "Ship"})
    assert r.status_code == 201
    data = r.json()
    assert "id" in data
    assert data["description"] == "Ship"
    assert data["completed"] is False


def test_action_items_complete_shape_for_frontend(client):
    """PUT /action-items/{id}/complete returns item with completed=True."""
    r = client.post("/action-items/", json={"description": "Done soon"})
    item_id = r.json()["id"]

    r = client.put(f"/action-items/{item_id}/complete")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == item_id
    assert data["completed"] is True


# ---------- Search response shape ----------


def test_search_notes_shape_for_frontend(client):
    """GET /notes/search/?q=... returns a JSON array with expected keys."""
    client.post("/notes/", json={"title": "Searchable", "content": "Find me"})
    r = client.get("/notes/search/", params={"q": "Find"})
    assert r.status_code == 200
    results = r.json()
    assert isinstance(results, list)
    assert len(results) >= 1
    assert "title" in results[0]
    assert "content" in results[0]


# ---------- Full frontend workflow simulation ----------


def test_full_note_workflow(client):
    """Simulate the frontend workflow: create note → list → verify presence."""
    # Create
    r = client.post(
        "/notes/",
        json={"title": "Workflow Note", "content": "Workflow Content"},
    )
    assert r.status_code == 201
    note_id = r.json()["id"]

    # List and find the created note
    r = client.get("/notes/")
    assert r.status_code == 200
    titles = [n["title"] for n in r.json()["items"]]
    assert "Workflow Note" in titles

    # Search for the note
    r = client.get("/notes/search/", params={"q": "Workflow"})
    assert r.status_code == 200
    assert any(n["id"] == note_id for n in r.json())


def test_full_action_item_workflow(client):
    """Simulate frontend workflow: create action → list → complete → verify."""
    # Create
    r = client.post("/action-items/", json={"description": "FE workflow task"})
    assert r.status_code == 201
    item_id = r.json()["id"]
    assert r.json()["completed"] is False

    # List and find it
    r = client.get("/action-items/")
    assert r.status_code == 200
    descriptions = [a["description"] for a in r.json()["items"]]
    assert "FE workflow task" in descriptions

    # Complete it
    r = client.put(f"/action-items/{item_id}/complete")
    assert r.status_code == 200
    assert r.json()["completed"] is True

    # Verify in list
    r = client.get("/action-items/")
    item = next(a for a in r.json()["items"] if a["id"] == item_id)
    assert item["completed"] is True
