# Week 4 Writeup — The Autonomous Coding Agent IRL

## Design Inspiration

The two automations in this submission were designed around two recurring pain points in everyday backend development: **test fatigue** and **documentation drift**.

The design of both automations draws directly from the Claude Code best practices guide (anthropic.com/engineering/claude-code-best-practices), specifically the guidance on:

- **CLAUDE.md as a persistent system prompt**: The guide recommends treating `CLAUDE.md` like a team-specific onboarding document that encodes project conventions, safe commands, and workflow rules so Claude never has to guess context. This influenced the structure of the CLAUDE.md file created for this project.
- **Slash commands for repeatable workflows**: The guide recommends encoding any workflow you run more than twice as a slash command, using `$ARGUMENTS` for flexibility and keeping commands focused and idempotent. The `/tests` and `/docs-sync` commands follow this pattern exactly.

The core design philosophy is **low friction, high trust**: each automation is safe to run at any time, does not auto-modify source code unless explicitly asked, and always ends with a clear summary of what changed and what needs attention.

---

## Automation 1: CLAUDE.md Guidance File

### Goals

Eliminate the repetitive context-setting that happens at the start of every Claude Code session. Without a `CLAUDE.md`, every session requires re-explaining the project structure, how to run tests, style rules, and workflow conventions. With it, Claude starts each session already knowing the project.

### Design

The `CLAUDE.md` file lives at `week4/CLAUDE.md` and covers five areas:

1. **Project overview** — stack summary so Claude immediately knows what kind of project this is.
2. **How to run** — exact `make` commands so Claude never guesses wrong invocations.
3. **Repository layout** — annotated tree pointing to every important file, including where routers, models, schemas, and tests live.
4. **Code style & tooling** — black, ruff, line length. Prevents Claude from introducing style violations.
5. **Workflow rules** — step-by-step procedures for the four most common tasks: adding an endpoint, schema changes, refactoring, and deleting a route. This encodes the team's TDD expectation (write failing test first).
6. **Safe vs. dangerous commands** — an explicit allowlist and blocklist so Claude never runs `rm -rf data/` without confirmation.

### Inputs / Outputs

- **Input**: The file is read automatically by Claude Code at session start — no manual trigger needed.
- **Output**: Claude begins every session with full project context, correctly using `make test` instead of `python -m pytest`, knowing to update `docs/API.md` after route changes, and never running destructive commands silently.

### How to Run

Place `CLAUDE.md` in the `week4/` directory. Claude Code reads it automatically. No further action required.

### Before vs. After

**Before**: Every session started with prompts like "this is a FastAPI project, run tests with `make test`, linting is ruff, don't touch the database file directly…" — repeated every time.

**After**: Claude Code reads the file at startup and behaves correctly from the first message, with no repeated context-setting needed.

### Rollback / Safety

Deleting `CLAUDE.md` reverts to the default Claude Code behavior with no project-specific context. There is no risk to source code or data — this file only affects Claude's behavior.

---

## Automation 2a: Custom Slash Command `/tests`

### Goals

Streamline the test-and-diagnose loop. Instead of running `make test`, reading raw pytest output, manually running coverage, and interpreting failures, `/tests` handles the full cycle and delivers a structured summary with actionable suggestions.

### Design

The command lives at `.claude/commands/tests.md`. It takes an optional `$ARGUMENTS` parameter (a pytest path, keyword filter, or marker) so it works both as a full suite runner and a targeted test runner.

Workflow:

1. Run `pytest -q ... --maxfail=3 -x` for fast feedback.
2. If green, automatically follow up with `--cov=backend/app --cov-report=term-missing` to identify untested lines.
3. Summarize: pass/fail counts, per-module coverage, uncovered lines.
4. On failure: print the traceback, name the failing assertion, and suggest the most likely cause — without auto-patching code (to preserve developer agency).

The command is designed to be idempotent and read-only by default.

### Inputs / Outputs

- **Input**: `/tests` (full suite) or `/tests backend/tests/test_tasks.py` or `/tests -k "test_create"`
- **Output**: Structured summary — ✅ pass/coverage report or ❌ failure diagnosis with suggestions.

### How to Run

```bash
# In Claude Code, type:
/tests
/tests backend/tests/test_tasks.py
/tests -k "test_create"
```

Claude Code picks up the command from `.claude/commands/tests.md` and executes the steps.

### Before vs. After

**Before**: Run `make test` → read dense pytest output → manually run coverage → interpret which lines are missing → guess why a test failed.

**After**: Type `/tests` → receive a clean summary of results, coverage by module, and specific fix suggestions in one response.

### Rollback / Safety

The command only runs `pytest` and `coverage` — both are read-only with respect to source files. No files are modified. Safe to run at any time.

---

## Automation 2b: Custom Slash Command `/docs-sync`

### Goals

Eliminate documentation drift between the live API and `docs/API.md`. In fast-moving backends, route signatures change frequently and documentation falls behind. `/docs-sync` fetches the live OpenAPI spec and regenerates `docs/API.md` automatically, highlighting exactly what changed.

### Design

The command lives at `.claude/commands/docs-sync.md`. It has no required arguments.

Workflow:

1. `curl http://localhost:8000/openapi.json` to get the authoritative spec.
2. Read the current `docs/API.md`.
3. Diff every `(METHOD, path)` pair: detect added, removed, and changed routes.
4. Rewrite `docs/API.md` with a consistent format: method, path, summary, request params/body, response codes.
5. Print a delta summary showing exactly what changed, with TODOs for incomplete spec entries.

A `<!-- custom -->` comment block convention protects any manually-written notes from being overwritten.

### Inputs / Outputs

- **Input**: `/docs-sync` (app must be running)
- **Output**: Updated `docs/API.md` + terminal diff summary (🟢 added, 🔴 removed, 🟡 changed routes)

### How to Run

```bash
# Start the app first
make run

# Then in Claude Code:
/docs-sync
```

### Before vs. After

**Before**: After adding a new endpoint, manually open `docs/API.md`, copy the route signature, write parameter descriptions by hand, hope nothing was missed.

**After**: Type `/docs-sync` → `docs/API.md` is fully regenerated from the live spec, with a diff showing every route that changed since the last sync.

### Rollback / Safety

Only modifies `docs/API.md`. Source code, database, and all backend files are untouched. Idempotent — running twice produces the same file. If the output is unsatisfactory, `git checkout docs/API.md` restores the previous version.

---

## How I Used the Automations to Enhance the Starter Application

### Using CLAUDE.md

`CLAUDE.md` served as the persistent context layer for all development work on the starter application. Rather than re-explaining the project structure at the start of each session, the file encodes the full repository layout, tooling expectations, and workflow rules in one place. The TDD rule ("write a failing test first, then implement") guided every change made to the backend — ensuring tests existed before any new route was considered done. The explicit safe/unsafe command list also acted as a safety guardrail, preventing accidental destructive operations (such as wiping the database) during iterative development.

### Using `/tests`

The `/tests` slash command was executed by manually running the steps defined in `tests.md` from the `week4/` directory. Since Claude Code was unavailable in this environment, the workflow was simulated directly in the terminal:

```bash
$env:PYTHONPATH="."; pytest -q backend/tests --maxfail=3 -x
pytest --cov=backend/app --cov-report=term-missing backend/tests
```

During the first run, a `PermissionError` was encountered at teardown — a Windows-specific bug where SQLite's temp file could not be deleted while still held open. This was caught immediately because the `/tests` workflow surfaces teardown errors explicitly. The fix was a targeted `try/except PermissionError` block in `conftest.py`. Subsequent runs passed cleanly with full coverage across all tested modules.

### Using `/docs-sync`

The `/docs-sync` command was simulated by fetching the live OpenAPI spec manually and comparing it against `docs/API.md`:

```bash
# Terminal 1
$env:PYTHONPATH="."; uvicorn backend.app.main:app --reload

# Terminal 2
curl -s http://localhost:8000/openapi.json
```

This process confirmed that `docs/API.md` was either missing or out of sync with the actual routes served by the application. The spec was used as the authoritative source to populate `docs/API.md` with accurate route signatures, request parameters, and response codes — exactly the workflow the `/docs-sync` command is designed to automate.