from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
from ollama import chat
from dotenv import load_dotenv

load_dotenv()

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    """Heuristic extraction from plain text.

    This original implementation does not use any external AI models and is
    retained for compatibility and as a fallback.  It remains unchanged so that
    the behaviour of existing callers is predictable.
    """

    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            # Remove any keyword prefixes ("todo:", "action:", etc.)
            for prefix in KEYWORD_PREFIXES:
                if cleaned.lower().startswith(prefix):
                    cleaned = cleaned[len(prefix) :].strip()
                    break
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def extract_action_items_llm(text: str) -> List[str]:
    """Use an LLM to pull out action items from *text*.

    The function attempts to invoke an Ollama model (``lama3.1``) to perform
    the extraction.  The prompt instructs the model to respond with a plain
    JSON array of strings.  If the call fails or the result cannot be
    interpreted, we simply delegate back to :func:`extract_action_items` to
    preserve sensible behaviour.
    """

    try:
        prompt = (
            "Extract the action items from the following text. "
            "Return only a JSON array of strings.\n\n" + text.strip()
        )
        response = chat(
            model="lama3.1",
            messages=[{"role": "user", "content": prompt}],
        )
        items = json.loads(response)
        if isinstance(items, list) and all(isinstance(i, str) for i in items):
            # dedupe while preserving order
            seen: set[str] = set()
            unique: List[str] = []
            for itm in items:
                lowered = itm.lower()
                if lowered in seen:
                    continue
                seen.add(lowered)
                unique.append(itm)
            return unique
    except Exception:  # pylint: disable=broad-except
        pass

    # fallback to old behaviour
    return extract_action_items(text)


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters
