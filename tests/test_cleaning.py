import pytest
from datetime import date
import pandas as pd
from ingestion.crossref import PaperRecord
from ingestion.cleaning import build_clean_dataframe

def test_build_clean_dataframe():
    sample_records = [
        PaperRecord(
            paper_id="10.1000/1",
            title="Deep Learning in Retrieval",
            summary="A comprehensive study on neural information retrieval models.",
            authors=["Alice Smith", "Bob Jones"],
            categories=["cs.IR", "cs.AI"],
            primary_category="cs.IR",
            published="2026-01-01",
            updated="2026-01-02",
            abs_url="https://doi.org/10.1000/1",
            pdf_url="",
            comment=""
        ),
        PaperRecord(
            paper_id="10.1000/2",
            title="Freshness Evaluation",
            summary="Measuring age and freshness decay in enterprise knowledge bases.",
            authors=["Carol Danvers"],
            categories=["cs.DB"],
            primary_category="cs.DB",
            published="2026-03-01",
            updated="",
            abs_url="https://doi.org/10.1000/2",
            pdf_url="",
            comment=""
        ),
        # Duplicate record that should be deduped
        PaperRecord(
            paper_id="10.1000/1",
            title="Deep Learning in Retrieval (Duplicate)",
            summary="Duplicate abstract text.",
            authors=["Alice Smith"],
            categories=["cs.IR"],
            primary_category="cs.IR",
            published="2026-01-01",
            updated="",
            abs_url="",
            pdf_url="",
            comment=""
        )
    ]

    ref_date = date(2026, 9, 25)
    df = build_clean_dataframe(sample_records, run_date=ref_date)

    # Dedup check
    assert len(df) == 2
    assert "10.1000/1" in df["paper_id"].values
    assert "10.1000/2" in df["paper_id"].values

    # Columns check
    expected_cols = [
        "paper_id", "title", "summary", "authors_joined", "categories_joined",
        "published", "age_days", "text_for_embedding"
    ]
    for col in expected_cols:
        assert col in df.columns

    # age_days calculation check
    row2 = df[df["paper_id"] == "10.1000/2"].iloc[0]
    # From 2026-03-01 to 2026-09-25 is 208 days
    assert row2["age_days"] == (ref_date - date(2026, 3, 1)).days

    # text_for_embedding check
    assert "Title: Freshness Evaluation" in row2["text_for_embedding"]
    assert "Summary: Measuring age and freshness decay" in row2["text_for_embedding"]
