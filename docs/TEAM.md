# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `7GioKem10`
- **Mã Nhóm / Lớp:** `K4-L3-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3-DAY10-7GioKem10-DataPipeline`

---

## # Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Tạ Hoàng Vinh | 2A202602543 | vinh.th@example.com | Trưởng nhóm / Pipeline Integrator (`core/`, `phase1.py`, `corruption_flow.py`) | `report/2A202602543_TaHoangVinh.md` |
| 2 | Bùi Tiến Cường | 2A202602539 | cuong.bt@example.com | Data Foundation & Recovery (`crossref.py`, `cleaning.py`, raw data) | `report/2A202602539_BuiTienCuong.md` |
| 3 | Phạm Quang Huy | 2A202602900 | huy.pq@example.com | RAG & Vector Index (`retrieval/index.py`, `embeddings.py`, ChromaDB) | `report/2A202602900_PhamQuangHuy.md` |
| 4 | Ngô Đức Chung | 2A202602985 | chung.nd@example.com | Observability & Evaluation (`quality.py` GX 1.x, `testset.py`, reporting) | `report/2A202602985_NgoDucChung.md` |
| 5 | Thân Tiến Đạt | 2A202603023 | dat.tt@example.com | Corruption & Reporting Lead (`corruption.py`, `reporting.py`, reports) | `report/2A202603023_ThanTienDat.md` |

---

## # Cá nhân

### ## TaHoangVinh-2A202602543
- **Vai trò:** Trưởng nhóm & Điều phối Pipeline.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập cấu hình hệ thống `core/config.py` và đường dẫn artifacts `core/utils.py`.
  - Kết nối luồng thực thi trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`.
  - Kiểm tra tính nhất quán của các artifacts và theo dõi Contributor tracking trên GitHub nhánh `main`.
- **Điều học được / Đóng góp chính:**
  - Hiểu sâu sắc về thiết kế Idempotent Pipeline và quản lý trạng thái luồng dữ liệu đa tầng.

### ## BuiTienCuong-2A202602539
- **Vai trò:** Phụ trách Ingestion, Làm sạch & Phục hồi dữ liệu.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng module thu thập Crossref API với cơ chế Fallback offline trong `src/ingestion/crossref.py`.
  - Chuẩn hóa schema, tính toán trường `age_days` và `text_for_embedding` trong `src/ingestion/cleaning.py`.
  - Thực thi cơ chế Idempotent Repair phục hồi dữ liệu từ raw snapshot.
- **Điều học được / Đóng góp chính:**
  - Kỹ thuật truy vết nguồn gốc dữ liệu (Data Lineage) và bảo toàn raw snapshot trước khi biến đổi.

### ## PhamQuangHuy-2A202602900
- **Vai trò:** Phụ trách RAG, Vector Database & Embedding.
- **Công việc chi tiết đã hoàn thành:**
  - Quản lý mô hình embedding `sentence-transformers/all-MiniLM-L6-v2`.
  - Nạp và quản lý 3 collection riêng biệt trong ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
  - Xây dựng QA Agent truy vấn ngữ cảnh chính xác theo tài liệu.
- **Điều học được / Đóng góp chính:**
  - Cách cô lập các không gian vector để so sánh khách quan giữa dữ liệu sạch và dữ liệu bị lỗi.

### ## NgoDucChung-2A202602985
- **Vai trò:** Phụ trách Data Observability & Benchmark Evaluation.
- **Công việc chi tiết đã hoàn thành:**
  - Thiết lập Quality Gate theo chuẩn mới **Great Expectations 1.x** và giám sát Freshness SLA trong `src/observability/quality.py`.
  - Xây dựng bộ câu hỏi đánh giá chuẩn trong `src/evaluation/testset.py`.
  - Đo lường và xuất bảng đối chiếu 3 trạng thái vào `data/reports/corruption_report.md`.
- **Điều học được / Đóng góp chính:**
  - Cách thiết lập hệ thống cảnh báo sớm chặn đứng hiện tượng Silent Failure trước khi dữ liệu vào serving layer.

### ## ThanTienDat-2A202603023
- **Vai trò:** Phụ trách Synthetic Corruption & Tổng hợp Báo cáo.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng module giả lập 6 dạng độc tố dữ liệu thực tế trong `src/ingestion/corruption.py`.
  - Triển khai bộ sinh báo cáo tự động Markdown trong `src/observability/reporting.py`.
  - Tổng hợp số liệu và hoàn thiện báo cáo nhóm `report/group_report.md`.
- **Điều học được / Đóng góp chính:**
  - Hiểu rõ cơ chế gây ra lỗi Silent Failure trên các hệ thống RAG thực tế và cách viết báo cáo định lượng đối chiếu.
