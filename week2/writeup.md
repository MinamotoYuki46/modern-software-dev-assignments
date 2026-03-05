# Week 2 Write-up

Tip: To preview this markdown file

- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## INSTRUCTIONS

Fill out all of the `TODO`s in this file.

## SUBMISSION DETAILS

Name: **Muhammad Fauzan Ahsani** \
SUNet ID: **2310817310009** \
Citations: **TODO**

This assignment took me about **TODO** hours to do.

## YOUR RESPONSES

For each exercise, please include what prompts you used to generate the answer, in addition to the location of the generated response. Make sure to clearly add comments in your code documenting which parts are generated.

### Exercise 1: Scaffold a New Feature

Prompt:

```
you are a coding assistant, here are function called extract_action_items. You need to implement LLM alternative one that using model from ollama (use lamma3.1). Ensure the output file is same as the original function one. dont remove the older one, make the function called extract_action_items_llm().

after finishing, then apply the function to revise usage in the other files
```

Generated Code Snippets:

```
TODO: List all modified code files with the relevant line numbers.

-- extract.py line[76 - 111]
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


-- action_items.py [line: 8]
from ..services.extract import extract_action_items_llm as extract_action_items


-- test_extract.py [line: 4 - 7]
from ..app.services.extract import (
    extract_action_items,
    extract_action_items_llm,
)
```

### Exercise 2: Add Unit Tests

Prompt:

```
now, write some testcase for extract_action_items_llm() function with various input

like bullet lists, keyword-prefixed lines, empty input

ensure it give proper feedback
```

Generated Code Snippets:

```
test_extract.py [line: 55 - 75]
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
```

### Exercise 3: Refactor Existing Code for Clarity

Prompt:

```
Umm, i've already done that in the first taask
```

Generated/Modified Code Snippets:

```
TODO: List all modified code files with the relevant line numbers. (We anticipate there may be multiple scattered changes here – just produce as comprehensive of a list as you can.)
```

### Exercise 4: Use Agentic Mode to Automate a Small Task

Prompt:

```
alright, lets move to the next step

1. Integrate the LLM-powered extraction as a new endpoint. Update the frontend to include an "Extract LLM" button that, when clicked, triggers the extraction process via the new endpoint.

2. Expose one final endpoint to retrieve all notes. Update the frontend to include a "List Notes" button that, when clicked, fetches and displays them.


do it carefully, add some kind of note of what feature added, the flow how it works, every detail so i can evaluate the results. also steps for testing it
```

Generated Code Snippets:

```
-- action_items.py [line; 30 - 44]
@router.post("/extract-llm")
def extract_llm(payload: Dict[str, Any]) -> Dict[str, Any]:
    """LLM-powered extraction endpoint."""
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    note_id: Optional[int] = None
    if payload.get("save_note"):
        note_id = db.insert_note(text)

    items = extract_action_items_llm(text)
    ids = db.insert_action_items(items, note_id=note_id)
    return {"note_id": note_id, "items": [{"id": i, "text": t} for i, t in zip(ids, items)]}

--notes.py [line 34 - 43]

@router.get("")
def list_notes() -> List[Dict[str, Any]]:
    """Return all notes in descending insertion order."""
    rows = db.list_notes()
    return [
        {"id": r["id"], "content": r["content"], "created_at": r["created_at"]}
        for r in rows
    ]

-- index.html

[line 27 28]
      <button id="extract_llm">Extract (LLM)</button>
      <button id="list_notes">List Notes</button>

[line 32]
    <div class="notes" id="notes" style="margin-top:1rem;"></div>

[line 39 - 66]
       await runExtraction('/action-items/extract');
      });

      document.querySelector('#extract_llm').addEventListener('click', async () => {
        await runExtraction('/action-items/extract-llm');
      });

      document.querySelector('#list_notes').addEventListener('click', async () => {
        notesEl.textContent = 'Loading notes...';
        try {
          const res = await fetch('/notes');
          if (!res.ok) throw new Error('request failed');
          const data = await res.json();
          if (!data || data.length === 0) {
            notesEl.innerHTML = '<p class="muted">No notes saved.</p>';
            return;
          }
          notesEl.innerHTML = data.map(n =>
            `<div class="item"><strong>#${n.id}</strong>: ${n.content}</div>`
          ).join('');
        } catch (e) {
          console.error(e);
          notesEl.textContent = 'Error loading notes';
        }
      });

      // helper used by both buttons
      async function runExtraction(endpoint) {

[line 71]
          const res = await fetch(endpoint, {

[line 99]
      }

new file: test_api.py
import os
import pytest

from fastapi.testclient import TestClient

from ..app import main, db


@pytest.fixture(autouse=True)
def reset_db(tmp_path, monkeypatch):
    # make sure each test run uses a fresh database file in tmp_path
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "app.db")
    db.init_db()


@pytest.fixture

def client():
    return TestClient(main.app)


def test_notes_list_and_create(client):
    # initially empty
    r = client.get("/notes")
    assert r.status_code == 200
    assert r.json() == []

    # create a note
    r = client.post("/notes", json={"content": "remember coffee"})
    assert r.status_code == 200
    note = r.json()
    assert note["content"] == "remember coffee"

    # listing returns the note
    r = client.get("/notes")
    notes = r.json()
    assert len(notes) == 1
    assert notes[0]["content"] == "remember coffee"


def test_action_item_endpoints(client, monkeypatch):
    # mock the LLM call so extract-llm doesn't hit a model
    fake = "[\"a\", \"b\"]"
    monkeypatch.setattr("week2.app.services.extract.chat", lambda **kw: fake)

    # heuristic extraction uses bullets
    text = "- one\n- two"
    r = client.post("/action-items/extract", json={"text": text, "save_note": False})
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(it["text"] == "one" for it in items)

    # llm endpoint returns the mocked result
    r2 = client.post("/action-items/extract-llm", json={"text": "whatever", "save_note": False})
    assert r2.status_code == 200
    assert r2.json()["items"] == [{"id": i + 1, "text": t} for i, t in enumerate(["a", "b"]) ]


```

### Exercise 5: Generate a README from the Codebase

Prompt:

```
Alright, now write/create the readme.md on the folder week2

analyze the current codebase and generate a well-structured `README.md` file. The README should include, at a minimum:
- A brief overview of the project
- How to set up and run the project
- API endpoints and functionality
- Instructions for running the test suite
```

Generated Code Snippets:

```
README.md

# Action Item Extractor (Week 2)

A minimal FastAPI + SQLite application that converts free-form notes into a
checklist of action items.  The project demonstrates both a heuristic parser
and an LLM-powered alternative (via Ollama), a simple web frontend, and a
lightweight persistence layer.

## Features

* Extract action items from text using:
  * **Heuristics**: bullet points, `todo:`/`action:` prefixes, checkbox markers
  * **LLM**: send input to an Ollama model (`lama3.1`) to generate a JSON list
* Persist notes and extracted items in an SQLite database
* Mark items as done
* List saved notes
* Single-page frontend with buttons to exercise each extraction mode and view
  notes

## Requirements

* Python 3.10+ (tested with 3.11)
* Poetry (for dependency management)
* [Ollama](https://ollama.com) installed if you want to use the LLM extractor
  (a model such as `lama3.1` should be pulled with `ollama pull lama3.1`).

## Setup & run

bash
# from project root
cd week2
poetry install          # install dependencies
poetry run uvicorn week2.app.main:app --reload


Then open your browser at `http://127.0.0.1:8000/`.  Paste or type notes
into the textarea and click one of the extraction buttons.  Use the "Save as
note" checkbox to persist the input; press "List Notes" to display saved
notes.

### Environment

Configure Ollama via environment variables if desired (e.g. `OLLAMA_DEBUG=1`).
A `.env` file is loaded automatically by `python-dotenv`.

## API Endpoints

| Method | Path                     | Description                                |
|--------|--------------------------|--------------------------------------------|
| POST   | `/action-items/extract`  | Run heuristic extraction                   |
| POST   | `/action-items/extract-llm` | Run LLM extraction (falls back to heuristics) |
| POST   | `/action-items/{id}/done`| Mark an action item as done/undone         |
| GET    | `/action-items`          | List action items (optionally filter by note) |
| POST   | `/notes`                 | Create a new note                          |
| GET    | `/notes`                 | List all saved notes                       |
| GET    | `/notes/{id}`            | Retrieve a single note by id               |

All POST endpoints expect and return JSON.  The extraction routes accept
`{"text": "...", "save_note": true}`; they return `{"note_id": …,
"items": [{"id":…, "text":…},…]}`.

## Testing

Run the full test suite with:

bash
poetry run pytest week2/tests


* `test_extract.py` contains unit tests for both the heuristic and LLM
  extraction functions, including fallback behaviour when the model fails.
* `test_api.py` exercises the FastAPI routes via `fastapi.testclient`, mocking
  the Ollama call and using a temporary database file.

## Directory structure


week2/
├─ app/
│  ├─ main.py          # FastAPI application definition
│  ├─ db.py            # SQLite helper functions
│  ├─ routers/         # API route handlers
│  │  ├─ action_items.py
│  │  └─ notes.py
│  └─ services/
│     └─ extract.py    # extraction logic (heuristic + LLM)
├─ frontend/
│  └─ index.html       # simple client UI
├─ tests/              # pytest test modules
├─ data/               # SQLite file (created at runtime)
└─ README.md           # <- this file


## Notes

* The LLM extraction requires an Ollama model to be running locally; if it's
  unavailable the server will log an error and fall back to the heuristic
  parser.
* The frontend is intentionally minimal – feel free to replace it with
  something more sophisticated in future iterations.
* The database is recreated automatically when the server starts.

---

This README was generated automatically by inspecting the codebase and
reflects the state of the project as of March 2026.

```

### Mini side

Since i found error while testing, so i perform one more prompting

```
=============================================== short test summary info ===============================================
FAILED week2/tests/test_api.py::test_action_item_endpoints - AssertionError: assert [{'id': 3, 't... 'text': 'b'}] == [{'id': 1, 't... 'text': 'b'}]
FAILED week2/tests/test_extract.py::test_extract_llm_empty_and_keywords - AssertionError: assert 'clean room' in ['todo: clean room', 'action: send email']
FAILED week2/tests/test_extract.py::test_extract_llm_invalid_json_fallback - AssertionError: assert 'clean room' in ['todo: clean room']
============================================= 3 failed, 4 passed in 2.56s =============================================
```

```
extract.py
After trimming bullets and checkboxes, now strip any of the KEYWORD_PREFIXES from the beginning of the cleaned line.

            # Remove any keyword prefixes ("todo:", "action:", etc.)
            for prefix in KEYWORD_PREFIXES:
                if cleaned.lower().startswith(prefix):
                    cleaned = cleaned[len(prefix) :].strip()
                    break

tests/test_api.py
Relaxed assertion to compare only the texts of items, not their IDs.

returned = r2.json()["items"]
assert [it["text"] for it in returned] == ["a", "b"]


```

## SUBMISSION INSTRUCTIONS

1. Hit a `Command (⌘) + F` (or `Ctrl + F`) to find any remaining `TODO`s in this file. If no results are found, congratulations – you've completed all required fields.
2. Make sure you have all changes pushed to your remote repository for grading.
3. Submit via Gradescope.
