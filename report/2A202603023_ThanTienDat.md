# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Thân Tiến Đạt              |
| MSSV               | 2A202603023                |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | 7GioKem10                  |
| Vai trò chính    | Corruption & Reporting Lead |
| Repository         | https://github.com/nguoibian863-ai/K4-L3-DAY10-7GioKem10-DataPipeline.git |
| Ngày hoàn thành | 2026-09-25                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------- |
| **Synthetic Corruption Suite** | `src/ingestion/corruption.py` | Cleaned DataFrame | `data/clean/papers_clean_corrupted.csv`, `corruption_log.json` | Hoàn thành |
| **Markdown Reporting Engine** | `src/observability/reporting.py` | Metrics & Quality dicts | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Hoàn thành |
| **Three-State Comparison** | `src/pipelines/corruption_flow.py` | Kết quả 3 trạng thái | Bảng so sánh đối đầu Baseline vs Corrupted vs Repaired | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Hỗ trợ tích hợp luồng Phase 2 | Tạ Hoàng Vinh / `corruption_flow.py` | Đảm bảo các file metrics JSON được load và mapping đúng vào bảng báo cáo |
| Phối hợp kiểm tra chốt chặn với Quality Lead | Ngô Đức Chung / `quality.py` | Xác nhận cả 6 lỗi tiêm vào đều kích hoạt đúng tín hiệu cảnh báo tương ứng |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Xây dựng 6 kịch bản tiêm lỗi dữ liệu | `src/ingestion/corruption.py`: `corrupt_clean_dataframe` | `data/results/corruption_log.json` (ghi nhận đủ 6 loại lỗi) | Lệnh Checkpoint 4 in ra `Corrupted 22 dòng` |
| Xây dựng engine sinh báo cáo tự động | `src/observability/reporting.py`: `generate_corruption_report` | `data/reports/corruption_report.md` | Xuất bảng đối chiếu 3 cột đầy đủ số liệu |

**Output cụ thể tạo ra:**  
Báo cáo đối chiếu 3 trạng thái tại [`data/reports/corruption_report.md`](file:///D:/LAB/Lab08/K4-L3-DAY10-7GioKem10-DataPipeline/data/reports/corruption_report.md) và tệp nhật ký độc tố dữ liệu [`data/results/corruption_log.json`](file:///D:/LAB/Lab08/K4-L3-DAY10-7GioKem10-DataPipeline/data/results/corruption_log.json) phản ánh minh bạch toàn bộ 6 hành động làm bẩn dữ liệu và sự sụt giảm chỉ số RAG.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Chứng minh bằng thực nghiệm hiểm họa Silent Failure trong các hệ thống RAG: khi dữ liệu bị lỗi, hệ thống không báo lỗi runtime mà âm thầm trả lời sai sự thật. Cần thiết kế một bộ công cụ tiêm lỗi có kiểm soát (Controlled Corruption) bao gồm các tình huống lỗi thường gặp nhất trong sản xuất, đồng thời xây dựng bộ sinh báo cáo định lượng để so sánh khách quan năng lực tự phục hồi (Idempotent Repair) của hệ thống.

### Cách triển khai
1. Trong `src/ingestion/corruption.py`:
   - Triển khai **6 kịch bản lỗi thực tế**:
     1. `drop_latest_records`: Cắt bỏ 20% bài báo mới nhất (4 records) mô phỏng lỗi mất dữ liệu tươi.
     2. `blank_summary`: Xóa trắng phần tóm tắt ở 2 dòng (`summary = ""`).
     3. `inject_noise`: Chèn chuỗi ký tự rác vô nghĩa vào 2 bản ghi.
     4. `truncate_title`: Cắt ngắn tiêu đề `< 8` ký tự ở 2 bản ghi.
     5. `stale_date`: Lùi ngày xuất bản về 365 ngày trước cho 8 bản ghi (đẩy tỷ lệ bài cũ lên 50.0%, vi phạm Freshness SLA).
     6. `duplicate_rows`: Nhân bản 2 dòng để vi phạm tính duy nhất của khóa chính `paper_id`.
   - **Tái tạo ngữ cảnh nhúng:** Duyệt qua toàn bộ DataFrame bị can thiệp và xây dựng lại chuỗi `text_for_embedding` để đảm bảo vector store phản ánh chính xác dữ liệu bẩn.
   - Ghi lại chi tiết toàn bộ các hành động vào file nhật ký `corruption_log.json`.
2. Trong `src/observability/reporting.py`:
   - Hàm `generate_phase1_report()`: Tổng hợp chi tiết thông tin nguồn Ingestion, kết quả 6 checks Great Expectations 1.x, chỉ số Freshness SLA và baseline benchmark.
   - Hàm `generate_corruption_report()`: Xây dựng bảng so sánh đối đầu 3 cột giữa **Baseline vs Corrupted vs Repaired**, phân tích cơ chế Silent Failure và chứng minh năng lực tự phục hồi nhất quán (Idempotency).

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | Cleaned DataFrame, các từ điển metrics từ Phase 1 và Phase 2 |
| **Output** | Corrupted DataFrame, file nhật ký `corruption_log.json`, báo cáo Markdown hoàn chỉnh |
| **Module phụ thuộc** | `core/config.py`, `core/utils.py` |
| **Module sử dụng output**| Script chạy demo Checkpoint 6, hồ sơ nộp bài nghiệm thu |
| **Điều kiện lỗi cần xử lý**| Thư mục đích chưa tồn tại (tự động tạo qua `ensure_parent`), thiếu metrics (hiển thị N/A) |

### Cách xác minh
```bash
python -c "from core.config import load_settings; from ingestion.corruption import corrupt_clean_dataframe; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); c=corrupt_clean_dataframe(df, s.paths.corruption_log); print(f'Tín hiệu hoàn thành: Corrupted {len(c)} dòng')"
```
- **Kết quả mong đợi:** In ra `Tín hiệu hoàn thành: Corrupted 22 dòng`.
- **Kết quả thực tế:** `Tín hiệu hoàn thành: Corrupted 22 dòng`.
- **Artifact/log:** `data/results/corruption_log.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Quyết định cách thức tiêm lỗi: Tiêm ngẫu nhiên hoàn toàn (Random noise) hay tiêm có chủ đích theo kịch bản đo lường được (Deterministic targeted corruption).
- **Các phương án đã cân nhắc:**
  1. *Phương án 1 (Random noise):* Áp dụng xác suất ngẫu nhiên làm hỏng các cell dữ liệu bất kỳ.
  2. *Phương án 2 (Targeted deterministic corruption):* Định lượng chính xác số lượng dòng cho từng loại lỗi cụ thể (ví dụ: đúng 8 dòng stale date, 4 dòng drop, 2 dòng duplicate).
- **Phương án đã chọn:** Phương án 2 (Targeted deterministic corruption).
- **Lý do:** Giúp kết quả thí nghiệm có tính tái lập tuyệt đối (Reproducibility). Mỗi lần chạy đều đảm bảo kích hoạt đúng các Expectation tương ứng của Great Expectations và Freshness SLA, cho phép đối chiếu định lượng chuẩn xác mức độ suy giảm của các chỉ số RAG.
- **Bằng chứng:** Tệp `data/results/corruption_log.json` luôn ghi nhận nhất quán 6 nhóm hành động với số lượng dòng bị ảnh hưởng được kiểm soát.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Khi tiêm lỗi trường `summary` và `title` trong DataFrame, kết quả đánh giá retrieval ban đầu không suy giảm như kỳ vọng vì Vector Store vẫn nhận chuỗi ngữ cảnh cũ.
- **Lệnh tái hiện:** Sửa DataFrame bằng `corrupted.at[idx, 'summary'] = ""` nhưng không cập nhật lại cột `text_for_embedding`.
- **Nguyên nhân gốc:** ChromaDB sử dụng trường `text_for_embedding` để tạo vector nhúng chứ không đọc trực tiếp trường `summary` đơn lẻ. Nếu chỉ sửa `summary` mà không ghép nối lại chuỗi context thì vector embedding vẫn giữ nguyên nội dung sạch ban đầu!
- **Cách xử lý:** Thêm bước số 7 trong hàm `corrupt_clean_dataframe`: duyệt qua toàn bộ DataFrame sau khi đã tiêm đủ 6 lỗi và sinh lại chuỗi `text_for_embedding` mới từ các giá trị đã bị làm bẩn.
- **Cách xác minh sau khi sửa:** Chỉ số `retrieval_hit_rate` lập tức sụt giảm rõ rệt từ 100% xuống còn 60%, phản ánh trung thực tác động của dữ liệu bẩn.
- **Điều học được:** Trong các đường ống dữ liệu học máy (ML Data Pipelines), khi thay đổi các trường dữ liệu gốc (Raw features), luôn phải tính toán lại toàn bộ các trường phái sinh (Derived features) để đảm bảo tính nhất quán của dữ liệu.

## 7. Hiểu biết về luồng end-to-end

1. **Từ Crossref đến Vector Index:** Dữ liệu thô thu thập $\rightarrow$ làm sạch và tạo `text_for_embedding` $\rightarrow$ kiểm định GX 1.x $\rightarrow$ nhúng MiniLM và lưu trữ ChromaDB.
2. **Ground-truth Doc IDs trong Evaluation:** Cung cấp tiêu chuẩn tham chiếu tuyệt đối (Absolute Truth) để đo lường xem hệ thống tìm kiếm có kéo đúng tài liệu gốc lên top-k hay không.
3. **Quality checks vs Freshness:** Quality checks bảo đảm dữ liệu đúng cấu trúc và định dạng; Freshness bảo đảm dữ liệu không bị lỗi thời theo thời gian.
4. **Tại sao giữ nguyên Test Set:** Để giữ nguyên biến số kiểm thử; chỉ có chất lượng dữ liệu nền thay đổi nhằm đo lường chính xác tác động của lỗi và sự phục hồi.
5. **Đánh giá Repair thành công:** Dựa trên việc chỉ số Hit Rate và Token F1 lấy lại mức 100% so với Baseline, đồng thời Quality Gate quay lại trạng thái `PASSED`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | ---: | ---: | ---: | :--- |
| `retrieval_hit_rate` | **100.0%** | **60.0%** | **100.0%** | Sụt giảm 40% do 4 bài báo mới bị drop |
| `mean_token_f1` | **1.0000** | **0.5741** | **1.0000** | F1 giảm sâu do summary bị xóa và chèn nhiễu ký tự |
| `judge_accuracy` | **100.0%** | **60.0%** | **100.0%** | AI Giám khảo chấm điểm phản ánh đúng thực tế lỗi |
| `mean_judge_score` | **5.00 / 5.0** | **3.20 / 5.0** | **5.00 / 5.0** | Điểm số phục hồi hoàn hảo sau khi Repair |
| Quality checks | **PASSED** | **FAILED** | **PASSED** | Chốt kiểm soát GX 1.x bắt được dữ liệu hỏng |
| Freshness status | **FRESH** | **STALE** | **FRESH** | Cảnh báo kịp thời khi tỷ lệ bài cũ vượt quá 25% |

### Kết luận từ số liệu
1. Dữ liệu bị tiêm lỗi $\rightarrow$ Quality Gate báo `FAILED` & Freshness báo `STALE` $\rightarrow$ Hit Rate giảm từ 100% xuống 60%, Token F1 giảm từ 1.0 xuống 0.5741 (Minh chứng rõ ràng hiện tượng Silent Failure).
2. Kích hoạt Idempotent Repair từ nguồn Raw $\rightarrow$ Quality Gate báo `PASSED` & Freshness báo `FRESH` $\rightarrow$ Toàn bộ chỉ số RAG lấy lại 100% phong độ ban đầu.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Bản chất của Silent Failure:** AI Agent vẫn trả lời rất trôi chảy dù dữ liệu đầu vào đã bị hỏng nặng; nếu không có Data Quality Gate, người dùng sẽ là nạn nhân của thông tin sai lệch.
2. **Kỹ thuật báo cáo định lượng đối chiếu:** Học được cách thiết kế bảng so sánh 3 trạng thái giúp các bên liên quan nhìn thấy ngay giá trị của Data Observability.
3. **Derived Features Consistency:** Nhận thức rõ ràng tầm quan trọng của việc đồng bộ hóa dữ liệu phái sinh (`text_for_embedding`) mỗi khi dữ liệu cơ sở thay đổi.

### Nếu có thêm thời gian
Tự động hóa việc xuất biểu đồ trực quan (Charts/Visualizations) dưới dạng SVG hoặc PNG nhúng trực tiếp vào báo cáo markdown để tăng tính sinh động cho bài thuyết trình demo.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Thân Tiến Đạt  
**Ngày xác nhận:** 2026-09-25  
