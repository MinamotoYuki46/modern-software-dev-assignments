import os
import pytest

from ..app.services.extract import (
    extract_action_items,
    extract_action_items_llm,
)


def test_extract_bullets_and_checkboxes():
    text = """
    Notes from meeting:
    - [ ] Set up database
    * implement API extract endpoint
    1. Write tests
    Some narrative sentence.
    """.strip()

    # verify original heuristics still work
    items = extract_action_items(text)
    assert "Set up database" in items
    assert "implement API extract endpoint" in items
    assert "Write tests" in items


def test_extract_llm_serves_as_fallback(monkeypatch):
    # we'll fake the ollama chat response so tests don't require a model
    fake = '["pick up groceries", "submit report"]'
    monkeypatch.setattr(
        "week2.app.services.extract.chat", lambda **kwargs: fake
    )

    text = "Some meeting notes"
    items = extract_action_items_llm(text)
    assert items == ["pick up groceries", "submit report"]


def test_extract_llm_empty_and_keywords(monkeypatch):
    # ensure model errors fall back to heuristic
    def bad_chat(**kwargs):
        raise RuntimeError("model not available")

    monkeypatch.setattr("week2.app.services.extract.chat", bad_chat)

    # empty input should return an empty list
    assert extract_action_items_llm("") == []

    # keyword prefixes should still be caught by heuristics
    kw_text = "todo: clean room\naction: send email"
    items = extract_action_items_llm(kw_text)
    assert "clean room" in items
    assert "send email" in items


def test_extract_llm_bullets_and_empty(monkeypatch):
    # simulate an LLM response that mirrors bullet list extraction
    fake = '["Set up database", "implement API extract endpoint", "Write tests"]'
    monkeypatch.setattr("week2.app.services.extract.chat", lambda **kwargs: fake)

    text = "- Set up database\n* implement API extract endpoint\n1. Write tests"
    items = extract_action_items_llm(text)
    assert items == ["Set up database", "implement API extract endpoint", "Write tests"]

    # if model returns an empty list we still get empty result
    monkeypatch.setattr("week2.app.services.extract.chat", lambda **kwargs: "[]")
    assert extract_action_items_llm("") == []


def test_extract_llm_invalid_json_fallback(monkeypatch):
    # bad JSON from model should revert to heuristics
    monkeypatch.setattr("week2.app.services.extract.chat", lambda **kwargs: "not a json")
    text = "todo: clean room"
    items = extract_action_items_llm(text)
    assert "clean room" in items

