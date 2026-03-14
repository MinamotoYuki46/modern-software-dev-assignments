# /docs-sync — Sync API.md with Current OpenAPI Spec

Read the live OpenAPI spec from the running server and update `docs/API.md` to match.
Also detects route additions, removals, and signature changes since the last sync.

---

## Usage

```
/docs-sync
```

No arguments required. The app must be running on `http://localhost:8000`.

---

## Steps

1. **Fetch the live spec**:

```bash
curl -s http://localhost:8000/openapi.json
```

If the server is not running, instruct the user to run `make run` first and abort.

2. **Read the current docs**:

```bash
cat week4/docs/API.md
```

3. **Diff the routes** — compare every `(METHOD, path)` pair in `openapi.json` against the routes documented in `API.md`:
   - 🟢 **Added**: present in spec, missing from docs
   - 🔴 **Removed**: present in docs, missing from spec
   - 🟡 **Changed**: same path but different parameters, response schema, or description

4. **Rewrite `docs/API.md`** with the following structure for every route:

```markdown
## <METHOD> <path>

**Summary**: <operationId or summary from spec>

**Description**: <description if present>

### Request

- **Path params**: list or "None"
- **Query params**: list or "None"
- **Body** (JSON):
  ```json
  { <example derived from schema> }
  ```

### Response

- **200**: <description + example>
- **422**: Validation error (automatic)
- **<other codes>**: <description>
```

5. **Print a delta summary** at the end:

```
docs-sync complete.
🟢 Added:   POST /tasks, GET /tasks/{id}
🔴 Removed: (none)
🟡 Changed: GET /tasks — added query param `status`
TODOs: Add request examples for POST /tasks (no example in spec)
```

---

## Safety Notes

- Only modifies `docs/API.md` — no source code is touched.
- Idempotent: running twice produces the same result.
- If `docs/API.md` does not exist yet, create it from scratch.
- Do not remove manually-written notes in `API.md` that appear under a `<!-- custom -->` HTML comment block.
