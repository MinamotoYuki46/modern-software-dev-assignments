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

```bash
# from project root
cd week2
poetry install          # install dependencies
poetry run uvicorn week2.app.main:app --reload
```

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

```bash
poetry run pytest week2/tests
```

* `test_extract.py` contains unit tests for both the heuristic and LLM
  extraction functions, including fallback behaviour when the model fails.
* `test_api.py` exercises the FastAPI routes via `fastapi.testclient`, mocking
  the Ollama call and using a temporary database file.

## Directory structure

```
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
```

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