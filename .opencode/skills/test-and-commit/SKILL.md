---
name: test-and-commit
description: Run all unit tests, and if and only if all tests pass, automatically commit all staged changes to git with an auto-generated message summarizing the changes.
---

## What I do

- Run all pytest unit tests (`tests/`)
- If (and only if) all tests pass, commit all staged changes to git with an auto-generated commit message summarizing what was changed
- If any test fails, nothing is committed and failure is shown

## When to use me

Use this skill when you want your code to be committed **only when all tests succeed, and every commit message reflects the actual files/changes made**. This enforces atomic, reliable, and self-describing git commits.

## Usage

**Run all tests, then commit if and only if they pass:**

```bash
cd /Users/tkjelsrud/Public/homeauto && \
source venv/bin/activate && \
pytest tests/ && \
git add . && \
git commit -m "[test-and-commit] All tests pass – auto commit" -m "$(git diff --cached --stat)"
```

Or, for a multi-line summary including a section heading:
```bash
git commit -m "[test-and-commit] All tests pass – auto commit" \
  -m "Changes:\n$(git diff --cached --stat)"
```

**If tests fail:**
- No commit is made; pytest output highlights failure.

## Requirements
- Python virtualenv must be active (venv/)
- pytest must be installed
- The project must be a git repository

## Example Output

If all tests pass:
```
==================== 11 passed in 8.00s ====================
[test-and-commit] All tests pass – auto commit

Changes:
 web/routes.py     | 10 +++++++---
 requirements.txt  |  2 +-
 2 files changed, 8 insertions(+), 4 deletions(-)
```
If any test fails:
```
==================== 8 passed, 3 failed in 7.95s ====================
No changes were committed.
```
