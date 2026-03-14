from dataclasses import dataclass
import re
from typing import Optional, List


@dataclass
class ExtractedItem:
    text: str
    kind: str
    deadline: Optional[str]
    confidence: float


def _detect_deadline(text: str) -> Optional[str]:
    match = re.search(r"\b(?:by|due)\s+([\w\d\s\-/,]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else None


def extract_action_items_structured(text: str) -> List[ExtractedItem]:
    lines = [line.strip('- ').strip() for line in text.splitlines() if line.strip()]
    items: List[ExtractedItem] = []

    trigger_verbs = {"review", "send", "fix", "deploy", "implement", "update", "test"}
    trigger_phrases = ["need to", "must", "please", "should"]

    for line in lines:
        normalized = line.lower()
        kind = None
        confidence = 0.0

        if normalized.startswith("todo:"):
            kind = "TODO"
            confidence = 1.0
        elif normalized.startswith("action:"):
            kind = "ACTION"
            confidence = 1.0
        elif normalized.endswith("!"):
            kind = "EXCLAMATION"
            confidence = 0.8
        elif any(normalized.startswith(verb + " ") for verb in trigger_verbs):
            kind = "VERB"
            confidence = 0.9
        elif any(phrase in normalized for phrase in trigger_phrases):
            kind = "TRIGGER_PHRASE"
            confidence = 0.7

        if kind is not None:
            deadline = _detect_deadline(line)
            items.append(ExtractedItem(text=line, kind=kind, deadline=deadline, confidence=confidence))

    return items


def extract_action_items(text: str) -> List[str]:
    # Backward-compatible wrapper that returns only text strings
    return [item.text for item in extract_action_items_structured(text)]


