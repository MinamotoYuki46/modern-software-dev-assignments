from backend.app.services.extract import extract_action_items, extract_action_items_structured


def test_extract_action_items_structured():
    text = """
    This is a note
    - TODO: write tests by Monday
    - ACTION: review PR
    - Ship it!
    - Please update docs
    - deploy to staging by Friday
    Not actionable
    """.strip()

    structured = extract_action_items_structured(text)
    texts = [item.text for item in structured]
    kinds = [item.kind for item in structured]
    deadlines = [item.deadline for item in structured]
    confidences = [item.confidence for item in structured]

    assert "TODO: write tests by Monday" in texts
    assert "ACTION: review PR" in texts
    assert "Ship it!" in texts
    assert "Please update docs" in texts
    assert "deploy to staging by Friday" in texts

    assert "TODO" in kinds
    assert "ACTION" in kinds
    assert "EXCLAMATION" in kinds
    assert "TRIGGER_PHRASE" in kinds
    assert "ACTION_VERB" in kinds

    assert any(d == "Monday" for d in deadlines if d)
    assert any(d == "Friday" for d in deadlines if d)
    assert all(0.0 < c <= 1.0 for c in confidences)


def test_extract_action_items_wrapper():
    text = """
    - TODO: do something
    - Fix deployment
    """.strip()
    items = extract_action_items(text)
    assert items == ["TODO: do something", "Fix deployment"]



