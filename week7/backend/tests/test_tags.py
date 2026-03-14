def test_tag_crud_and_duplicate(client):
    r = client.post("/tags/", json={"name": "Feature"})
    assert r.status_code == 201
    tag = r.json()
    assert tag["name"] == "feature"

    r = client.post("/tags/", json={"name": "feature"})
    assert r.status_code == 409

    r = client.get("/tags/")
    assert r.status_code == 200
    tags = r.json()
    assert tags[0]["name"] == "feature"

    r = client.get(f"/tags/{tag['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "feature"

    r = client.delete(f"/tags/{tag['id']}")
    assert r.status_code == 204

    r = client.get(f"/tags/{tag['id']}")
    assert r.status_code == 404


def test_note_tag_relationship_and_cascade(client):
    # create note and tag, associate
    r = client.post("/notes/", json={"title": "With Tag", "content": "X"})
    assert r.status_code == 201
    note_id = r.json()["id"]

    r = client.post("/tags/", json={"name": "urgent"})
    assert r.status_code == 201
    tag_id = r.json()["id"]

    r = client.post(f"/notes/{note_id}/tags/{tag_id}")
    assert r.status_code == 200
    assert any(t["id"] == tag_id for t in r.json()["tags"])

    # remove association
    r = client.delete(f"/notes/{note_id}/tags/{tag_id}")
    assert r.status_code == 200
    assert not r.json()["tags"]

    # attach again and then remove note, ensure tag remains
    r = client.post(f"/notes/{note_id}/tags/{tag_id}")
    assert r.status_code == 200

    r = client.delete(f"/notes/{note_id}")
    assert r.status_code == 204

    r = client.get(f"/tags/{tag_id}")
    assert r.status_code == 200

    # create second note, attach same tag, delete tag, ensure note has no tags
    r = client.post("/notes/", json={"title": "Second", "content": "X"})
    assert r.status_code == 201
    note2_id = r.json()["id"]

    r = client.post(f"/notes/{note2_id}/tags/{tag_id}")
    assert r.status_code == 200
    assert any(t["id"] == tag_id for t in r.json()["tags"])

    r = client.delete(f"/tags/{tag_id}")
    assert r.status_code == 204

    r = client.get(f"/notes/{note2_id}")
    assert r.status_code == 200
    assert not r.json()["tags"]
