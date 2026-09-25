# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | 7GioKem10                  |
| Repository         | https://github.com/nguoibian863-ai/K4-L3-DAY10-7GioKem10-DataPipeline.git |
| Ngày hoàn thành | 2026-09-25                 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Tạ Hoàng Vinh | 2A202602543 | Trưởng nhóm / Pipeline Integrator | `core/config.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |
| 2 | Bùi Tiến Cường | 2A202602539 | Data Foundation & Recovery | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `data/raw/` |
| 3 | Phạm Quang Huy | 2A202602900 | RAG & Vector Index | `src/retrieval/index.py`, `src/retrieval/embeddings.py`, ChromaDB collections |
| 4 | Ngô Đức Chung | 2A202602985 | Observability & Evaluation | `src/observability/quality.py` (GX 1.x & Freshness), `src/evaluation/testset.py` |
| 5 | Thân Tiến Đạt | 2A202603023 | Corruption & Reporting Lead | `src/ingestion/corruption.py`, `src/observability/reporting.py`, `reports/` |

## 2. Tóm tắt kết quả

Nhóm **7GioKem10** đã hoàn thành toàn bộ 7 Checkpoint (CP0 – CP6) của bài lab:
1. **Baseline Pipeline (CP0 – CP3):** Thu thập 24 bản ghi metadata từ Crossref API, chuẩn hóa schema, tính `age_days`, ghép `text_for_embedding`, lưu trữ an toàn bản thô (Raw Preservation) và bản sạch (`papers_clean.csv`, `papers_clean.json`). Nhúng ngữ nghĩa vào ChromaDB collection `papers-baseline`. Kết quả đánh giá trên bộ Benchmark 10 câu hỏi đạt **Retrieval Hit Rate = 100.0%**, **Mean Token F1 = 1.0000**, **Judge Accuracy = 100.0% (5.0/5.0)**. Hệ thống vượt qua Quality Gate Great Expectations 1.x (`success=True`) và Freshness SLA (`is_fresh=True`, tỷ lệ cũ 4.2%).
2. **Controlled Corruption Suite (CP4):** Tiêm 6 kịch bản lỗi thực tế (bỏ rơi 20% bài mới, xóa trắng summary, chèn nhiễu ký tự, cắt ngắn tiêu đề, lùi ngày xuất bản 365 ngày, nhân bản dòng). Kết quả chứng minh hiện tượng **Silent Failure**: AI Agent vẫn trả lời tự tin không báo lỗi runtime, nhưng chất lượng sụt giảm nghiêm trọng (**Hit Rate giảm xuống 60.0%**, **Token F1 giảm xuống 0.5741**, **Judge Score giảm còn 3.20/5.0**). Chốt kiểm soát GX 1.x lập tức báo động đỏ (`FAILED`) và Freshness SLA cảnh báo (`STALE`, 50% bài cũ).
3. **Idempotent Repair & Comparison (CP5 – CP6):** Tự động khôi phục dữ liệu sạch từ bản lưu thô nguyên bản (`data/raw/crossref_records.json`), tái tạo vector store `papers-repaired` và đưa toàn bộ chỉ số RAG trở về **100% mức chuẩn ban đầu**. Báo cáo Markdown đối chiếu 3 trạng thái đã được xuất bản hoàn chỉnh tại `data/reports/corruption_report.md`.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Nguồn Crossref API (hoặc Snapshot Offline data/raw/crossref_response.json)
    ├── 1. Kéo dữ liệu & Raw Preservation    -> data/raw/crossref_records.json
    ├── 2. Transformation & Cleaning        -> data/clean/papers_clean.csv & .json
    ├── 3. Great Expectations 1.x & SLA      -> data/quality/ (GX Ephemeral + Freshness)
    ├── 4. ChromaDB Vector Store Indexing   -> sentence-transformers + ChromaDB collection
    ├── 5. Evaluation Benchmarking          -> data/eval/test_set.json -> baseline_metrics.json
    ├── 6. Synthetic Data Corruption        -> 6 lỗi thực tế -> corrupted_metrics.json
    └── 7. Idempotent Repair & Comparison   -> Phục hồi từ Raw -> corruption_report.md
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | Crossref API / `data/raw/` | Fetch API, retry backoff, parse payload, lưu trữ raw snapshot | `data/raw/crossref_records.json` | Bùi Tiến Cường |
| **Cleaning** | `PaperRecord` list | Khử trùng lặp `paper_id`, tính `age_days`, tạo `text_for_embedding` | `data/clean/papers_clean.csv`, `papers_clean.json` | Bùi Tiến Cường |
| **Embedding/Index** | Cleaned DataFrame | Nhúng `all-MiniLM-L6-v2`, lập chỉ mục ChromaDB (cosine space) | `data/chroma/`, `data/embeddings/` | Phạm Quang Huy |
| **Evaluation** | Cleaned DataFrame | Sinh 10 câu hỏi qua 4 nhóm (`summary`, `authors`, `date`, `categories`), đo Hit Rate, F1, LLM Judge | `data/eval/test_set.json`, `data/results/` | Ngô Đức Chung |
| **Observability** | DataFrame (Clean/Corrupt) | Great Expectations 1.x ephemeral suite (4 checks) & Freshness SLA (180 ngày) | `data/quality/*.json` | Ngô Đức Chung |
| **Corruption/Repair**| Cleaned DataFrame, Raw snapshot | Tiêm 6 kịch bản lỗi; Tự động phục hồi nhất quán từ nguồn Raw thô | `corruption_log.json`, `repaired_clean.*` | Thân Tiến Đạt |
| **Orchestration** | Toàn bộ các module | Điều phối luồng Phase 1 (`run_phase1.py`) và Phase 2 (`run_corruption_flow.py`) | `data/reports/*.md` | Tạ Hoàng Vinh |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| :--- | :--- |
| `LLM_PROVIDER` | `gemini` |
| `LLM_MODEL` | `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày (ngưỡng tối đa bài cũ cho phép: 25%) |
| Collections Chroma | `papers-baseline`, `papers-corrupted`, `papers-repaired` |

### Lệnh cài đặt

Sử dụng môi trường Python tiêu chuẩn:
```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

### Lệnh chạy

1. **Chạy Baseline Pipeline (Pha 1):**
```bash
python script/run_phase1.py
```

2. **Chạy Corruption, Repair & So sánh 3 trạng thái (Pha 2):**
```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| :--- | :--- | :--- | :--- |
| Baseline pipeline | Thành công (Exit code 0) | 2026-09-25 15:17:38 | `data/reports/phase1_report.md`, `baseline_metrics.json` |
| Corruption flow | Thành công (Exit code 0) | 2026-09-25 15:19:09 | `data/reports/corruption_report.md`, `corruption_log.json` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| :--- | :--- |
| Source | Crossref REST API công khai (`https://api.crossref.org/works`) |
| Query/filter | `query="agentic retrieval augmented generation large language model"`, `filter="from-pub-date:2026-03-29,has-abstract:true"` |
| Thời điểm lấy dữ liệu | 2026-09-25 |
| Số record nhận được | 24 bài báo khoa học |
| Cơ chế retry/backoff | Tự động thử lại khi gặp lỗi mạng/429; Fallback tự động sang snapshot offline `data/raw/crossref_response.json` nếu mất kết nối |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| :--- | :--- | :--- | :--- | :--- |
| `paper_id` | String | Có | Mã DOI định danh duy nhất của bài báo | Bỏ qua record nếu thiếu; bắt buộc không null và unique |
| `title` | String | Có | Tiêu đề công trình khoa học | Bỏ qua record nếu thiếu; loại bỏ khoảng trắng thừa |
| `summary` | String | Có | Tóm tắt nội dung bài báo | Lọc bỏ thẻ XML/HTML `<jats:p>`, yêu cầu tối thiểu >= 30 ký tự |
| `authors` | List[String] | Không | Danh sách tên các tác giả | Ghép nối `authors_joined = ", ".join(authors)` |
| `categories` | List[String] | Không | Danh sách lĩnh vực phân loại chuyên môn | Ghép nối `categories_joined = ", ".join(categories)` |
| `published` | String (ISO) | Có | Ngày công bố bài báo (`YYYY-MM-DD`) | Parse date parts, fallback ngày `created` |
| `age_days` | Integer | Có | Số ngày tuổi từ ngày công bố đến thời điểm chạy | `(run_date - published).days`, dùng kiểm định Freshness |
| `text_for_embedding`| String | Có | Đoạn văn bản hoàn chỉnh phục vụ nhúng vector | Ghép nối chuẩn cấu trúc 5 trường thông tin |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| :--- | :--- | ---: | :--- |
| Lọc bỏ thẻ XML/HTML `<jats:p>` trong tóm tắt | Validity / Syntactic Accuracy | 24 | Hàm `_clean_abstract()`, regex `<[^>]+>` |
| Khử trùng lặp khóa chính `paper_id` | Uniqueness | 0 (tập gốc đã chuẩn) | `df.drop_duplicates(subset=['paper_id'])` |
| Loại bỏ khoảng trắng thừa | Completeness & Conformity | 24 | `normalize_whitespace()` |
| Định dạng chuẩn ngày tháng ISO | Temporal Validity | 24 | `_parse_date()`, tính `age_days` |

**Cách tạo `text_for_embedding`, document ID và `age_days`:**
- `age_days = (run_date.date() - published_date).days` đo lường số ngày tuổi chính xác của từng tài liệu so với ngày chạy pipeline.
- `text_for_embedding` ghép nối chuẩn mực:
  ```text
  Title: <Tiêu đề>
  Authors: <Tác giả 1, Tác giả 2>
  Published: <YYYY-MM-DD>
  Categories: <Chuyên ngành>
  Summary: <Tóm tắt sạch>
  ```
- Document ID được gán tương ứng theo DOI: `f"{paper_id}::{index}"` trong ChromaDB.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| :--- | :--- |
| Số câu hỏi | 10 câu |
| Các `question_type` | 4 nhóm: `summary` (3), `authors` (3), `date` (2), `categories` (2) |
| Ground-truth document ID | DOI chính xác của bài báo (`ground_truth_doc_ids: [paper_id]`) |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (dimension: 384, normalized cosine) |
| Vector store/collection | ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k` | 4 |
| LLM provider/model | `gemini-2.5-flash` (Structured Output với Schema `JudgeVerdict`) |
| Test set dùng chung | `data/eval/test_set.json` (cố định 10 câu cho cả 3 trạng thái) |

**Lý do giữ nguyên test set cho cả 3 trạng thái:**  
Để đảm bảo tính khách quan và khoa học (Controlled Experiment). Bộ đề thi đóng vai trò "thước đo cố định". Bằng cách giữ nguyên câu hỏi và đáp án chuẩn (Ground Truth), mọi sự thay đổi về điểm số Hit Rate và F1 đều phản ánh trực tiếp sự suy giảm hay phục hồi của chất lượng dữ liệu nền, loại bỏ nhiễu do câu hỏi thay đổi.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| :--- | :--- | :--- | :--- |
| Raw response/records | `data/raw/crossref_records.json` | Có | 24 bài báo gốc |
| Cleaned dataset | `data/clean/papers_clean.csv`, `.json` | Có | 24 dòng sạch, đủ 16 cột |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json` | Có | Metadata và vector Chroma |
| Evaluation set | `data/eval/test_set.json` | Có | 10 câu hỏi đa dạng |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Hit rate: 100%, F1: 1.0 |
| Quality/freshness | `data/quality/baseline_quality_report.json` | Có | GX 1.x validation: True |
| Baseline report | `data/reports/phase1_report.md` | Có | Báo cáo Markdown chi tiết |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| :--- | ---: | :--- |
| `retrieval_hit_rate` | 100.0% (1.0000) | 10/10 câu hỏi tìm chính xác tài liệu mục tiêu trong top-4 kết quả |
| `mean_token_f1` | 1.0000 | Câu trả lời trích xuất trùng khớp hoàn hảo với Ground Truth |
| `judge_accuracy` | 100.0% (1.0000) | Gemini 2.5 Flash đánh giá 10/10 câu trả lời chính xác về ngữ nghĩa |
| `mean_judge_score` | 5.00 / 5.0 | Điểm tuyệt đối từ AI Judge |

## 8. Data quality và freshness

### Quality checks (Great Expectations 1.x)

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| :--- | :--- | :--- | :--- | :--- |
| `ExpectTableRowCountToBeBetween` | Completeness | [5, 5000] dòng | PASSED (24 dòng) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`paper_id`) | Completeness | 0% null | PASSED (0 null) | `baseline_quality_report.json` |
| `ExpectColumnValuesToBeUnique` (`paper_id`) | Uniqueness | 100% unique | PASSED (24 unique) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`title`) | Completeness | 0% null | PASSED (0 null) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`text_for_embedding`) | Completeness | 0% null | PASSED (0 null) | `baseline_quality_report.json` |
| `ExpectColumnValueLengthsToBeBetween` (`summary`) | Validity | min_value = 30 chars | PASSED (độ dài > 100) | `baseline_quality_report.json` |

### Freshness SLA

| Thuộc tính | Giá trị |
| :--- | :--- |
| Freshness được đo tại | `data/clean/papers_clean.csv` qua trường `age_days` |
| Timestamp mới nhất / cũ nhất | 2026-07-22 (mới nhất) / 2026-03-28 (cũ nhất) |
| Ngưỡng freshness | 180 ngày; Tỷ lệ quá hạn tối đa cho phép: 25.0% |
| Trạng thái baseline | **FRESH (is_fresh = True)** |
| Lý do | Chỉ có 1/24 bài báo (>180 ngày), tương đương 4.17% (nằm sâu trong ngưỡng an toàn <25%) |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| :--- | :--- | ---: | :--- | :--- | :--- |
| **Drop latest records** | Cắt bỏ 20% bản ghi mới nhất ở đầu bảng | 4 records | Không có tín hiệu ở bảng, nhưng Hit Rate sụt giảm | Hit Rate giảm từ 100% về 60% | Đọc lại từ snapshot raw đầy đủ |
| **Blank summary** | Gán summary rỗng `""` | 2 records | `ExpectColumnValueLengthsToBeBetween` FAILED | Mất thông tin tóm tắt khi trả lời câu hỏi | Re-clean từ trường summary gốc |
| **Inject noise** | Chèn chuỗi ký tự rác vào summary | 2 records | Gây nhiễu vector ngữ nghĩa | Vector bị lệch khoảng cách cosine | Tái tạo lại từ raw records |
| **Truncate title** | Cắt ngắn tiêu đề `< 8` ký tự | 2 records | Mất khả năng match tiêu đề chính xác | Gây trượt retrieval exact lookup | Khôi phục tiêu đề gốc |
| **Stale date** | Lùi ngày xuất bản về 365 ngày trước | 8 records | Freshness SLA: **STALE (is_fresh=False)** | Tỷ lệ bài cũ tăng lên 50.0% (>25%) | Lấy lại ngày xuất bản chuẩn từ raw |
| **Duplicate rows** | Nhân đôi 2 bản ghi chèn thêm vào cuối | 2 records | `ExpectColumnValuesToBeUnique` FAILED | Làm loãng vector store | Deduplicate theo `paper_id` |

**Corruption log:**
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có đầy đủ 6 dạng lỗi, liệt kê chi tiết `paper_id` và số lượng dòng bị can thiệp.

**Cơ chế Idempotent Repair:**  
Hệ thống không "sửa chắp vá" trên tập dữ liệu đã bị hỏng, mà thực hiện nguyên lý **Idempotency (Nhất quán bất biến)**: Tái khởi động quy trình Ingestion từ nguồn thô đáng tin cậy duy nhất (`data/raw/crossref_records.json`), chạy lại toàn bộ Data Cleaning pipeline với logic deduplication và schema validation chuẩn, sau đó xóa và nạp lại toàn bộ vector collection trong ChromaDB. Bất kể chạy lại bao nhiêu lần, kết quả luôn hội tụ về trạng thái sạch ban đầu.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| `retrieval_hit_rate` | **100.0%** | **60.0%** | **100.0%** | -40.0% | +40.0% (100%) | Bị trượt các câu hỏi thuộc bài báo bị drop |
| `mean_token_f1` | **1.0000** | **0.5741** | **1.0000** | -0.4259 | +0.4259 (100%)| Câu chữ bị sai lệch hoặc thiếu ngữ cảnh |
| `judge_accuracy` | **100.0%** | **60.0%** | **100.0%** | -40.0% | +40.0% (100%)| Điểm AI đánh giá phản ánh đúng thực tế |
| `mean_judge_score` | **5.00 / 5.0** | **3.20 / 5.0** | **5.00 / 5.0** | -1.80 | +1.80 (100%) | Chất lượng suy giảm rõ rệt khi data bẩn |
| Quality checks pass/fail | **PASSED** | **FAILED** | **PASSED** | Gióng chuông đỏ | Đạt chuẩn 100% | Bắt được lỗi trùng ID & rỗng summary |
| Freshness status | **FRESH** | **STALE** | **FRESH** | Cảnh báo quá hạn | Về 4.2% an toàn| Phát hiện tỷ lệ bài cũ 50% vi phạm SLA |

### Hai kết luận nhân quả từ thực nghiệm:
1. **Dữ liệu lỗi $\rightarrow$ Quality Gate báo động $\rightarrow$ Agent suy giảm hiệu năng (Silent Failure):**  
   Khi 4 bài báo mới bị drop và 2 bài bị xóa summary, Quality Gate GX 1.x lập tức báo `FAILED` và Freshness báo `STALE`. Trên hệ thống RAG, Agent vẫn tự tin trả lời mà không phát sinh exception runtime (Silent Failure), nhưng `retrieval_hit_rate` sụt giảm nghiêm trọng từ 100% xuống 60%, kéo `mean_token_f1` từ 1.0 xuống 0.5741.
2. **Idempotent Repair $\rightarrow$ Khôi phục 100% độ tin cậy của AI:**  
   Bằng việc kích hoạt quy trình tự phục hồi Idempotent từ bản lưu thô nguyên bản (`crossref_records.json`), Quality Gate chuyển về `PASSED`, Freshness SLA trở lại `FRESH`, và toàn bộ chỉ số RAG (`hit_rate` = 100%, `token_f1` = 1.0000, `judge_score` = 5.0/5.0) lấy lại 100% phong độ ban đầu.

## 11. Vấn đề tích hợp quan trọng

- **Triệu chứng:** Khi chạy `run_phase1.py`, tiến trình bị treo (hang) vô hạn tại bước tải mô hình embedding `sentence-transformers/all-MiniLM-L6-v2` (~90 MB) từ HuggingFace Hub.
- **Nguyên nhân:** Do hạ tầng mạng kết nối quốc tế từ Việt Nam đến máy chủ AWS CDN của HuggingFace thường xuyên bị ngắt ngang sau khi đọc được khoảng 600 KB (`urllib3.exceptions.ProtocolError: IncompleteRead`), trong khi thư viện `huggingface_hub` mặc định dùng tải đơn luồng không đặt socket read timeout trên Windows nên tiến trình chờ vô tận.
- **Cách xử lý:** Nhóm đã xây dựng một tiện ích tải nối đoạn thông minh sử dụng **HTTP Range Requests** (`bytes=start-end`), kết hợp `socket.setdefaulttimeout(15.0)` và cơ chế tự động thử lại (retry) theo từng chunk 2MB để kéo đầy đủ file trọng số `model.safetensors` và tokenizer vào đúng cấu trúc cache của HuggingFace (`~/.cache/huggingface/hub/`).
- **Cách xác minh:** Kiểm tra `SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')` nạp thành công 100% offline, sinh vector shape `(1, 384)` tức thì trong 0.2 giây mà không cần kết nối mạng.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| :--- | :--- | :--- |
| Tập dữ liệu thử nghiệm ở quy mô lab (24 bài báo) | Chưa kiểm thử được hiệu năng vector index khi đạt quy mô hàng triệu vector | Mở rộng ingestion đa luồng (AsyncIO) và áp dụng HNSW index phân mảnh |
| Fallback Judge dựa trên Token F1 khi không có mạng/LLM | Điểm số ngữ nghĩa có thể chưa linh hoạt như LLM trực tiếp | Triển khai mô hình SLM cục bộ (như Ollama Qwen/Llama3) làm Judge offline |
| Cơ chế phục hồi hiện tại chạy Full Re-index | Tốn chi phí tính toán khi tập dữ liệu lớn | Chuyển sang Incremental Repair (chỉ bù đắp bản ghi thiếu và cập nhật bản ghi đổi) |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác (`7GioKem10`).
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp (`run_phase1.py` và `run_corruption_flow.py`).
- [x] Baseline, corrupted và repaired dùng chung cùng evaluation set 10 câu.
- [x] Bảng metrics khớp chính xác với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
