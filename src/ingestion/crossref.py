from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any
import requests

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_abstract(raw: str) -> str:
    text = re.sub(r"<[^>]+>", " ", raw or "")
    return normalize_whitespace(text)


def _parse_date_parts(parts: list[Any]) -> str:
    if not parts:
        return ""
    if len(parts) >= 3:
        return f"{int(parts[0]):04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    if len(parts) == 2:
        return f"{int(parts[0]):04d}-{int(parts[1]):02d}-01"
    if len(parts) == 1:
        return f"{int(parts[0]):04d}-01-01"
    return ""


def parse_crossref_payload(payload: dict[str, Any]) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    items = payload.get("message", {}).get("items", []) if "message" in payload else payload.get("items", [])
    records: list[PaperRecord] = []

    for item in items:
        paper_id = str(item.get("DOI", "")).strip()
        raw_title = item.get("title", "")
        if isinstance(raw_title, list):
            title = normalize_whitespace(raw_title[0]) if raw_title else ""
        else:
            title = normalize_whitespace(str(raw_title))

        raw_abstract = item.get("abstract", "")
        summary = _clean_abstract(raw_abstract)
        if not summary and "summary" in item:
            summary = normalize_whitespace(str(item["summary"]))

        authors: list[str] = []
        for author in item.get("author", []):
            if isinstance(author, dict):
                given = author.get("given", "").strip()
                family = author.get("family", "").strip()
                full = f"{given} {family}".strip() or author.get("name", "").strip()
                if full:
                    authors.append(full)
            elif isinstance(author, str) and author.strip():
                authors.append(author.strip())

        categories: list[str] = []
        raw_subjects = item.get("subject", []) or item.get("categories", [])
        for subject in raw_subjects:
            if isinstance(subject, str) and subject.strip():
                categories.append(subject.strip())

        primary_category = categories[0] if categories else "General"

        published = ""
        pub_info = item.get("published", {})
        if isinstance(pub_info, dict) and "date-parts" in pub_info and pub_info["date-parts"]:
            published = _parse_date_parts(pub_info["date-parts"][0])
        if not published:
            created = item.get("created", {}).get("date-time", "")
            if created and len(created) >= 10:
                published = created[:10]
            elif isinstance(item.get("published"), str):
                published = item["published"]

        updated = published
        abs_url = item.get("URL", f"https://doi.org/{paper_id}" if paper_id else "")
        pdf_url = item.get("pdf_url") or abs_url
        comment = item.get("comment", f"Crossref record {paper_id}")

        if paper_id and title:
            records.append(
                PaperRecord(
                    paper_id=paper_id,
                    title=title,
                    summary=summary,
                    authors=authors,
                    categories=categories,
                    primary_category=primary_category,
                    published=published,
                    updated=updated,
                    abs_url=abs_url,
                    pdf_url=pdf_url,
                    comment=comment,
                )
            )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi source API hoac dung snapshot offline, luu raw response, parse thanh records."""
    if settings.refresh_source:
        try:
            url = "https://api.crossref.org/works"
            params = {
                "query": settings.source_query,
                "filter": settings.source_filter,
                "rows": settings.max_results,
            }
            headers = {"User-Agent": "DataPipelineLab/1.0 (mailto:lab@example.com)"}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                payload = response.json()
                write_json(settings.paths.raw_api_response, payload)
                records = parse_crossref_payload(payload)
                write_json(settings.paths.raw_records_json, [asdict(r) for r in records])
                return records
        except Exception:
            pass

    # Fallback to local snapshot
    if settings.paths.raw_records_json.exists():
        records = load_raw_records(settings.paths.raw_records_json)
        if records:
            return records

    if settings.paths.raw_api_response.exists():
        payload = read_json(settings.paths.raw_api_response)
        records = parse_crossref_payload(payload)
        write_json(settings.paths.raw_records_json, [asdict(r) for r in records])
        return records

    raise FileNotFoundError("Khong tim thay ban ghi raw nao tai data/raw/.")


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh list PaperRecord."""
    data = read_json(path)
    if isinstance(data, list):
        records: list[PaperRecord] = []
        for item in data:
            records.append(
                PaperRecord(
                    paper_id=str(item.get("paper_id", "")),
                    title=str(item.get("title", "")),
                    summary=str(item.get("summary", "")),
                    authors=list(item.get("authors", [])),
                    categories=list(item.get("categories", [])),
                    primary_category=str(item.get("primary_category", "")),
                    published=str(item.get("published", "")),
                    updated=str(item.get("updated", "")),
                    abs_url=str(item.get("abs_url", "")),
                    pdf_url=str(item.get("pdf_url", "")),
                    comment=str(item.get("comment", "")),
                )
            )
        return records
    if isinstance(data, dict):
        return parse_crossref_payload(data)
    return []
