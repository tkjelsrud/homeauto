import os
import sys
from datetime import date

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web')))

from integration.ukeplan import extract_text_from_pdf, parse_ukeplan_text


def test_ukeplan_dummy_pdf_parsing():
    pdf_path = os.path.join(os.path.dirname(__file__), "ukeplan_dummy.pdf")
    assert os.path.exists(pdf_path)

    base_date = date(2026, 2, 2)  # Monday
    extract = extract_text_from_pdf(pdf_path)
    text = extract["text"]

    events = parse_ukeplan_text(text, base_date)
    assert events

    by_date = {}
    for evt in events:
        by_date.setdefault(evt["date_iso"], []).append(evt["title"])

    assert "2026-02-02" in by_date
    assert "4A har mat og helse på kjøkkenet. Ta med forkle og hårstrikk." in by_date["2026-02-02"]

    assert "2026-02-03" in by_date
    assert "4B skal på forfatterbesøk med Nora Dåsnes i skolens samlingssal." in by_date["2026-02-03"]

    assert "2026-02-04" in by_date
    assert "4A skal på forfatterbesøk med Nora Dåsnes i skolens samlingssal." in by_date["2026-02-04"]

    assert "2026-02-05" in by_date
    assert "Husk gymtøy, gymsko, håndkle + såpe til kroppsøving." in by_date["2026-02-05"]

    assert "2026-02-06" in by_date
    assert "4B skal på svømming på Nordtvet bad. Husk: badetøy, håndkle og såpe." in by_date["2026-02-06"]
