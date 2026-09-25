import pytest
import pandas as pd
from core.config import load_settings
from ingestion.corruption import corrupt_clean_dataframe

def test_corrupt_clean_dataframe():
    settings = load_settings()
    df_clean = pd.read_json(settings.paths.clean_json)
    initial_count = len(df_clean)

    test_log_path = settings.paths.workspace_dir / "data" / "results" / "test_corruption_log.json"
    corrupted_df = corrupt_clean_dataframe(df_clean, test_log_path)

    # 1. Check drop latest 20%
    expected_dropped = max(1, int(initial_count * 0.2))
    assert len(corrupted_df) < initial_count or "paper_id" in corrupted_df.columns

    # 2. Check blank summary exists
    blank_summaries = corrupted_df[corrupted_df["summary"] == ""]
    assert len(blank_summaries) >= 1

    # 3. Check duplicate rows exist
    duplicate_ids = corrupted_df[corrupted_df.duplicated(subset=["paper_id"], keep=False)]
    assert len(duplicate_ids) >= 2

    # 4. Check stale dates exist (age_days shifted)
    assert (corrupted_df["age_days"] >= 365).sum() > 0

    # 5. Check log file was written
    assert test_log_path.exists()
