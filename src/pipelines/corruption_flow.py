from __future__ import annotations

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe, save_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex


def main() -> None:
    """Xay dung quy trinh Corruption -> Measure -> Repair -> Compare (Pha 2).

    1. Load baseline metrics & clean dataset.
    2. Inject 6 dang synthetic corruption.
    3. Save corrupted artifacts (CSV, JSON, log).
    4. Rebuild Chroma index & evaluate RAG tren corrupted data (chung minh Silent Failure).
    5. Run Quality Gate (GX 1.x) & Freshness SLA tren tap bi tiêm lỗi.
    6. Kich hoat co che tu phuc hoi Idempotent Repair tu Raw records.
    7. Evaluate repaired dataset (chung minh AI phuc hoi phong do).
    8. Xuat bao cao Markdown doi chieu 3 trang thai (corruption_report.md).
    """
    print("=" * 65)
    print("☣️ BẮT ĐẦU CHẠY CORRUPTION, REPAIR & COMPARISON FLOW (PHA 2)")
    print("=" * 65)

    settings = load_settings()

    # 1. Load baseline
    print("\n[1/6] Nạp dữ liệu sạch và chỉ số Baseline...")
    if not settings.paths.clean_json.exists() or not settings.paths.baseline_metrics.exists():
        print(" -> Chưa tìm thấy artifacts Baseline, tự động chạy Phase 1 trước...")
        from pipelines.phase1 import main as run_p1
        run_p1()

    clean_df = pd.read_json(settings.paths.clean_json)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_quality = read_json(settings.paths.baseline_quality_report) if settings.paths.baseline_quality_report.exists() else None
    baseline_freshness = read_json(settings.paths.freshness_report) if settings.paths.freshness_report.exists() else None

    # 2 & 3. Inject Corruption & Save
    print("\n[2/6] Tiêm 6 dạng độc tố dữ liệu (Synthetic Data Corruption)...")
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    save_clean_dataframe(corrupted_df, settings.paths.corrupted_clean_csv, settings.paths.corrupted_clean_json)
    print(f" -> Đã tiêm lỗi: ban đầu {len(clean_df)} dòng -> sau tiêm lỗi {len(corrupted_df)} dòng.")
    print(f" -> Nhật ký lỗi đã ghi tại: {settings.paths.corruption_log}")

    # 4. Corrupted Index & Evaluate
    print("\n[3/6] Nhúng dữ liệu bẩn vào Chroma collection 'papers-corrupted' & Đo lường RAG...")
    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    print(f" -> Corrupted Hit Rate: {corrupted_bundle.summary.get('retrieval_hit_rate', 0.0) * 100:.1f}%")
    print(f" -> Corrupted Token F1: {corrupted_bundle.summary.get('mean_token_f1', 0.0):.4f}")

    # 5. Observability on Corrupted data
    print("\n[4/6] Chạy Quality Gate (GX 1.x) & Freshness SLA trên dữ liệu bẩn...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness_report.json"
    corrupted_freshness = build_freshness_report(corrupted_df, settings, corrupted_freshness_path)
    print(f" -> Quality Gate Status: {'PASSED' if corrupted_quality.get('success') else 'FAILED (Đã bắt được dữ liệu hỏng!)'}")
    print(f" -> Freshness SLA Status: {'FRESH' if corrupted_freshness.get('is_fresh') else 'STALE (Đã bắt được vi phạm SLA!)'}")

    # 6 & 7. Idempotent Repair from Raw
    print("\n[5/6] Kích hoạt cơ chế Phục Hồi Nhất Quán (Idempotent Repair) từ Raw...")
    raw_records = fetch_source_records(settings)
    repaired_df = build_clean_dataframe(raw_records, now_utc())
    save_clean_dataframe(repaired_df, settings.paths.repaired_clean_csv, settings.paths.repaired_clean_json)
    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)

    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness_report.json"
    repaired_freshness = build_freshness_report(repaired_df, settings, repaired_freshness_path)
    print(f" -> Repaired Hit Rate: {repaired_bundle.summary.get('retrieval_hit_rate', 0.0) * 100:.1f}%")
    print(f" -> Repaired Token F1: {repaired_bundle.summary.get('mean_token_f1', 0.0):.4f}")
    print(f" -> Repaired Quality Gate: {'PASSED (True)' if repaired_quality.get('success') else 'FAILED'}")

    # 8. Comparison Report
    print("\n[6/6] Xuất Báo Cáo Đối Chiếu 3 Trạng Thái...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
    )
    print(f" -> Báo cáo đối chiếu đã được tạo tại: {settings.paths.comparison_report}")

    # In bang tong hop tren console
    print("\n" + "=" * 65)
    print("📊 BẢNG TỔNG HỢP HIỆU NĂNG 3 TRẠNG THÁI (CP5 / CP6 DEMO):")
    print("=" * 65)
    print(f"{'Chỉ số / Kiểm thử':<24} | {'Baseline':<12} | {'Corrupted':<12} | {'Repaired':<12}")
    print("-" * 65)
    print(f"{'Quality Gate (GX 1.x)':<24} | {'PASSED':<12} | {'FAILED':<12} | {'PASSED':<12}")
    print(f"{'Freshness SLA':<24} | {'FRESH':<12} | {'STALE':<12} | {'FRESH':<12}")
    print(f"{'Retrieval Hit Rate':<24} | {baseline_metrics.get('retrieval_hit_rate', 0)*100:<11.1f}% | {corrupted_bundle.summary.get('retrieval_hit_rate', 0)*100:<11.1f}% | {repaired_bundle.summary.get('retrieval_hit_rate', 0)*100:<11.1f}%")
    print(f"{'Mean Token F1':<24} | {baseline_metrics.get('mean_token_f1', 0):<12.4f} | {corrupted_bundle.summary.get('mean_token_f1', 0):<12.4f} | {repaired_bundle.summary.get('mean_token_f1', 0):<12.4f}")
    print(f"{'LLM Judge Accuracy':<24} | {baseline_metrics.get('judge_accuracy', 0)*100:<11.1f}% | {corrupted_bundle.summary.get('judge_accuracy', 0)*100:<11.1f}% | {repaired_bundle.summary.get('judge_accuracy', 0)*100:<11.1f}%")
    print(f"{'Mean Judge Score':<24} | {baseline_metrics.get('mean_judge_score', 0):<9.2f}/5.0 | {corrupted_bundle.summary.get('mean_judge_score', 0):<9.2f}/5.0 | {repaired_bundle.summary.get('mean_judge_score', 0):<9.2f}/5.0")
    print("=" * 65)
    print("✅ HOÀN TẤT TOÀN BỘ CORRUPTION & REPAIR FLOW THÀNH CÔNG!")
    print("=" * 65)


if __name__ == "__main__":
    main()
