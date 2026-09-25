from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Tao bo evaluation set (10 cau hoi) tu cleaned dataframe qua 4 nhom nghiep vu:

    - summary
    - authors
    - date
    - categories
    """
    if len(df) < 5:
        raise ValueError("Dataframe phai co it nhat 5 ban ghi de sinh bo test.")

    # Cycle qua 4 question types
    question_types = [
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
    ]

    target_count = min(10, len(df))
    test_set: list[dict[str, Any]] = []

    for i in range(target_count):
        row = df.iloc[i]
        q_type = question_types[i % len(question_types)]
        title = row["title"]
        paper_id = str(row["paper_id"])

        if q_type == "summary":
            question = f"What is the summary of the paper '{title}'?"
            ground_truth = first_sentence(str(row["summary"]))
        elif q_type == "authors":
            question = f"Who authored the paper '{title}'?"
            ground_truth = str(row.get("authors_joined", ""))
        elif q_type == "date":
            question = f"When was the paper '{title}' published?"
            ground_truth = str(row.get("published", ""))
        else:  # categories
            question = f"What categories belong to the paper '{title}'?"
            ground_truth = str(row.get("categories_joined", ""))

        test_set.append(
            {
                "id": f"eval_{i + 1:03d}",
                "question_type": q_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    out = Path(output_path)
    write_json(out, test_set)
    return test_set
