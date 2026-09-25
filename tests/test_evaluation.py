import pytest
import pandas as pd
from core.config import load_settings
from evaluation.testset import build_test_set

def test_build_test_set():
    settings = load_settings()
    df_clean = pd.read_json(settings.paths.clean_json)

    test_output_path = settings.paths.workspace_dir / "data" / "eval" / "test_set_unit_test.json"
    test_set = build_test_set(df_clean, test_output_path)

    # 1. Total questions count
    assert len(test_set) == 10

    # 2. Check coverage of 4 question types
    types = {item["question_type"] for item in test_set}
    assert {"summary", "authors", "date", "categories"}.issubset(types)

    # 3. Check schema of each item
    for item in test_set:
        assert "id" in item
        assert "question_type" in item
        assert "question" in item
        assert "ground_truth" in item
        assert "ground_truth_doc_ids" in item
        assert len(item["ground_truth_doc_ids"]) > 0

    # Clean up unit test output file
    if test_output_path.exists():
        test_output_path.unlink()
