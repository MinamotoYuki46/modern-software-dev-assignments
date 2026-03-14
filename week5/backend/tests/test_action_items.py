def test_create_and_complete_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_action_items_pagination(client):
    # Seed 3 action items
    for i in range(3):
        client.post("/action-items/", json={"description": f"Task {i}"})

    # page_size=2, first page returns 2 items
    r = client.get("/action-items/", params={"page": 1, "page_size": 2})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2

    # second page returns 1 item
    r = client.get("/action-items/", params={"page": 2, "page_size": 2})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert len(data["items"]) == 1

    # empty last page (beyond total)
    r = client.get("/action-items/", params={"page": 10, "page_size": 2})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert data["items"] == []

    # too-large page_size still works
    r = client.get("/action-items/", params={"page": 1, "page_size": 1000})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


# ---------- 404 scenarios ----------

def test_complete_item_not_found(client):
    """PUT /action-items/{id}/complete with non-existent ID returns 404."""
    r = client.put("/action-items/9999/complete")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_complete_item_zero_id(client):
    """PUT /action-items/0/complete returns 404."""
    r = client.put("/action-items/0/complete")
    assert r.status_code == 404


# ---------- 400 / 422 (validation) scenarios ----------

def test_create_item_missing_description(client):
    """POST /action-items/ without description returns 422."""
    r = client.post("/action-items/", json={})
    assert r.status_code == 422


def test_create_item_no_json(client):
    """POST /action-items/ with no body returns 422."""
    r = client.post("/action-items/")
    assert r.status_code == 422


def test_create_item_extra_fields_ignored(client):
    """POST /action-items/ with extra fields still creates successfully."""
    r = client.post("/action-items/", json={"description": "Do it", "extra": "ignored"})
    assert r.status_code == 201
    data = r.json()
    assert data["description"] == "Do it"
    assert data["completed"] is False


# ---------- Idempotency / double-complete ----------

def test_complete_already_completed_item(client):
    """Completing an already-completed item should still return 200."""
    r = client.post("/action-items/", json={"description": "Twice"})
    item_id = r.json()["id"]

    client.put(f"/action-items/{item_id}/complete")
    r = client.put(f"/action-items/{item_id}/complete")
    assert r.status_code == 200
    assert r.json()["completed"] is True


# ---------- List empty ----------

def test_list_items_empty(client):
    """GET /action-items/ on fresh DB returns empty paginated response."""
    r = client.get("/action-items/")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0


# ---------- Response shape ----------

def test_action_item_response_shape(client):
    """Verify returned JSON has exactly the expected keys."""
    r = client.post("/action-items/", json={"description": "Check shape"})
    data = r.json()
    assert set(data.keys()) == {"id", "description", "completed"}
    assert isinstance(data["id"], int)
    assert isinstance(data["description"], str)
    assert isinstance(data["completed"], bool)
