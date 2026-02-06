import json
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from config import CONFIG

WEEKDAY_MAP = {
    "mandag": 0,
    "tirsdag": 1,
    "onsdag": 2,
    "torsdag": 3,
    "fredag": 4,
    "lordag": 5,
    "sondag": 6,
}

WEEKDAY_PATTERNS = [
    r"mandag",
    r"tirsdag",
    r"onsdag",
    r"torsdag",
    r"fredag",
    r"lordag",
    r"sondag",
]

DATE_RE = re.compile(r"(\d{1,2})[\./-](\d{1,2})(?:[\./-](\d{2,4}))?")


def _base_dir():
    return Path(__file__).resolve().parents[2]


def _normalize_text(value):
    return (value or "").lower().replace("\u00f8", "o").replace("\u00e5", "a").replace("\u00e6", "ae")


def extract_text_from_pdf(path):
    errors = []
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        pages_text = [p.get_text("text") for p in doc]
        text = "\n\n".join(pages_text)
        return {
            "text": text,
            "method": "pymupdf",
            "page_count": doc.page_count,
        }
    except Exception as e:
        errors.append(f"pymupdf: {e}")

    try:
        from pdfminer.high_level import extract_text
        text = extract_text(path)
        return {
            "text": text,
            "method": "pdfminer",
            "page_count": 1,
        }
    except Exception as e:
        errors.append(f"pdfminer: {e}")

    raise RuntimeError("PDF text extraction failed: " + "; ".join(errors))


def text_is_sufficient(text, page_count, min_chars_per_page=50):
    alpha_count = sum(1 for c in text if c.isalpha())
    if page_count <= 0:
        page_count = 1
    return (alpha_count / page_count) >= min_chars_per_page


def _detect_weekday(line):
    lower = _normalize_text(line)
    for pat in WEEKDAY_PATTERNS:
        if re.search(rf"\b{pat}\b", lower):
            return WEEKDAY_MAP.get(pat)
    return None


def _strip_weekday_prefix(line):
    lower = _normalize_text(line)
    for pat in WEEKDAY_PATTERNS:
        m = re.search(rf"\b{pat}\b", lower)
        if m:
            return line[m.end():].strip(" -:\t")
    return line


def parse_ukeplan_text(text, base_date):
    if not isinstance(base_date, date):
        raise ValueError("base_date must be a date")

    week_start = base_date - timedelta(days=base_date.weekday())
    lines = [l.strip() for l in text.splitlines()]

    events = []
    current_day = None

    for line in lines:
        if not line:
            continue

        detected = _detect_weekday(line)
        if detected is not None:
            current_day = detected
            remainder = _strip_weekday_prefix(line)
            remainder = DATE_RE.sub("", remainder).strip(" -:\t")
            if remainder:
                events.append(_make_event(week_start, current_day, remainder))
            continue

        if current_day is not None:
            events.append(_make_event(week_start, current_day, line))

    return events


def _make_event(week_start, weekday_index, text):
    event_date = week_start + timedelta(days=weekday_index)
    title = text.strip()
    return {
        "date_iso": event_date.strftime("%Y-%m-%d"),
        "title": title,
        "description": "",
        "weekday_index": weekday_index,
        "confidence": 0.8,
    }


def load_latest_ukeplan(path=None):
    if path is None:
        path = _base_dir() / "data" / "ukeplan" / "latest.json"

    path = Path(path)
    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    events = payload.get("events", [])
    if not isinstance(events, list):
        return []

    today = datetime.now().date()
    monday_this = today - timedelta(days=today.weekday())

    out = []
    exclude_prefixes = CONFIG.get("UKEPLAN_EXCLUDE_PREFIXES", [])
    for evt in events:
        date_str = evt.get("date_iso")
        if not date_str:
            continue
        try:
            event_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        monday_event = event_date - timedelta(days=event_date.weekday())
        week_offset = (monday_event - monday_this).days // 7
        days_ahead = (event_date - today).days
        weekday_index = event_date.weekday()

        summary = evt.get("title") or evt.get("description") or "Ukeplan"
        if exclude_prefixes:
            if any(summary.lower().startswith(p.lower()) for p in exclude_prefixes):
                continue
        start = datetime(event_date.year, event_date.month, event_date.day, 8, 0, 0).strftime("%Y-%m-%d %H:%M:%S")

        out.append({
            "summary": summary,
            "start": start,
            "weekday_index": weekday_index,
            "week_offset": week_offset,
            "days_ahead": days_ahead,
        })

    return out
