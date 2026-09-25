# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Bùi Tiến Cường             |
| MSSV               | 2A202602539                |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | 7GioKem10                  |
| Vai trò chính    | Data Foundation & Recovery |
| Repository         | https://github.com/nguoibian863-ai/K4-L3-DAY10-7GioKem10-DataPipeline.git |
| Ngày hoàn thành | 2026-09-25                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------- |
| **Raw Ingestion & Lineage** | `src/ingestion/crossref.py` | Crossref REST API / Snapshot local | `data/raw/crossref_records.json`, `data/raw/crossref_response.json` | Hoàn thành |
| **Data Cleaning & Modeling** | `src/ingestion/cleaning.py` | Danh sách `PaperRecord` | `data/clean/papers_clean.csv`, `papers_clean.json` (24 dòng sạch) | Hoàn thành |
| **Idempotent Data Source** | `src/ingestion/crossref.py` (`load_raw_records`) | Nguồn thô ban đầu | Cung cấp dữ liệu chuẩn cho luồng Idempotent Repair | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Kiểm tra schema cho Great Expectations | Ngô Đức Chung / `quality.py` | Cung cấp chính xác kiểu dữ liệu và danh sách cột cho Expectation suite |
| Hỗ trợ tích hợp kịch bản Repair từ Raw | Thân Tiến Đạt / `corruption.py` | Đảm bảo luồng repair đọc đúng dữ liệu thô nguyên vẹn không bị sửa đổi |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Thu thập và bóc tách Crossref API | `src/ingestion/crossref.py`: `fetch_source_records`, `parse_crossref_payload` | 24 bản ghi `PaperRecord` trong `data/raw/` | Lệnh: `python -c "...fetch_source_records..."` in ra `Đã tải 24 bài báo` |
| Làm sạch và chuẩn hóa dữ liệu | `src/ingestion/cleaning.py`: `build_clean_dataframe` | `data/clean/papers_clean.csv` (16 cột chuẩn) | Lệnh kiểm tra Checkpoint 1 in ra `Clean thành công 24 dòng` |

**Output cụ thể tạo ra:**  
Tập dữ liệu sạch [`data/clean/papers_clean.csv`](file:///D:/LAB/Lab08/K4-L3-DAY10-7GioKem10-DataPipeline/data/clean/papers_clean.csv) và [`data/clean/papers_clean.json`](file:///D:/LAB/Lab08/K4-L3-DAY10-7GioKem10-DataPipeline/data/clean/papers_clean.json) gồm đúng 24 bản ghi nghiên cứu khoa học, được loại bỏ sạch thẻ rác XML/HTML, chuẩn hóa tác giả, ngày tháng ISO và tính sẵn trường `age_days` phục vụ đo Freshness.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Dữ liệu học thuật từ API bên ngoài thường xuyên bị nhiễu: định dạng abstract chứa các thẻ XML/HTML đặc thù như `<jats:p>`, ngày tháng lồng ghép trong mảng phức tạp `date-parts`, và API có thể bị lỗi mạng hoặc quá tải `429 Too Many Requests`. Cần xây dựng một tầng thu thập và làm sạch vững chắc, bảo tồn dữ liệu gốc để hỗ trợ truy vết nguồn gốc (Data Lineage) và phục hồi khi xảy ra sự cố.

### Cách triển khai
1. Trong `src/ingestion/crossref.py`:
   - Hàm `_clean_abstract()` sử dụng regex `re.sub(r"<[^>]+>", " ", raw)` để làm sạch triệt để mọi thẻ XML/HTML.
   - Hàm `_parse_date_parts()` bóc tách an toàn các thành phần ngày, tháng, năm từ `date-parts` của Crossref.
   - Hàm `fetch_source_records()` hỗ trợ cơ chế Dual-Mode: thử gọi REST API công khai; nếu mạng chập chờn hoặc gặp mã lỗi 429/503 thì tự động fallback sang đọc file snapshot chuẩn `data/raw/crossref_response.json`.
2. Trong `src/ingestion/cleaning.py`:
   - Hàm `build_clean_dataframe()` tính toán số ngày tuổi: `age_days = max(0, (target_date - pub_date).days)`.
   - Ghép nối cấu trúc chuẩn cho chuỗi ngữ cảnh nhúng vector `text_for_embedding` gồm đủ 5 trường thông tin: Title, Authors, Published, Categories, Summary.
   - Khử trùng lặp bản ghi theo khóa duy nhất `paper_id` và sắp xếp theo ngày xuất bản giảm dần.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | JSON phản hồi từ Crossref REST API hoặc file snapshot `crossref_response.json` |
| **Output** | Danh sách dataclass `PaperRecord` và DataFrame Pandas sạch 16 cột |
| **Module phụ thuộc** | `core/config.py`, `core/utils.py` |
| **Module sử dụng output**| `retrieval/index.py` (nhúng Chroma), `observability/quality.py` (kiểm định GX) |
| **Điều kiện lỗi cần xử lý**| Mất kết nối internet, mã lỗi HTTP 429, bản ghi thiếu tiêu đề hoặc mã DOI |

### Cách xác minh
```bash
# Kiểm tra Ingestion:
python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records; s=load_settings(); r=fetch_source_records(s); print(f'Tín hiệu hoàn thành: Đã tải {len(r)} bài báo')"

# Kiểm tra Cleaning:
python -c "from datetime import datetime, timezone; from core.config import load_settings; from ingestion.crossref import load_raw_records; from ingestion.cleaning import build_clean_dataframe; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), datetime.now(timezone.utc)); print(f'Tín hiệu hoàn thành: Clean thành công {len(df)} dòng')"
```
- **Kết quả mong đợi:** Console in ra lần lượt `Đã tải 24 bài báo` và `Clean thành công 24 dòng`.
- **Kết quả thực tế:** 100% khớp kết quả mong đợi.
- **Artifact/log:** `data/raw/crossref_records.json` và `data/clean/papers_clean.csv`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Xử lý các bản ghi Crossref có ngày tháng công bố không đồng nhất (có bản ghi có đủ ngày-tháng-năm, có bản ghi chỉ có năm hoặc chỉ có trường `created`).
- **Các phương án đã cân nhắc:**
  1. *Phương án 1:* Loại bỏ các bản ghi không có đủ ngày tháng chi tiết.
  2. *Phương án 2:* Chuẩn hóa đa tầng: nếu có `date-parts` thì gán ngày 01 cho tháng/ngày thiếu; nếu không có thì fallback sang trường `created.date-time`.
- **Phương án đã chọn:** Phương án 2.
- **Lý do:** Giúp bảo toàn số lượng bản ghi (không làm mất 20-30% tài liệu nghiên cứu giá trị chỉ vì thiếu ngày xuất bản chính xác đến từng ngày), đồng thời vẫn đảm bảo tính toán `age_days` một cách nhất quán cho hệ thống Freshness SLA.
- **Bằng chứng:** Hàm `_parse_date_parts()` trong `crossref.py` xử lý linh hoạt cho độ dài `len(parts) == 1, 2, 3`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Văn bản tóm tắt xuất ra bị lẫn nhiều thẻ XML dạng `<jats:p>Retrieval-Augmented Generation...</jats:p>` khiến độ dài chuỗi bị tăng ảo và làm nhiễu vector nhúng trong ChromaDB.
- **Lệnh tái hiện:** Đọc trực tiếp trường `abstract` từ file `crossref_response.json`.
- **Nguyên nhân gốc:** Crossref lưu trữ tóm tắt dưới dạng JATS XML format chuẩn của các nhà xuất bản học thuật.
- **Cách xử lý:** Viết hàm `_clean_abstract(raw: str)` áp dụng biểu thức chính quy `re.sub(r"<[^>]+>", " ", raw)` kết hợp `normalize_whitespace` để loại bỏ toàn bộ tag markup mà vẫn giữ trọn vẹn ngữ nghĩa câu văn.
- **Cách xác minh sau khi sửa:** Toàn bộ tóm tắt trong `data/clean/papers_clean.csv` hoàn toàn là văn bản thuần sạch sẽ, không còn bất kỳ ký tự tag nào.
- **Điều học được:** Dữ liệu từ các API công cộng luôn cần bước tiền xử lý bóc tách định dạng (Format Sanitization) trước khi đưa vào các mô hình học máy hay trạm kiểm soát dữ liệu.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu từ Crossref đến Vector Index:** Dữ liệu được fetch từ API $\rightarrow$ lưu snapshot thô $\rightarrow$ parse thành `PaperRecord` $\rightarrow$ làm sạch và tạo `text_for_embedding` $\rightarrow$ đưa qua mô hình MiniLM để tạo vector 384 chiều $\rightarrow$ lưu vào ChromaDB.
2. **Vai trò Ground-truth Document IDs:** Đóng vai trò là "nhãn thật" (True Label) để đo lường xem hệ thống tìm kiếm có kéo đúng tài liệu mục tiêu chứa câu trả lời lên đầu danh sách hay không.
3. **Quality checks vs Freshness:** Quality checks bảo đảm dữ liệu "đúng cấu trúc, không hỏng hóc, không trùng lặp"; Freshness bảo đảm dữ liệu "còn giá trị thời gian, không lỗi thời".
4. **Tại sao giữ nguyên Test Set:** Để đảm bảo biến số duy nhất thay đổi trong thí nghiệm là "chất lượng của dữ liệu" chứ không phải "độ khó của câu hỏi".
5. **Đánh giá Repair thành công:** Khi pipeline chạy lại từ nguồn Raw thô ban đầu và đưa các chỉ số đo lường trở về đúng bằng chỉ số Baseline ban đầu.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | ---: | ---: | ---: | :--- |
| `retrieval_hit_rate` | **100.0%** | **60.0%** | **100.0%** | Hit rate sụt giảm vì dữ liệu bị mất 4 bài báo mới nhất |
| `mean_token_f1` | **1.0000** | **0.5741** | **1.0000** | F1 giảm do summary bị xóa trắng và chèn chuỗi ký tự rác |
| `judge_accuracy` | **100.0%** | **60.0%** | **100.0%** | Điểm số phục hồi 100% sau khi chạy lại Data Pipeline sạch |
| `mean_judge_score` | **5.00 / 5.0** | **3.20 / 5.0** | **5.00 / 5.0** | Minh chứng giá trị của việc khôi phục dữ liệu từ Raw |
| Quality checks | **PASSED** | **FAILED** | **PASSED** | Data Gate hoạt động chính xác |
| Freshness status | **FRESH** | **STALE** | **FRESH** | Cảnh báo kịp thời khi dữ liệu bị sửa ngày về quá khứ |

### Kết luận từ số liệu
1. Dữ liệu bị tiêm lỗi $\rightarrow$ Quality Gate báo `FAILED` $\rightarrow$ Retrieval Hit Rate giảm từ 100% về 60%.
2. Phục hồi từ `data/raw/crossref_records.json` $\rightarrow$ Dữ liệu sạch 24 dòng $\rightarrow$ Hit Rate và F1 trở lại 100%.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Raw Preservation là phao cứu sinh:** Luôn cất giữ bản sao dữ liệu gốc nguyên bản để có thể tái tạo lại hệ thống bất kỳ lúc nào mà không phụ thuộc vào API bên ngoài.
2. **Tác động của việc làm sạch đến RAG:** Việc loại bỏ các thẻ XML và chuẩn hóa câu chữ giúp cải thiện trực tiếp khoảng cách vector cosine trong ChromaDB.
3. **Data Lineage:** Nắm rõ đường đi của dữ liệu từ lúc cào về cho tới khi được nhúng giúp việc debug các lỗi suy giảm mô hình trở nên nhanh chóng.

### Nếu có thêm thời gian
Tích hợp thêm module kiểm tra tự động phát hiện ngôn ngữ (Language Detection) để tự động lọc và dịch các bài báo không phải tiếng Anh sang chuẩn chung trước khi embed.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Bùi Tiến Cường  
**Ngày xác nhận:** 2026-09-25  
