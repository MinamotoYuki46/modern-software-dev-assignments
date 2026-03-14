from backend.app.services.extract import extract_action_items, extract_action_items_structured, ExtractedItem


def test_extract_action_items():
    text = """
    This is a note
    - TODO: write tests
    - ACTION: review PR
    - Ship it!
    Not actionable
    """.strip()
    items = extract_action_items(text)
    assert "TODO: write tests" in items
    assert "ACTION: review PR" in items
    assert "Ship it!" in items


def test_extract_action_items_structured():
    text = """
    - TODO: write tests by Friday
    - Please fix the bug
    - deploy API
    - Not an action
    """.strip()
    extracted = extract_action_items_structured(text)
    assert any(item.kind == "TODO" and item.deadline == "Friday" for item in extracted)
    assert any(item.kind == "TRIGGER_PHRASE" for item in extracted)
    assert any(item.kind == "VERB" for item in extracted)
    assert all(isinstance(item, ExtractedItem) for item in extracted)



