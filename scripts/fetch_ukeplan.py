#!/usr/bin/env python3
import argparse
import json
import logging
import os
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "ukeplan"
STATE_PATH = DATA_DIR / "state.json"
LATEST_PATH = DATA_DIR / "latest.json"

DEFAULT_FOLDER_ID = "1HfWeVET0ihoUGSn9AcLiHHXs81qlecXu"
DEFAULT_PATTERN = "uke-"

sys.path.insert(0, str(BASE_DIR / "web"))
from integration.ukeplan import extract_text_from_pdf, text_is_sufficient, parse_ukeplan_text


def _load_state():
    if not STATE_PATH.exists():
        return {}
    try:
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_config():
    config_path = BASE_DIR / "config.json"
    if not config_path.exists():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _latest_is_fresh(max_age_days=7):
    if not LATEST_PATH.exists():
        return False
    mtime = datetime.fromtimestamp(LATEST_PATH.stat().st_mtime)
    if (datetime.now() - mtime) > timedelta(days=max_age_days):
        return False
    try:
        with open(LATEST_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return isinstance(payload.get("events"), list)
    except Exception:
        return False


def _parse_rfc3339(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def _find_latest_pdf(folder_id, pattern, credentials_path):
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials

    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
    drive = build("drive", "v3", credentials=creds)

    q = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    if pattern:
        q += f" and name contains '{pattern}'"

    res = drive.files().list(
        q=q,
        orderBy="modifiedTime desc",
        pageSize=1,
        fields="files(id,name,modifiedTime)",
    ).execute()

    files = res.get("files", [])
    return files[0] if files else None


def _download_file(file_id, dest_path, credentials_path):
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
    from googleapiclient.http import MediaIoBaseDownload
    import io

    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
    drive = build("drive", "v3", credentials=creds)

    request = drive.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        _, done = downloader.next_chunk()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(fh.getvalue())


def _write_json_atomic(path, payload):
    path = Path(path)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def _is_too_old(modified_time, max_days=14):
    if modified_time is None:
        return False
    now = datetime.now(timezone.utc)
    age = now - modified_time
    return age > timedelta(days=max_days)


def _summarize_events(events):
    return {
        "count": len(events),
        "weekday_counts": {i: 0 for i in range(7)},
    }


def _filter_events(events, exclude_prefixes):
    if not exclude_prefixes:
        return events
    out = []
    for evt in events:
        title = (evt.get("title") or "").strip()
        if any(title.lower().startswith(p.lower()) for p in exclude_prefixes):
            continue
        out.append(evt)
    return out


def run(args):
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.force and _latest_is_fresh(max_age_days=7):
        logging.info("latest.json is fresh (< 7 days). Skipping processing.")
        return 0

    if args.file:
        pdf_path = Path(args.file)
        if not pdf_path.exists():
            logging.error(f"File not found: {pdf_path}")
            return 1
        file_meta = {
            "id": "local",
            "name": pdf_path.name,
            "modifiedTime": datetime.now(timezone.utc).isoformat(),
        }
    else:
        credentials_path = args.credentials or (BASE_DIR / "creds" / "service-account.json")
        if not Path(credentials_path).exists():
            logging.error(f"Missing credentials: {credentials_path}")
            return 1

        file_meta = _find_latest_pdf(args.folder_id, args.pattern, credentials_path)
        if not file_meta:
            logging.info("No matching PDF found.")
            return 0

        modified_time = _parse_rfc3339(file_meta.get("modifiedTime"))
        if _is_too_old(modified_time, max_days=14):
            logging.info("Latest file is older than 14 days. Skipping parsing.")
            return 0

        pdf_path = DATA_DIR / f"{file_meta['id']}.pdf"
        if not pdf_path.exists() or args.force_download:
            _download_file(file_meta["id"], pdf_path, credentials_path)

    extract = extract_text_from_pdf(str(pdf_path))
    text = extract.get("text", "")
    if not text_is_sufficient(text, extract.get("page_count", 1)):
        logging.info("Text extraction looks insufficient (likely scanned PDF). Skipping parsing.")
        return 0

    modified_time = _parse_rfc3339(file_meta.get("modifiedTime"))
    base_date = (modified_time or datetime.now(timezone.utc)).date()

    events = parse_ukeplan_text(text, base_date)
    for evt in events:
        evt["source_file_id"] = file_meta.get("id")

    config = _load_config()
    exclude_prefixes = config.get("UKEPLAN_EXCLUDE_PREFIXES", [])
    events = _filter_events(events, exclude_prefixes)

    summary = _summarize_events(events)

    if args.dry_run:
        logging.info(f"Found {len(events)} events from {file_meta.get('name')} ({file_meta.get('id')})")
        logging.info(f"Summary: {summary}")
        logging.info("Sample text:\n" + "\n".join(text.splitlines()[:20]))
        return 0

    payload = {
        "source_file_id": file_meta.get("id"),
        "source_name": file_meta.get("name"),
        "modified_time": file_meta.get("modifiedTime"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "events": events,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_out = DATA_DIR / f"{file_meta.get('id', 'latest')}.json"
    _write_json_atomic(file_out, payload)
    _write_json_atomic(LATEST_PATH, payload)

    state = _load_state()
    state["last_file_id"] = file_meta.get("id")
    state["last_modified_time"] = file_meta.get("modifiedTime")
    _save_state(state)

    logging.info(f"Wrote {len(events)} events to {LATEST_PATH}")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder-id", default=DEFAULT_FOLDER_ID)
    parser.add_argument("--pattern", default=DEFAULT_PATTERN)
    parser.add_argument("--credentials", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--force-download", action="store_true")
    parser.add_argument("--file", help="Process a local PDF instead of Google Drive")
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
