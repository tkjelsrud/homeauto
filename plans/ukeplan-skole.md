# Ukeplan (skole)

Goal: automatically find the latest PDF in the shared Google Drive folder, convert it to plain text (text-based PDFs only; no OCR), extract structured events/entries and make them available to the `bigcalendar` API.

Overview
- Locate the latest PDF in the Drive folder (by modified time and filename pattern).
- Download the PDF to the server.
- Convert PDF → text (text-based PDFs only; no OCR).
- Parse the text into structured entries (dates, titles, descriptions) with language-aware parsing (Norwegian).
- Cache/store structured data and surface it from `bigcalendar` (or merge into existing calendar data).

Drive access and discovery (recommended)
- Use Google Drive API (recommended for reliability):
  - Scope: `https://www.googleapis.com/auth/drive.readonly`.
  - Prefer a service account with access to the folder, or OAuth credentials if a user flow is needed.
- Query to find latest PDF in folder (python/googleapiclient example):
  - Filenames include week numbers like `uke-6-og-7` or `uke-5`, so you can filter with a name pattern and still order by modified time.

```
# list latest pdf in folder
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = Credentials.from_service_account_file('creds/service-account.json', scopes=SCOPES)
drive = build('drive', 'v3', credentials=creds)
folder_id = '1HfWeVET0ihoUGSn9AcLiHHXs81qlecXu'
res = drive.files().list(
    q=f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false",
    orderBy='modifiedTime desc',
    pageSize=1,
    fields='files(id,name,modifiedTime)'
).execute()
files = res.get('files', [])
if files:
    latest = files[0]
    file_id = latest['id']
    # download with files().get_media(fileId=file_id)
```

- If the folder/files are publicly shared and you prefer not to use the API, a lightweight fallback is to fetch the folder's HTML and follow the file links — fragile and not recommended for long-term use.

Downloading the file
- Use `drive.files().get_media(fileId=...)` and stream to disk. Save metadata (id, modifiedTime) to skip reprocessing identical files.

PDF → text conversion (text-based PDFs only)

Note: There is no way to reliably extract text from arbitrary PDFs using only Python's standard library. To be cross-platform and avoid heavy system dependencies where possible, prefer widely-available, pip-installable libraries. This plan only supports text-based PDFs and explicitly does not perform OCR on scanned/image-only PDFs.

Priority strategy (recommended):
1) Try PyMuPDF (aka `fitz`) — single dependency, cross-platform, good at extracting text. Install: `pip install PyMuPDF`.
   - Use `fitz.open('file.pdf')` and call `.get_text()` for each page; if text output looks populated, use it.
2) If PyMuPDF is unavailable or unsuitable, fall back to `pdfminer.six` for text extraction (pure Python, `pip install pdfminer.six`).
   - Use `pdfminer.high_level.extract_text('input.pdf')` to get text.

Heuristics for text-only support
- After extracting text with PyMuPDF/pdfminer, compute a simple score: number of alphabetic characters / file pages. If score < threshold (e.g., < 50 chars/page), treat as scanned and abort parsing (log and skip).

Code snippets (examples)

PyMuPDF text-extract (recommended):

```python
import fitz  # PyMuPDF

def extract_with_pymupdf(path):
    doc = fitz.open(path)
    pages_text = [p.get_text("text") for p in doc]
    joined = "\n\n".join(pages_text)
    return joined
```

pdfminer.six text-extract (fallback):

```python
from pdfminer.high_level import extract_text

def extract_with_pdfminer(path):
    return extract_text(path)
```

Minimal external binaries
- Poppler (`pdftotext`): optional; used only if you choose system `pdftotext` fallback.

Dependency summary (prioritized, cross-platform when possible)
- PyMuPDF (pip) — preferred: fast, extracts text; cross-platform.
- pdfminer.six (pip) — fallback for text extraction from text-based PDFs.

Why this order?
- PyMuPDF gives the best single-package experience: it extracts text without requiring Poppler; it's widely used and cross-platform.
- `pdfminer.six` is pure-Python and works well for many text PDFs when PyMuPDF isn't available.

Trade-offs and notes
- There is no perfect "standard library only" path for PDF text extraction — third-party libraries are necessary. Prioritize pip-installable packages to keep cross-platform installs simple.
- This plan does not attempt OCR. If a PDF is scanned/image-only, it will be skipped and logged.
- For reliability, include a short health-check in the script that logs which extraction method was used and a confidence score so you can monitor failures.

Decide by quick heuristic: if PyMuPDF/pdfminer output contains very few letters/lines, treat as scanned and skip parsing.

Parsing / extracting events
- Normalize whitespace and remove headers/footers.
- Look for date markers: Norwegian weekday names and date formats (e.g., "mandag 2. februar", "02.02."). Use `dateparser` (configure locale `['no']`) or `dateutil` with custom parsing. each entry having in Norwegian like "Mandag, Tirsdag, " etc, this has to be mapped to this weeks days.
- Only the newest matching file should be parsed (if several matches).
- If the file is old (check its date from the Drive file metadata / exposed URL date), i.e., more than 14 days, it should not be parsed because it is outdated.
- Strategy:
  1) Split text into candidate blocks by double newlines or headings.
  2) For each block, search for a date (or weekday) and treat the remainder as the event description.
  3) Map ambiguous entries heuristically (e.g., week ranges → multiple events).
- Store parsed events as: `{date_iso, title, description, source_file_id, confidence}`.

Integration with bigcalendar API
- Create a small script `scripts/fetch_ukeplan.py` that:
  1) Finds latest PDF (Drive API).
  2) Downloads it to `data/ukeplan/<file_id>.pdf`.
  3) Converts + parses into `data/ukeplan/<file_id>.json` (structured events).
  4) Atomically updates a symlink or writes `data/ukeplan/latest.json` with merged calendar entries.
- In `bigcalendar` function:
  - Load `data/ukeplan/latest.json` and merge events with existing sources (respect deduplication by source_file_id).
  - Schedule a periodic job (APScheduler or cron) to run `scripts/fetch_ukeplan.py` daily or hourly depending on update frequency.
  - Expose a read-only debug endpoint or service that serves `data/ukeplan/latest.json` (no admin trigger).

Idempotency & caching
- If `data/ukeplan/latest.json` exists, is valid, and is < 7 days old, skip processing and use cached output.
- Record processed file ids and modifiedTime in a small state file `data/ukeplan/state.json` to avoid reprocessing.
- Keep last N parsed files for auditing (e.g., 5 latest) so you can inspect changes if parsing fails.

Security and secrets
- Do NOT commit service account JSON into git. Store credentials in `creds/service-account.json` excluded by `.gitignore`, or use a secret manager / environment variables.

Dependencies
- System packages: `poppler-utils` (optional, for `pdftotext`).
- Python packages: `google-api-python-client`, `google-auth`, `pdfminer.six`, `dateparser`, `PyMuPDF`.

Testing & verification
- Manual run:
  - `venv/bin/python scripts/fetch_ukeplan.py --dry-run` (lists candidate file and shows first N lines of text)
  - `venv/bin/python scripts/fetch_ukeplan.py` → produces `data/ukeplan/latest.json`
- Automated tests:
  - Add a unit test that targets one fixed dummy PDF (extracted once from Drive and stored as committed test data).
  - Add a normal pytest file under `tests/` (follow existing tests) that calls the parser and asserts the output for the dummy PDF.
  - Integration test that mocks Drive API returning a sample PDF file.

Next steps (recommended)
1) Create a service account and grant it read access to the Drive folder (or confirm the folder is publicly readable). (Recommended)
2) Add `scripts/fetch_ukeplan.py` implementing discovery, download, convert, parse, and write `latest.json`.
3) Wire `bigcalendar` to read `data/ukeplan/latest.json` and add a scheduled job.

Verification checklist
- [ ] Service account created and `creds/service-account.json` placed on server (gitignored).
- [ ] `scripts/fetch_ukeplan.py` downloads the latest PDF and writes `data/ukeplan/latest.json`.
- [ ] `bigcalendar` returns ukeplan events at the same endpoint as other calendar sources.
- [ ] Add tests that validate parsing correctness for typical PDFs from the folder.

Reference: folder id `1HfWeVET0ihoUGSn9AcLiHHXs81qlecXu`

Unit test requirement (final step)
- Add a pytest unit test that uses a fixed PDF as test data to ensure extraction works end-to-end for planning purposes:
  - Create `tests/fixtures/ukeplan/sample.pdf` (committed test fixture) containing a representative ukeplan PDF.
  - Add test file `tests/test_ukeplan_parser.py` which:
    - Calls the extractor/parser code (the same functions used by `scripts/fetch_ukeplan.py`).
    - Asserts that the parsed output contains entries grouped by calendar day for a sample week (e.g., Monday–Friday), with each entry having in Norwegian like "Mandag, Tirsdag, " etc, this has to be mapped to this weeks days
    - Uses deterministic expectations (specific dates or weekday counts) so CI can fail fast if parsing regresses.
  - This test ensures the extracted text can be mapped to per-day planner entries and prevents accidental parser regressions.
