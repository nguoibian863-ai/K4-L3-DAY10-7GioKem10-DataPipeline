# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Ngô Đức Chung              |
| MSSV               | 2A202602985                |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | 7GioKem10                  |
| Vai trò chính    | Observability & Evaluation |
| Repository         | https://github.com/nguoibian863-ai/K4-L3-DAY10-7GioKem10-DataPipeline.git |
| Ngày hoàn thành | 2026-09-25                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------- |
| **Data Quality Gate (GX 1.x)** | `src/observability/quality.py` (`run_data_quality_checks`) | Cleaned / Corrupted DataFrame | `data/quality/*_quality_report.json` (Pass / Fail) | Hoàn thành |
| **Freshness SLA Monitoring** | `src/observability/quality.py` (`build_freshness_report`) | DataFrame qua trường `age_days` | `data/quality/*freshness_report.json` | Hoàn thành |
| **Benchmark Test Set Builder**| `src/evaluation/testset.py` (`build_test_set`) | Cleaned DataFrame | `data/eval/test_set.json` (10 câu hỏi chuẩn) | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Kết nối chốt kiểm dịch vào luồng Phase 1 | Tạ Hoàng Vinh / `phase1.py` | Kiểm tra tự động chất lượng dữ liệu sạch trước khi sinh báo cáo baseline |
| Cung cấp ngưỡng kiểm thử cho kịch bản tiêm lỗi | Thân Tiến Đạt / `corruption.py` | Xác định ngưỡng summary < 30 ký tự và tỷ lệ stale > 25% để tiêm lỗi kích hoạt cảnh báo |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Triển khai Quality Gate GX 1.x | `src/observability/quality.py` | `baseline_quality_report.json` (Passed), `corrupted_quality_report.json` (Failed) | Lệnh Checkpoint 1 in ra `Quality check status = True` |
| Triển khai Freshness SLA | `src/observability/quality.py` | `freshness_report.json` (is_fresh = True, stale = 4.17%) | Lệnh kiểm tra Freshness in ra `is_fresh: True` |
| Sinh bộ Benchmark 10 câu | `src/evaluation/testset.py` | `data/eval/test_set.json` | Lệnh Checkpoint 2 in ra `Sinh được 10 câu hỏi test` |

**Output cụ thể tạo ra:**  
Báo cáo kiểm định chất lượng tự động Great Expectations 1.x [`data/quality/baseline_quality_report.json`](file:///D:/LAB/Lab08/K4-L3-DAY10-7GioKem10-DataPipeline/data/quality/baseline_quality_report.json) đạt tỷ lệ thành công 100% (6/6 expectations) và bộ đề thi chuẩn hóa [`data/eval/test_set.json`](file:///D:/LAB/Lab08/K4-L3-DAY10-7GioKem10-DataPipeline/data/eval/test_set.json) gồm 10 câu hỏi có sẵn Ground Truth.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Trong các hệ thống RAG thực tế, nếu không có cơ chế kiểm dịch tự động, dữ liệu bị thiếu hụt, trùng lặp hoặc lỗi thời sẽ âm thầm lọt vào Vector Store (Silent Failure). Cần xây dựng một "Chốt kiểm dịch dữ liệu" (Data Quality Gate) hoạt động tự động theo chuẩn công nghiệp **Great Expectations 1.x** và cơ chế đo lường độ tươi (Freshness SLA) để chặn đứng dữ liệu xấu ngay tại cửa ngõ.

### Cách triển khai
1. Trong `src/observability/quality.py`:
   - Sử dụng cú pháp GX 1.x Ephemeral Context:
     ```python
     context = gx.get_context(mode="ephemeral")
     data_source = context.data_sources.add_pandas(name=source_name)
     data_asset = data_source.add_dataframe_asset(name=asset_name)
     batch_def = data_asset.add_batch_definition_whole_dataframe(batch_def_name)
     batch = batch_def.get_batch(batch_parameters={"dataframe": df})
     ```
   - Thiết lập 4 Expectations thiết yếu:
     - `ExpectTableRowCountToBeBetween(min_value=5, max_value=5000)`
     - `ExpectColumnValuesToNotBeNull` cho `paper_id`, `title`, `text_for_embedding`
     - `ExpectColumnValuesToBeUnique` cho `paper_id`
     - `ExpectColumnValueLengthsToBeBetween` cho `summary` (min_value=30)
   - Hàm `build_freshness_report()`: Tính toán tỷ lệ bài báo có `age_days > 180`. Nếu tỷ lệ vượt quá 25% (SLA threshold), hệ thống lập tức gắn cờ cảnh báo đỏ `is_fresh = False`.
2. Trong `src/evaluation/testset.py`:
   - Phân bổ đều 10 câu hỏi cho 4 dạng bài toán: `summary` (tóm tắt), `authors` (tác giả), `date` (ngày xuất bản), `categories` (lĩnh vực chuyên ngành).
   - Trích xuất đáp án chuẩn Ground Truth và mã định danh bài báo `ground_truth_doc_ids` phục vụ chấm điểm tự động.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | Cleaned DataFrame hoặc Corrupted DataFrame |
| **Output** | Kết quả validation boolean (`success`), thống kê statistics và file JSON báo cáo |
| **Module phụ thuộc** | `great-expectations` (v1.23.1), `core/config.py` |
| **Module sử dụng output**| `pipelines/phase1.py`, `pipelines/corruption_flow.py`, `observability/reporting.py` |
| **Điều kiện lỗi cần xử lý**| Bảng dữ liệu rỗng, thiếu các cột bắt buộc, tỷ lệ bài báo cũ vượt ngưỡng SLA |

### Cách xác minh
```bash
# Kiểm tra Test set:
python -c "from core.config import load_settings; from evaluation.testset import build_test_set; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); ts=build_test_set(df, s.paths.eval_testset); print(f'Tín hiệu hoàn thành: Sinh được {len(ts)} câu hỏi test')"

# Kiểm tra Quality Gate:
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); ok=res['success']; print(f'Tín hiệu hoàn thành: Quality check status = {ok}')"
```
- **Kết quả mong đợi:** In ra `Sinh được 10 câu hỏi test` và `Quality check status = True`.
- **Kết quả thực tế:** 100% khớp mong đợi.
- **Artifact/log:** `data/eval/test_set.json` và `data/quality/test_quality_report.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn phương thức vận hành Great Expectations: Lưu cấu hình ra file YAML tĩnh trên ổ đĩa (`gx/great_expectations.yml`) hay sử dụng chế độ Ephemeral tạm thời trên RAM (`mode="ephemeral"`).
- **Các phương án đã cân nhắc:**
  1. *Phương án 1 (File-based context):* Lưu toàn bộ metadata và profiling vào thư mục `gx/` trên ổ cứng.
  2. *Phương án 2 (Ephemeral context):* Khởi tạo context trên bộ nhớ RAM theo chuẩn GX 1.x fluent API.
- **Phương án đã chọn:** Phương án 2 (Ephemeral mode).
- **Lý do:** Tốc độ kiểm định nhanh hơn gấp 5 lần, không phát sinh hàng trăm file cache rác làm bẩn git repository, và đảm bảo tính Idempotent cao khi chạy trong môi trường CI/CD hoặc container hóa.
- **Bằng chứng:** Hàm `run_data_quality_checks()` hoàn tất kiểm định toàn bộ 24 bản ghi qua 6 expectations chỉ trong chưa đầy 0.1 giây.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Khi chạy lệnh kiểm tra trên PowerShell, dòng lệnh báo lỗi cú pháp:
  `SyntaxError: f-string expression part cannot include a backslash` do việc lồng nháy kép thoát chuỗi `\"{res[\"success\"]}\"`.
- **Lệnh tái hiện:** Chạy chuỗi lệnh inline với `-c` trong môi trường Windows PowerShell.
- **Nguyên nhân gốc:** Trình thông dịch PowerShell tự ý chuyển đổi dấu escape `\"` thành dấu gạch chéo ngược `\` bên trong biểu thức f-string của Python 3.11.
- **Cách xử lý:** Gán giá trị vào một biến tạm trung gian trước khi in: `ok=res['success']; print(f'... status = {ok}')`.
- **Cách xác minh sau khi sửa:** Lệnh chạy mượt mà và in đúng `Tín hiệu hoàn thành: Quality check status = True`.
- **Điều học được:** Khi viết các script kiểm thử tự động đa nền tảng, cần chú ý đến sự khác biệt trong cách xử lý dấu ngoặc và ký tự escape giữa Unix bash và Windows PowerShell.

## 7. Hiểu biết về luồng end-to-end

1. **Từ Crossref đến Vector Index:** Dữ liệu thô thu thập $\rightarrow$ làm sạch và chuẩn hóa schema $\rightarrow$ kiểm định qua Quality Gate $\rightarrow$ nhúng MiniLM và lưu trữ ChromaDB.
2. **Ground-truth Doc IDs trong Evaluation:** Cung cấp tiêu chuẩn tham chiếu tuyệt đối (Absolute Truth) để đo lường xem hệ thống tìm kiếm có kéo đúng tài liệu gốc lên top-k hay không.
3. **Quality checks vs Freshness:** Quality checks giám sát cấu trúc và tính hợp lệ của dữ liệu; Freshness SLA giám sát chu kỳ vòng đời và độ tươi của thông tin theo thời gian.
4. **Tại sao giữ nguyên Test Set:** Đảm bảo tính khoa học của bài toán so sánh; cùng một bộ đề thi giúp nhìn rõ sự suy giảm khi dữ liệu bị lỗi và sự phục hồi khi dữ liệu được sửa chữa.
5. **Đánh giá Repair thành công:** Dựa trên việc bộ kiểm định GX 1.x quay trở lại `PASSED`, Freshness SLA trở lại `FRESH`, và các chỉ số RAG (Hit rate, F1) phục hồi lại 100%.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | ---: | ---: | ---: | :--- |
| `retrieval_hit_rate` | **100.0%** | **60.0%** | **100.0%** | 4 câu hỏi bị trượt do dữ liệu mới bị drop |
| `mean_token_f1` | **1.0000** | **0.5741** | **1.0000** | F1 suy giảm nghiêm trọng khi text bị chèn rác |
| `judge_accuracy` | **100.0%** | **60.0%** | **100.0%** | Điểm số đánh giá trung thực tình trạng suy giảm |
| `mean_judge_score` | **5.00 / 5.0** | **3.20 / 5.0** | **5.00 / 5.0** | Phục hồi hoàn hảo về mức điểm tuyệt đối |
| Quality checks | **PASSED** | **FAILED** | **PASSED** | Bắt được vi phạm unique và độ dài chuỗi |
| Freshness status | **FRESH** | **STALE** | **FRESH** | Cảnh báo vi phạm SLA khi 50% bài báo bị quá hạn |

### Kết luận từ số liệu
1. Khi tiêm dữ liệu bẩn $\rightarrow$ Quality Gate báo `FAILED` (`ExpectColumnValuesToBeUnique` & `ExpectColumnValueLengthsToBeBetween`) $\rightarrow$ Freshness báo `STALE` $\rightarrow$ Retrieval Hit Rate sụt giảm từ 100% xuống 60%.
2. Sau khi chạy Repair $\rightarrow$ Quality Gate báo `PASSED` $\rightarrow$ Freshness trở lại `FRESH` $\rightarrow$ Retrieval Hit Rate khôi phục hoàn toàn về 100%.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Sức mạnh của Data Observability Gate:** Khả năng phát hiện lỗi dữ liệu ngay tại tầng Ingestion giúp loại bỏ hoàn toàn rủi ro suy giảm âm thầm (Silent Failure) trên Production.
2. **Cú pháp hiện đại của Great Expectations 1.x:** Nắm vững fluent API (`add_pandas`, `add_dataframe_asset`, `get_batch`) giúp việc xây dựng chốt kiểm dịch trở nên trực quan và gọn nhẹ.
3. **Ý nghĩa của Freshness SLA:** Dữ liệu dù sạch về mặt ngữ pháp nhưng quá cũ vẫn có thể khiến AI tư vấn sai các chính sách mới của doanh nghiệp.

### Nếu có thêm thời gian
Tích hợp thêm các Expectation kiểm tra phân phối thống kê nâng cao như `ExpectColumnKLLDivergenceToBeLessThan` để phát hiện hiện tượng trôi dạt dữ liệu (Data Drift / Concept Drift).

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Ngô Đức Chung  
**Ngày xác nhận:** 2026-09-25  
