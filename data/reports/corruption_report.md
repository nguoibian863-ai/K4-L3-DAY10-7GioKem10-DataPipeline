# Báo Cáo Đối Chiếu 3 Trạng Thái: Data Observability & Idempotent Repair

**Thời gian xuất báo cáo:** 2026-09-25T08:22:38.129750+00:00  
**Nhiệm vụ:** Chứng minh hiểm họa Silent Failure khi dữ liệu bị lỗi, năng lực phát hiện của GX 1.x & Freshness Gate, và khả năng tự phục hồi sạch sẽ (Idempotent Self-Healing).

---

## 1. Bảng Đối Chiếu Định Lượng 3 Trạng Thái (Quantitative Comparison)

| Chỉ số / Kiểm thử | Baseline (Pha 1) | Corrupted (Pha 2 - Tiêm Lỗi) | Repaired (Sau Phục Hồi) | Kết Luận & Xu Hướng |
| :--- | :--- | :--- | :--- | :--- |
| **Quality Gate (GX 1.x)** | **PASSED (True)** | <mark>**FAILED (False)**</mark> | **PASSED (True)** | Gate bắt lỗi thành công, phục hồi 100% |
| **Freshness SLA (180d)** | **FRESH (True)** | <mark>**STALE (False)**</mark> | **FRESH (True)** | Phát hiện vi phạm hạn dùng dữ liệu |
| **Tỷ lệ bài cũ (Stale %)** | **4.2%** | **50.0%** (vượt 25%) | **4.2%** | Trở về ngưỡng an toàn (<25%) |
| **Retrieval Hit Rate** | **100.0%** | <mark>**60.0%**</mark> (sụt giảm) | **100.0%** | Khôi phục độ phủ tìm kiếm |
| **Mean Token F1** | **1.0000** | <mark>**0.5741**</mark> (sụt giảm) | **1.0000** | Độ chính xác câu chữ trở lại mức gốc |
| **LLM Judge Accuracy** | **100.0%** | <mark>**60.0%**</mark> | **100.0%** | AI giám khảo chấm điểm phục hồi |
| **Mean Judge Score** | **5.00 / 5.0** | <mark>**3.20 / 5.0**</mark> | **5.00 / 5.0** | Lấy lại phong độ toàn diện |

---

## 2. Phân Tích Hiểm Họa Silent Failure
Khi hệ thống bị tiêm 6 kịch bản lỗi:
1. **Drop latest records (Mất 20% bản ghi mới):** Khiến Agent hoàn toàn không tìm thấy tài liệu mới xuất bản. Hit Rate sụt giảm trực tiếp.
2. **Blank summary (Xóa rỗng tóm tắt):** Thiếu hụt thông tin trầm trọng, khiến nội dung trả về bị rỗng hoặc ảo giác.
3. **Inject noise (Chèn ký tự rác):** Làm lệch vector embedding không gian đa chiều, dẫn đến việc bộ tìm kiếm kéo về những đoạn context sai lệch.
4. **Truncate title (Cắt cụt tiêu đề):** Phá vỡ cơ chế tìm kiếm chính xác theo tiêu đề bài báo.
5. **Stale date (Làm cũ ngày xuất bản):** Gây nhiễu thời gian, vi phạm Freshness SLA.
6. **Duplicate rows (Nhân bản dữ liệu):** Làm loãng vector store và vi phạm tính duy nhất.

**Bản chất của Silent Failure:**  
Mặc dù dữ liệu bị hỏng nặng, hệ thống AI Agent **không hề phát sinh exception runtime** hay dừng chương trình. Agent vẫn trả lời rất tự tin nhưng nội dung hoàn toàn sai lệch hoặc bịa đặt. Đây chính là lý do vì sao Data Observability Gate là lớp phòng thủ sinh tử cho sản xuất.

---

## 3. Vai Trò Của Data Observability Gate (GX 1.x & Freshness SLA)
- **Great Expectations 1.x:** Đã gióng chuông cảnh báo đỏ ngay lập tức (`success = False`):
  - Bắt lỗi `ExpectColumnValuesToBeUnique`: Phát hiện trùng lặp khóa chính `paper_id`.
  - Bắt lỗi `ExpectColumnValueLengthsToBeBetween`: Phát hiện `summary` bị xóa rỗng dưới 30 ký tự.
- **Freshness SLA Monitor:** Phát hiện tỷ lệ bài báo cũ vượt quá ngưỡng 25% cho phép, bật cờ `is_fresh = False`.

---

## 4. Cơ Chế Tự Phục Hồi Nhất Quán (Idempotent Repair)
- Hệ thống kích hoạt cơ chế khôi phục từ bản sao lưu thô nguồn cội (`data/raw/crossref_records.json`).
- Dữ liệu được làm sạch lại, kiểm định lại qua Great Expectations và nạp lại vào ChromaDB collection `papers-repaired`.
- **Tính Idempotent (Bất biến/Nhất quán):** Bất kể quy trình chạy lại bao nhiêu lần, kết quả thu được luôn sạch sẽ, đồng nhất, và đưa toàn bộ chỉ số RAG trở lại chính xác mức Baseline ban đầu.
