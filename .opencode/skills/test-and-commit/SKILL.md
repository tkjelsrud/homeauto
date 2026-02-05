---
name: test-and-commit
description: Run all unit tests, and if and only if all tests pass, automatically commit all staged changes to git.
---

## What I do

- Run all pytest unit tests (`tests/`)
- If (and only if) all tests pass, commit all staged changes to git with a default message
- If any test fails, nothing is committed and failure is shown

## When to use me

Use this skill when you want to ensure your code is only committed when all unit tests succeed. This enforces atomic and reliable git commits.

## Usage

**Run all tests, then commit if and only if they pass:**

```bash
cd /Users/tkjelsrud/Public/homeauto && \
source venv/bin/activate && \
pytest tests/ && \
git add . && \
git commit -m "Tested: all unit tests pass"
```

**If tests fail:**
- No commit is made; pytest output highlights failure.

**To specify a custom commit message:**
Change the message in `git commit -m "..."`

## Requirements
- Virtualenv must be active (venv/)
- pytest must be installed
- The project must be a git repository
- All changes to be committed must be staged (or use `git add .` before)

## Example Output

If all tests pass:
```
==================== 11 passed in 8.00s ====================
[Tested: all unit tests pass]
[Git commit hash: abcdef1]
```
If any test fails:
```
==================== 8 passed, 3 failed in 7.95s ====================
No changes were committed.
```
