from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import pandas as pd

from core.utils import ensure_parent, normalize_whitespace, write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate 6 dang data corruption thuc te:

    1. Drop 20% latest records (mat du lieu moi).
    2. Blank summary o mot so dong (loi cao du lieu rong).
    3. Inject noise vao summary (nhiễu ký tự).
    4. Truncate title < 8 ky tu.
    5. Stale date: lui published date ve 365 ngay truoc (vi pham Freshness SLA).
    6. Duplicate rows (trung lap paper_id).
    7. Rebuild text_for_embedding va ghi log.
    """
    corrupted = df.copy()
    total_initial = len(corrupted)
    log_entries: list[dict[str, Any]] = []

    # 1. Drop latest 20% records (since df is sorted by published descending)
    drop_count = max(1, int(total_initial * 0.2))
    dropped_ids = corrupted.iloc[:drop_count]["paper_id"].tolist()
    corrupted = corrupted.iloc[drop_count:].copy().reset_index(drop=True)
    log_entries.append(
        {
            "corruption_type": "drop_latest_records",
            "count": drop_count,
            "description": f"Dropped {drop_count} latest records ({dropped_ids})",
        }
    )

    # 2. Blank summary on 2 records
    blank_indices = [0, 1] if len(corrupted) >= 2 else [0]
    for idx in blank_indices:
        corrupted.at[idx, "summary"] = ""
        corrupted.at[idx, "summary_chars"] = 0
    log_entries.append(
        {
            "corruption_type": "blank_summary",
            "count": len(blank_indices),
            "description": f"Blanked summary for paper_ids: {[corrupted.at[i, 'paper_id'] for i in blank_indices]}",
        }
    )

    # 3. Inject noise into summary on next 2 records
    noise_indices = [2, 3] if len(corrupted) >= 4 else []
    for idx in noise_indices:
        original = corrupted.at[idx, "summary"]
        noisy = f"### CORRUPTED NOISE !@#$%^&*() {original[:30]} RANDOM_GARBAGE_TOKEN ###"
        corrupted.at[idx, "summary"] = noisy
        corrupted.at[idx, "summary_chars"] = len(noisy)
    if noise_indices:
        log_entries.append(
            {
                "corruption_type": "inject_noise",
                "count": len(noise_indices),
                "description": f"Injected noise for paper_ids: {[corrupted.at[i, 'paper_id'] for i in noise_indices]}",
            }
        )

    # 4. Truncate title < 8 characters on next 2 records
    trunc_indices = [4, 5] if len(corrupted) >= 6 else []
    for idx in trunc_indices:
        corrupted.at[idx, "title"] = corrupted.at[idx, "title"][:5]
    if trunc_indices:
        log_entries.append(
            {
                "corruption_type": "truncate_title",
                "count": len(trunc_indices),
                "description": f"Truncated titles to <8 chars for indices: {trunc_indices}",
            }
        )

    # 5. Stale date: shift publication date back by 365 days for 8 records (> 25% stale ratio)
    stale_indices = list(range(min(8, len(corrupted))))
    today = datetime.now(timezone.utc).date()
    for idx in stale_indices:
        orig_pub = str(corrupted.at[idx, "published"])
        try:
            pub_d = datetime.fromisoformat(orig_pub[:10]).date()
        except Exception:
            pub_d = today
        stale_d = pub_d - timedelta(days=365)
        stale_str = stale_d.isoformat()
        corrupted.at[idx, "published"] = stale_str
        corrupted.at[idx, "age_days"] = max(0, (today - stale_d).days)
    log_entries.append(
        {
            "corruption_type": "stale_date",
            "count": len(stale_indices),
            "description": f"Shifted published date back 365 days for {len(stale_indices)} rows to violate Freshness SLA",
        }
    )

    # 6. Duplicate rows: pick 2 rows and append to create duplicate paper_ids
    dup_rows = corrupted.iloc[:2].copy()
    corrupted = pd.concat([corrupted, dup_rows], ignore_index=True)
    log_entries.append(
        {
            "corruption_type": "duplicate_rows",
            "count": len(dup_rows),
            "description": f"Duplicated {len(dup_rows)} rows to violate unique paper_id expectation",
        }
    )

    # 7. Rebuild text_for_embedding for all rows
    updated_embeddings = []
    for _, row in corrupted.iterrows():
        title = normalize_whitespace(str(row["title"]))
        authors = str(row.get("authors_joined", ""))
        published = str(row.get("published", ""))
        categories = str(row.get("categories_joined", ""))
        summary = normalize_whitespace(str(row.get("summary", "")))
        text = (
            f"Title: {title}\n"
            f"Authors: {authors}\n"
            f"Published: {published}\n"
            f"Categories: {categories}\n"
            f"Summary: {summary}"
        )
        updated_embeddings.append(text)
    corrupted["text_for_embedding"] = updated_embeddings

    # Write log
    out = Path(output_log_path)
    ensure_parent(out)
    write_json(
        out,
        {
            "initial_rows": total_initial,
            "corrupted_rows": len(corrupted),
            "actions": log_entries,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return corrupted
