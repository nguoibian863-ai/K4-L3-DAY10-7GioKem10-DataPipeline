# Phase 1 Baseline Report: Data Pipeline & Data Observability for RAG

**Thời gian tạo:** 2026-09-25T08:59:46.550757+00:00  
**Trạng thái Quality Gate:** PASSED (Thành công)  
**Trạng thái Freshness SLA:** FRESH (Đạt SLA)  

---

## 1. Tổng Quan Nguồn Dữ Liệu (Ingestion Summary)
- **Nguồn dữ liệu:** Crossref REST API
- **Truy vấn (Query):** `agentic retrieval augmented generation large language model`
- **Bộ lọc (Filter):** `from-pub-date:2026-03-29,has-abstract:true`
- **Tổng số bài báo thu thập:** 24
- **Tập tin làm sạch:** `data/clean/papers_clean.csv` & `data/clean/papers_clean.json`

---

## 2. Kiểm Soát Chất Lượng Dữ Liệu (Great Expectations 1.x)
- **Kết quả tổng thể:** `success = True`
- **Số lượng Expectations đánh giá:** 6
- **Số lượng Expectations thành công:** 6
- **Tỷ lệ thành công:** 100.0%

### Danh sách Hàng Rào Kiểm Định:
| Kỳ vọng (Expectation) | Cột kiểm tra | Kết quả | Ghi chú |
| :--- | :--- | :--- | :--- |
| `ExpectTableRowCountToBeBetween` | Toàn bảng | PASSED | Số dòng nằm trong ngưỡng [5, 5000] |
| `ExpectColumnValuesToNotBeNull` | `paper_id` | PASSED | Khóa định danh không được null |
| `ExpectColumnValuesToBeUnique` | `paper_id` | PASSED | Không có bản ghi trùng lặp |
| `ExpectColumnValuesToNotBeNull` | `title` | PASSED | Tiêu đề bài báo không được null |
| `ExpectColumnValuesToNotBeNull` | `text_for_embedding` | PASSED | Chuỗi ngữ cảnh vector không được null |
| `ExpectColumnValueLengthsToBeBetween` | `summary` | PASSED | Độ dài tóm tắt >= 30 ký tự |

---

## 3. Giám Sát Độ Tươi Mới (Freshness SLA Monitoring)
- **Bài báo mới nhất:** 2026-07-22
- **Bài báo cũ nhất:** 2026-03-28
- **Ngưỡng quá hạn SLA:** 180 ngày
- **Số lượng bài báo quá hạn (>180 ngày):** 1 / 24
- **Tỷ lệ quá hạn thực tế:** 4.17%
- **Ngưỡng cho phép tối đa:** 25%
- **Đánh giá:** ĐẠT YÊU CẦU ĐỘ TƯƠI (is_fresh = True)

---

## 4. Chỉ Số Đánh Giá Baseline RAG (Benchmark Metrics)
- **Kích thước tập kiểm thử (Test Set):** 10 câu hỏi
- **Retrieval Hit Rate:** 100.0%
- **Mean Token F1:** 1.0000
- **LLM Judge Accuracy:** 100.0%
- **Mean Judge Score:** 5.00 / 5.0
