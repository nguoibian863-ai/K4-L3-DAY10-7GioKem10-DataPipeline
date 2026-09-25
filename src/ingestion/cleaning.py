from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
import re
from typing import Any

import pandas as pd

from core.utils import ensure_parent, normalize_whitespace
from ingestion.crossref import PaperRecord


def _parse_date(date_str: str) -> date | None:
    if not date_str:
        return None
    cleaned = date_str.strip()[:10]
    try:
        return datetime.fromisoformat(cleaned).date()
    except Exception:
        pass
    parts = re.split(r"[-/.]", cleaned)
    if len(parts) == 3:
        try:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception:
            return None
    return None


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime | date | None = None) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed.

    Pseudo-code:
    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding
    5. Drop duplicates va filter row xau.
    6. Sort dataframe va return.
    """
    if run_date is None:
        target_date = datetime.now(timezone.utc).date()
    elif isinstance(run_date, datetime):
        target_date = run_date.date()
    else:
        target_date = run_date

    rows: list[dict[str, Any]] = []

    for r in records:
        paper_id = normalize_whitespace(r.paper_id)
        title = normalize_whitespace(r.title)
        summary = normalize_whitespace(r.summary)

        # Skip rows without paper_id or title
        if not paper_id or not title:
            continue

        authors = [normalize_whitespace(a) for a in r.authors if normalize_whitespace(a)]
        categories = [normalize_whitespace(c) for c in r.categories if normalize_whitespace(c)]
        primary_category = normalize_whitespace(r.primary_category) or (categories[0] if categories else "General")

        published = r.published.strip()
        pub_date = _parse_date(published)
        if pub_date:
            age_days = max(0, (target_date - pub_date).days)
        else:
            age_days = 0

        updated = r.updated.strip() if r.updated else published

        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)
        summary_chars = len(summary)

        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Published: {published}\n"
            f"Categories: {categories_joined}\n"
            f"Summary: {summary}"
        )

        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "published": published,
                "updated": updated,
                "abs_url": r.abs_url,
                "pdf_url": r.pdf_url,
                "comment": r.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "paper_id",
                "title",
                "summary",
                "authors",
                "categories",
                "primary_category",
                "published",
                "updated",
                "abs_url",
                "pdf_url",
                "comment",
                "authors_joined",
                "categories_joined",
                "summary_chars",
                "age_days",
                "text_for_embedding",
            ]
        )

    # Deduplicate by paper_id
    df = df.drop_duplicates(subset=["paper_id"], keep="first")

    # Sort descending by published then paper_id
    df = df.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df


def save_clean_dataframe(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    """Luu dataframe vao ca hai dinh dang CSV va JSON."""
    ensure_parent(csv_path)
    ensure_parent(json_path)
    df.to_csv(csv_path, index=False)
    df.to_json(json_path, orient="records", indent=2, force_ascii=False)
