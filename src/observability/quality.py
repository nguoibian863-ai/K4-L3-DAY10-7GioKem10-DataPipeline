from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import great_expectations as gx
import great_expectations.expectations as gxe
import pandas as pd

from core.config import Settings
from core.utils import now_utc, write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Tao bo data quality checks voi Great Expectations 1.x ephemeral context.

    Pseudo-code:
    1. Check row count (5 den 5000).
    2. Check `paper_id` not null va unique.
    3. Check `title` va `text_for_embedding` not null.
    4. Check do dai `summary` (>= 30 ky tu).
    5. Ghi ket qua JSON vao `data/quality/`.
    """
    context = gx.get_context(mode="ephemeral")
    source_name = f"papers_source_{report_name}"
    asset_name = f"papers_asset_{report_name}"
    batch_def_name = f"papers_batch_{report_name}"
    suite_name = f"papers_suite_{report_name}"

    data_source = context.data_sources.add_pandas(name=source_name)
    data_asset = data_source.add_dataframe_asset(name=asset_name)
    batch_def = data_asset.add_batch_definition_whole_dataframe(batch_def_name)
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    suite = gx.ExpectationSuite(name=suite_name)
    suite.add_expectation(gxe.ExpectTableRowCountToBeBetween(min_value=5, max_value=5000))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValuesToBeUnique(column="paper_id"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="title"))
    suite.add_expectation(gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"))
    suite.add_expectation(gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=30))

    context.suites.add(suite)
    validation_result = batch.validate(suite)

    result_dict = validation_result.to_json_dict()
    result_dict["report_name"] = report_name
    result_dict["evaluated_at"] = now_utc().isoformat()

    if report_name == "baseline":
        out_path = settings.paths.baseline_quality_report
    elif report_name == "corrupted":
        out_path = settings.paths.corrupted_quality_report
    else:
        out_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"

    write_json(out_path, result_dict)
    return result_dict


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path | None = None) -> dict[str, Any]:
    """Tong hop freshness report va do luong ty le bai bao qua han (SLA: stale <= 25%).

    Pseudo-code:
    1. Tim latest va oldest published date.
    2. Dem so dong stale (age_days > freshness_threshold_days).
    3. Tao payload:
       - latest_published
       - oldest_published
       - stale_rows
       - total_rows
       - is_fresh
    4. Ghi JSON report.
    """
    total_rows = len(df)
    if total_rows == 0:
        payload = {
            "latest_published": "",
            "oldest_published": "",
            "threshold_days": settings.freshness_threshold_days,
            "max_stale_ratio_allowed": 0.25,
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "is_fresh": False,
            "generated_at": now_utc().isoformat(),
        }
    else:
        pub_series = df["published"].dropna().astype(str) if "published" in df.columns else pd.Series(dtype=str)
        latest_published = str(pub_series.max()) if not pub_series.empty else ""
        oldest_published = str(pub_series.min()) if not pub_series.empty else ""

        if "age_days" in df.columns:
            stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
        else:
            today = datetime.now(timezone.utc).date()
            age_days_list = []
            for p in pub_series:
                try:
                    d = datetime.fromisoformat(p[:10]).date()
                    age_days_list.append((today - d).days)
                except Exception:
                    age_days_list.append(0)
            stale_rows = int(sum(1 for a in age_days_list if a > settings.freshness_threshold_days))

        stale_ratio = float(stale_rows / total_rows)
        is_fresh = bool(stale_ratio <= 0.25)

        payload = {
            "latest_published": latest_published,
            "oldest_published": oldest_published,
            "threshold_days": settings.freshness_threshold_days,
            "max_stale_ratio_allowed": 0.25,
            "stale_rows": stale_rows,
            "total_rows": total_rows,
            "stale_ratio": round(stale_ratio, 4),
            "is_fresh": is_fresh,
            "generated_at": now_utc().isoformat(),
        }

    target_path = report_path or settings.paths.freshness_report
    write_json(target_path, payload)
    return payload
