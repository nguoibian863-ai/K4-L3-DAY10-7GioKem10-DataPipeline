import pytest
from core.config import load_settings
from ingestion.crossref import load_raw_records, parse_crossref_payload

def test_load_raw_records():
    settings = load_settings()
    records = load_raw_records(settings.paths.raw_records_json)
    assert isinstance(records, list)
    assert len(records) > 0
    assert hasattr(records[0], "paper_id") and len(records[0].paper_id) > 0

def test_parse_crossref_payload():
    sample_payload = {
        "message": {
            "items": [
                {
                    "DOI": "10.1234/test.doi",
                    "title": ["Test Paper Title"],
                    "abstract": "<jats:p>This is a test abstract that has enough length to be meaningful.</jats:p>",
                    "published": {"date-parts": [[2026, 3, 15]]},
                    "author": [{"given": "Alice", "family": "Smith"}, {"given": "Bob", "family": "Jones"}],
                    "subject": ["Computer Science", "AI"]
                }
            ]
        }
    }
    parsed = parse_crossref_payload(sample_payload)
    assert len(parsed) == 1
    record = parsed[0]
    assert record.paper_id == "10.1234/test.doi"
    assert record.title == "Test Paper Title"
    assert record.published == "2026-03-15"
    assert "Alice Smith" in record.authors
    assert "Bob Jones" in record.authors
    assert "Computer Science" in record.categories
    assert "<jats:p>" not in record.summary
