import pytest
import pandas as pd
from core.config import load_settings
from observability.quality import run_data_quality_checks, build_freshness_report

def test_data_quality_checks_pass():
    settings = load_settings()
    df_clean = pd.read_json(settings.paths.clean_json)
    
    # Clean data should pass quality checks
    res = run_data_quality_checks(df_clean, settings, report_name="test_clean")
    assert res["success"] is True

def test_data_quality_checks_fail_on_corrupted():
    settings = load_settings()
    # Create corrupted sample
    corrupted_data = pd.DataFrame([
        {
            "paper_id": "10.001/1",
            "title": "Valid title 1",
            "summary": "Short", # < 30 chars -> fails summary length
            "text_for_embedding": "Some text"
        },
        {
            "paper_id": "10.001/1", # Duplicate id -> fails unique ID check
            "title": "Valid title 2",
            "summary": "This summary has plenty of length to easily exceed thirty characters.",
            "text_for_embedding": "Some text 2"
        },
        {
            "paper_id": None, # Null id -> fails not-null
            "title": "Valid title 3",
            "summary": "This summary has plenty of length to easily exceed thirty characters.",
            "text_for_embedding": "Some text 3"
        }
    ])
    res = run_data_quality_checks(corrupted_data, settings, report_name="test_corrupted_sample")
    assert res["success"] is False

def test_build_freshness_report():
    settings = load_settings()
    df = pd.DataFrame({
        "paper_id": ["1", "2", "3", "4"],
        "published": ["2026-08-01", "2026-08-15", "2026-09-01", "2025-01-01"],
        "age_days": [30, 20, 10, 400] # Only 1 stale out of 4 (25% stale <= 25% SLA)
    })
    report = build_freshness_report(df, settings, report_path=settings.paths.quality_dir / "test_freshness.json")
    assert report["total_rows"] == 4
    assert report["stale_rows"] == 1
    assert report["stale_ratio"] == 0.25
    assert report["is_fresh"] is True

    # Test stale SLA failure (> 25%)
    df_stale = pd.DataFrame({
        "paper_id": ["1", "2", "3", "4"],
        "published": ["2026-08-01", "2025-01-01", "2025-01-01", "2025-01-01"],
        "age_days": [30, 400, 400, 400] # 3 stale out of 4 (75% stale > 25% SLA)
    })
    report_stale = build_freshness_report(df_stale, settings, report_path=settings.paths.quality_dir / "test_stale.json")
    assert report_stale["is_fresh"] is False
    assert report_stale["stale_ratio"] == 0.75
