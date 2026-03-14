# /tests — Run Tests with Coverage

Run the full test suite (or a targeted subset) and report results with coverage analysis.

---

## Usage

```
/tests
/tests backend/tests/test_tasks.py
/tests -k "test_create"
```

`$ARGUMENTS` — optional pytest marker, keyword (`-k`), or path to a specific test file.

---

## Steps

1. **Run tests** from the `week4/` directory:

```bash
cd week4
pytest -q backend/tests $ARGUMENTS --maxfail=3 -x
```

2. **If all tests pass**, run coverage:

```bash
pytest --cov=backend/app --cov-report=term-missing backend/tests $ARGUMENTS
```

3. **Summarize results**:
   - Total tests: passed / failed / skipped
   - Coverage percentage per module
   - List any lines not covered (from `term-missing` output)

4. **If tests fail**:
   - Print the full failure traceback
   - Identify the failing test name and the assertion that broke
   - Suggest the most likely fix (wrong status code, missing field, DB state issue, etc.)
   - Do NOT auto-fix the code unless explicitly asked

5. **Always end with one of**:
   - ✅ All tests passing — coverage at X%
   - ❌ N test(s) failed — see suggestions above

---

## Safety Notes

- Read-only diagnostics by default — does not modify any source files.
- Safe to run repeatedly (idempotent).
- If the DB is in a bad state and tests fail on setup, suggest: `rm -f data/dev.db && make run` to reseed.
