# CLAUDE.md — Week 4 Developer Command Center

This file is automatically read by Claude Code at the start of every session.
Follow these instructions throughout all tasks in this repository.

---

## Project Overview

A minimal full-stack developer command center built with:
- **Backend**: FastAPI + SQLAlchemy + SQLite (`backend/`)
- **Frontend**: Static HTML/JS, served by FastAPI (`frontend/`)
- **Tests**: pytest (`backend/tests/`)
- **DB seed**: `data/seed.sql`
- **Docs**: `docs/` — keep `docs/API.md` in sync with `/openapi.json`

---

## How to Run

```bash
# From week4/ directory
conda activate cs146s
make run          # starts FastAPI on http://localhost:8000
make test         # runs pytest
make format       # black + ruff --fix
make lint         # ruff check only
```

- Frontend: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## Repository Layout

```
week4/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── database.py      # DB session setup
│   │   └── routers/         # Route modules (one file per resource)
│   └── tests/               # pytest test files
├── frontend/                # Static assets
├── data/
│   └── seed.sql             # SQLite seed data
├── docs/
│   └── API.md               # Human-readable API reference (keep in sync)
├── Makefile
└── writeup.md
```

---

## Code Style & Tooling

- **Formatter**: `black` (line length 88)
- **Linter**: `ruff`
- Always run `make format && make lint` before finishing any task.
- Never commit code that fails `make lint` or `make test`.

---

## Workflow Rules

1. **Adding a new endpoint**: Write a failing test first → implement → run `make test` → run `make format && make lint` → update `docs/API.md`.
2. **Schema changes**: Update `models.py` → update `schemas.py` → update `data/seed.sql` if needed → run migrations or recreate DB → fix tests.
3. **Refactoring a module**: Update imports in all affected files → run `make lint` → run `make test` → confirm no regressions.
4. **Deleting a route**: Check for usages in frontend JS → remove from router → re-sync `docs/API.md`.

---

## Safe Commands (always OK to run)

```bash
make test
make format
make lint
make run
cat backend/app/routers/*.py
cat docs/API.md
curl http://localhost:8000/openapi.json
```

## Commands to Avoid Without Confirmation

```bash
rm -rf data/          # destroys the database
drop table ...        # destructive SQL
git push --force      # dangerous rewrite
```

---

## Testing Conventions

- Test files live in `backend/tests/` and are prefixed `test_`.
- Use the `client` fixture (FastAPI `TestClient`) for HTTP tests.
- Each router should have a corresponding test file: `test_<router_name>.py`.
- Aim for at least one happy-path and one error-path test per endpoint.

---

## Docs Sync Rule

`docs/API.md` must always reflect the current state of `/openapi.json`.
After any route change, run `/docs-sync` or manually update `docs/API.md`.
