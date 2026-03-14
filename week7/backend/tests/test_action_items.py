def test_create_complete_list_and_patch_action_item(client):
    payload = {"description": "Ship it"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False
    assert "created_at" in item and "updated_at" in item

    r = client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = client.get("/action-items/", params={"completed": True, "limit": 5, "sort": "-created_at"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = client.patch(f"/action-items/{item['id']}", json={"description": "Updated"})
    assert r.status_code == 200
    patched = r.json()
    assert patched["description"] == "Updated"


def test_action_item_get_delete_and_validation(client):
    payload = {"description": "Test item"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201
    item_id = r.json()["id"]

    r = client.get(f"/action-items/{item_id}")
    assert r.status_code == 200
    assert r.json()["description"] == "Test item"

    r = client.delete(f"/action-items/{item_id}")
    assert r.status_code == 204

    r = client.get(f"/action-items/{item_id}")
    assert r.status_code == 404

    r = client.delete(f"/action-items/{item_id}")
    assert r.status_code == 404

    r = client.post("/action-items/", json={"description": ""})
    assert r.status_code == 422

    r = client.post("/action-items/", json={"description": "   "})
    assert r.status_code == 422


def test_action_item_get_delete_and_validation_duplicate(client):
    payload = {"description": "Test item"}
    r = client.post("/action-items/", json=payload)
    assert r.status_code == 201
    item_id = r.json()["id"]

    r = client.get(f"/action-items/{item_id}")
    assert r.status_code == 200
    assert r.json()["description"] == "Test item"

    r = client.delete(f"/action-items/{item_id}")
    assert r.status_code == 204

    r = client.get(f"/action-items/{item_id}")
    assert r.status_code == 404

    r = client.delete(f"/action-items/{item_id}")
    assert r.status_code == 404

    r = client.post("/action-items/", json={"description": ""})
    assert r.status_code == 422

    r = client.post("/action-items/", json={"description": "   "})
    assert r.status_code == 422


def test_action_items_pagination_and_sorting(client):
    ids = []
    descriptions = ["delta", "alpha", "echo", "beta", "charlie"]
    for d in descriptions:
        r = client.post("/action-items/", json={"description": d})
        assert r.status_code == 201
        ids.append(r.json()["id"])

    # page 1 and page 2 no overlap
    r1 = client.get("/action-items/", params={"limit": 2, "skip": 0, "sort": "created_at"})
    assert r1.status_code == 200
    page1 = r1.json()
    assert len(page1) == 2

    r2 = client.get("/action-items/", params={"limit": 2, "skip": 2, "sort": "created_at"})
    assert r2.status_code == 200
    page2 = r2.json()
    assert len(page2) == 2

    assert {item["id"] for item in page1}.isdisjoint({item["id"] for item in page2})

    r_skip_gt = client.get("/action-items/", params={"limit": 2, "skip": 999})
    assert r_skip_gt.status_code == 200
    assert r_skip_gt.json() == []

    r_limit0 = client.get("/action-items/", params={"limit": 0, "skip": 0})
    assert r_limit0.status_code == 200
    assert r_limit0.json() == []

    r_limit_high = client.get("/action-items/", params={"limit": 201, "skip": 0})
    assert r_limit_high.status_code == 422

    # sorting by id asc and desc
    r_id_asc = client.get("/action-items/", params={"limit": 5, "skip": 0, "sort": "id"})
    assert r_id_asc.status_code == 200
    ids_asc = [item["id"] for item in r_id_asc.json()]
    assert ids_asc == sorted(ids_asc)

    r_id_desc = client.get("/action-items/", params={"limit": 5, "skip": 0, "sort": "-id"})
    assert r_id_desc.status_code == 200
    ids_desc = [item["id"] for item in r_id_desc.json()]
    assert ids_desc == sorted(ids_desc, reverse=True)

    # alphabetical description by `description` field
    r_desc_alpha = client.get("/action-items/", params={"limit": 5, "skip": 0, "sort": "description"})
    assert r_desc_alpha.status_code == 200
    descs = [item["description"] for item in r_desc_alpha.json()]
    assert descs == sorted(descs)

    # invalid sort falls back to created_at desc not 500
    r_invalid_sort = client.get("/action-items/", params={"limit": 5, "skip": 0, "sort": "nope"})
    assert r_invalid_sort.status_code == 200
    times = [item["created_at"] for item in r_invalid_sort.json()]
    assert times == sorted(times, reverse=True)

    # combined sort + pagination
    r_combined = client.get("/action-items/", params={"limit": 2, "skip": 1, "sort": "-description"})
    assert r_combined.status_code == 200
    assert len(r_combined.json()) == 2


