from dataclasses import dataclass
import re


@dataclass
class ExtractedItem:
    text: str
    kind: str
    deadline: str | None = None
    confidence: float = 0.0


_TRIGGER_PHRASES = ["need to", "must", "please", "should"]
_ACTION_VERBS = ["review", "send", "fix", "deploy", "update", "implement", "test", "check"]


def _parse_deadline(line: str) -> str | None:
    m = re.search(r"\bby\s+([A-Za-z0-9\-/]+(?:\s+[A-Za-z0-9\-/]+)*)", line, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def extract_action_items_structured(text: str) -> list[ExtractedItem]:
    lines = [line.strip("- ") for line in text.splitlines() if line.strip()]
    results: list[ExtractedItem] = []

    for line in lines:
        normalized = line.strip()
        key = normalized.lower()

        kind: str | None = None
        confidence = 0.0

        if key.startswith("todo:"):
            kind = "TODO"
            confidence = 0.95
            action_text = normalized
        elif key.startswith("action:"):
            kind = "ACTION"
            confidence = 0.95
            action_text = normalized
        elif any(key.startswith(p) for p in _TRIGGER_PHRASES):
            kind = "TRIGGER_PHRASE"
            confidence = 0.85
            action_text = normalized
        elif any(key.startswith(v) for v in _ACTION_VERBS):
            kind = "ACTION_VERB"
            confidence = 0.85
            action_text = normalized
        elif normalized.endswith("!"):
            kind = "EXCLAMATION"
            confidence = 0.65
            action_text = normalized
        else:
            continue

        deadline = _parse_deadline(normalized)
        results.append(ExtractedItem(text=action_text, kind=kind, deadline=deadline, confidence=confidence))

    return results


def extract_action_items(text: str) -> list[str]:
    return [item.text for item in extract_action_items_structured(text)]



