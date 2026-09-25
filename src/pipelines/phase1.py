from __future__ import annotations

from core.config import load_settings
from core.utils import now_utc
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe, save_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Xay dung baseline pipeline end-to-end (Pha 1).

    1. Load settings.
    2. Fetch hoac load raw records tu Crossref.
    3. Clean data & tinh age_days.
    4. Save clean CSV & JSON.
    5. Build Chroma baseline vector collection.
    6. Tao evaluation test set (10 cau).
    7. Evaluate RAG tren tap test.
    8. Run quality checks (GX 1.x) va freshness report.
    9. Tao markdown report (phase1_report.md).
    """
    print("=" * 60)
    print("🚀 BẮT ĐẦU CHẠY BASELINE PIPELINE (PHA 1)")
    print("=" * 60)

    # 1. Load settings
    settings = load_settings()

    # 2. Ingestion
    print("\n[1/6] Đang thu thập và nạp dữ liệu thô...")
    records = fetch_source_records(settings)
    print(f" -> Đã thu thập {len(records)} bản ghi từ Crossref.")

    # 3 & 4. Cleaning
    print("\n[2/6] Đang làm sạch và chuẩn hóa dữ liệu...")
    df = build_clean_dataframe(records, now_utc())
    save_clean_dataframe(df, settings.paths.clean_csv, settings.paths.clean_json)
    print(f" -> Đã xuất dữ liệu sạch ({len(df)} dòng) ra:")
    print(f"    - {settings.paths.clean_csv}")
    print(f"    - {settings.paths.clean_json}")

    # 5. Chroma Vector Indexing
    print("\n[3/6] Đang nhúng vector và khởi tạo ChromaDB collection 'papers-baseline'...")
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    print(" -> Hoàn tất khởi tạo ChromaDB index.")

    # 6. Evaluation test set
    print("\n[4/6] Đang chuẩn bị tập dữ liệu đánh giá (Benchmark Test Set)...")
    build_test_set(df, settings.paths.eval_testset)
    print(f" -> Đã sinh bộ test set tại: {settings.paths.eval_testset}")

    # 7. Evaluate
    print("\n[5/6] Đang đánh giá chỉ số Baseline RAG (Hit Rate, Token F1, LLM Judge)...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    print(f" -> Retrieval Hit Rate: {bundle.summary.get('retrieval_hit_rate', 0.0) * 100:.1f}%")
    print(f" -> Mean Token F1:     {bundle.summary.get('mean_token_f1', 0.0):.4f}")
    print(f" -> LLM Judge Accuracy:{bundle.summary.get('judge_accuracy', 0.0) * 100:.1f}%")
    print(f" -> Mean Judge Score:  {bundle.summary.get('mean_judge_score', 0.0):.2f}/5.0")

    # 8. Observability & Quality
    print("\n[6/6] Đang kiểm định chất lượng (GX 1.x) và đo độ tươi (Freshness SLA)...")
    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    print(f" -> Quality Gate Status: {'PASSED (True)' if quality.get('success') else 'FAILED (False)'}")
    print(f" -> Freshness SLA Status: {'FRESH (True)' if freshness.get('is_fresh') else 'STALE (False)'} (Stale: {freshness.get('stale_ratio', 0)*100:.1f}%)")

    # 9. Generate Report
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "total_records": len(df),
    }
    generate_phase1_report(settings.paths.baseline_report, source_summary, bundle.summary, quality, freshness)
    print(f"\n -> Báo cáo Phase 1 đã được tạo tại: {settings.paths.baseline_report}")
    print("\n" + "=" * 60)
    print("✅ HOÀN TẤT BASELINE PIPELINE THÀNH CÔNG!")
    print("=" * 60)


if __name__ == "__main__":
    main()
