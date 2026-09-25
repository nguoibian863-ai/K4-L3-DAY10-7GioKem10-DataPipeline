# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Phạm Quang Huy             |
| MSSV               | 2A202602900                |
| Khóa/Lớp         | K4                         |
| Tên nhóm         | 7GioKem10                  |
| Vai trò chính    | RAG & Vector Index         |
| Repository         | https://github.com/nguoibian863-ai/K4-L3-DAY10-7GioKem10-DataPipeline.git |
| Ngày hoàn thành | 2026-09-25                 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------- |
| **Embedding Engine** | `src/retrieval/embeddings.py` | Chuỗi văn bản sạch | Vector embeddings chuẩn hóa (384 chiều) | Hoàn thành |
| **Vector Store Indexing** | `src/retrieval/index.py` | DataFrame sạch / hỏng | 3 collection ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) | Hoàn thành |
| **QA Retrieval & Agent** | `src/retrieval/qa.py`, `src/retrieval/agent.py` | Câu hỏi truy vấn, Vector Index | Câu trả lời kèm danh sách doc_ids trích xuất | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| :--- | :--- | :--- |
| Tích hợp mô hình nhúng vào Evaluation | Ngô Đức Chung / `metrics.py` | Đảm bảo bộ đánh giá RAG tính đúng Hit Rate và Token F1 |
| Gỡ rối tải model HuggingFace | Toàn nhóm | Tìm ra giải pháp tải nối đoạn HTTP Range để lưu trữ cache vĩnh viễn |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Nhúng và đánh chỉ mục ChromaDB | `src/retrieval/index.py`: `LocalEmbeddingIndex.build` | `data/chroma/chroma.sqlite3`, `data/embeddings/papers_embeddings.json` | Index thành công 24 documents trong Phase 1 |
| Xây dựng hệ thống QA trích xuất | `src/retrieval/qa.py`: `answer_question` | Trích xuất câu trả lời chính xác cho 10/10 câu hỏi test | `retrieval_hit_rate` = 100.0%, `mean_token_f1` = 1.0000 |

**Output cụ thể tạo ra:**  
Cơ sở dữ liệu vector ChromaDB hoàn chỉnh lưu trữ tại [`data/chroma/`](file:///D:/LAB/Lab08/K4-L3-DAY10-7GioKem10-DataPipeline/data/chroma/) cùng tệp manifest embedding [`data/embeddings/papers_embeddings.json`](file:///D:/LAB/Lab08/K4-L3-DAY10-7GioKem10-DataPipeline/data/embeddings/papers_embeddings.json) ghi nhận chi tiết 24 vector 384 chiều được chuẩn hóa L2 norm trong không gian cosine.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Xây dựng tầng lưu trữ và truy hồi thông tin (Retrieval Layer) có khả năng ánh xạ ngữ nghĩa các đoạn văn bản khoa học vào không gian vector nhiều chiều, đồng thời hỗ trợ tìm kiếm kết hợp cả theo ngữ nghĩa (Semantic Search) và theo tiêu đề bài báo chính xác (Exact Lookup). Đảm bảo phân tách hoàn toàn các tập dữ liệu giữa 3 trạng thái Baseline, Corrupted và Repaired để đo lường công bằng.

### Cách triển khai
1. Trong `src/retrieval/embeddings.py`:
   - Sử dụng lớp `MiniLMEmbeddings` kế thừa từ `langchain_core.embeddings.Embeddings`.
   - Sử dụng `@lru_cache` để tối ưu hóa bộ nhớ RAM, tránh nạp lại mô hình `SentenceTransformer` nhiều lần.
   - Luôn bật cờ `normalize_embeddings=True` để chuẩn hóa các vector về độ dài đơn vị (unit vector).
2. Trong `src/retrieval/index.py`:
   - Khởi tạo client ChromaDB bền vững (`chromadb.PersistentClient`).
   - Cấu hình không gian tìm kiếm `configuration={"hnsw": {"space": "cosine"}}` để tính độ tương đồng cosin trực tiếp từ tích vô hướng của các vector đã chuẩn hóa.
   - Xây dựng từ điển tra cứu nhanh `documents_by_title` và `documents_by_paper_id` phục vụ exact matching khi câu hỏi chứa tiêu đề bài báo trong dấu nháy đơn.
3. Trong `src/retrieval/qa.py`:
   - Hàm `answer_question()` kết hợp giữa exact lookup và semantic search top-k, tự động loại bỏ bản ghi trùng lặp và trích xuất câu trả lời chuẩn xác theo loại câu hỏi (tác giả, ngày công bố, danh mục chuyên ngành hoặc câu đầu tiên của tóm tắt).

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | Cleaned/Corrupted DataFrame từ tầng Ingestion |
| **Output** | Đối tượng `LocalEmbeddingIndex`, kết quả tìm kiếm `SearchResult` và `AnswerResult` |
| **Module phụ thuộc** | `sentence-transformers`, `chromadb`, `core/config.py` |
| **Module sử dụng output**| `evaluation/metrics.py`, `retrieval/agent.py` |
| **Điều kiện lỗi cần xử lý**| Kho vector rỗng, câu truy vấn không tìm thấy tài liệu phù hợp (trả về fallback message) |

### Cách xác minh
```bash
python -c "from retrieval.embeddings import MiniLMEmbeddings; m = MiniLMEmbeddings('sentence-transformers/all-MiniLM-L6-v2'); emb = m.embed_query('agentic RAG'); print(f'Vector dimension: {len(emb)}')"
```
- **Kết quả mong đợi:** Vector dimension: 384.
- **Kết quả thực tế:** Vector dimension: 384.
- **Artifact/log:** `data/chroma/chroma.sqlite3`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn thuật toán đo khoảng cách trong ChromaDB: Euclidean Distance (`l2`), Inner Product (`ip`) hay Cosine Similarity (`cosine`).
- **Các phương án đã cân nhắc:**
  1. *Phương án 1 (Euclidean L2):* Tính khoảng cách hình học thông thường.
  2. *Phương án 2 (Cosine Similarity):* Đo góc giữa hai vector không gian.
- **Phương án đã chọn:** Phương án 2 (Cosine Similarity).
- **Lý do:** Đối với các văn bản học thuật có độ dài không đồng đều, khoảng cách Euclidean có thể bị bóp méo do độ dài của chuỗi văn bản. Khoảng cách Cosine chỉ tập trung vào hướng của vector (ngữ nghĩa nội dung) mà không bị phụ thuộc vào độ dài đoạn tóm tắt, giúp tăng độ chính xác xếp hạng tìm kiếm.
- **Bằng chứng:** Điểm tương đồng `score = max(0.0, 1.0 - distance)` trong `src/retrieval/index.py` phản ánh trung thực mức độ phù hợp của tài liệu.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Khi gọi `SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")`, chương trình bị nghẽn vô hạn, kiểm tra file blob trong cache chỉ có kích thước `0 bytes` và xuất hiện thông báo:
  `ProtocolError: ('Connection broken: IncompleteRead(676820 bytes read, 90191556 more expected)')`.
- **Lệnh tái hiện:** Tải mô hình qua phương thức đơn luồng mặc định trên mạng phòng lab.
- **Nguyên nhân gốc:** Đường truyền mạng quốc tế đến máy chủ CDN AWS của HuggingFace bị gián đoạn giữa chừng sau khoảng 600KB, trong khi socket không có read timeout trên Windows nên tiến trình chờ vô tận.
- **Cách xử lý:** Tôi cùng nhóm đã thiết kế kịch bản tải nối đoạn bằng **HTTP Range Requests** (`Range: bytes=start-end`), chia nhỏ file 90.8MB thành các block 2MB kèm cơ chế retry 8 lần và đặt `socket.setdefaulttimeout(15.0)`. Ngay khi tải xong, đổi tên thành `model.safetensors` và copy vào đúng vị trí của HuggingFace cache.
- **Cách xác minh sau khi sửa:** Chạy kiểm tra nạp mô hình: `Loaded model successfully!`, vector sinh ra tức thì trong 0.2 giây.
- **Điều học được:** Trong môi trường thực tế, việc triển khai các hệ thống RAG cần có chiến lược quản lý model offline và cơ chế tải dự phòng (Fault-tolerant Downloader) để tránh phụ thuộc vào hạ tầng mạng của bên thứ ba.

## 7. Hiểu biết về luồng end-to-end

1. **Từ Crossref đến Vector Index:** Dữ liệu thô $\rightarrow$ làm sạch thành text ngữ cảnh $\rightarrow$ nhúng thành vector 384 chiều $\rightarrow$ lưu trữ trong ChromaDB HNSW graph.
2. **Ground-truth Doc IDs trong Evaluation:** Cho phép tính toán chính xác chỉ số `retrieval_hit_rate` bằng cách đối chiếu xem tài liệu cần tìm có nằm trong top-k kết quả trúng thưởng của bộ tìm kiếm hay không.
3. **Quality Gate vs Freshness:** Quality Gate kiểm soát tính đúng đắn cấu trúc dữ liệu trước khi embed (ngăn dữ liệu rác vào Chroma); Freshness kiểm soát giá trị thời gian để cảnh báo khi kiến thức trong kho sắp lỗi thời.
4. **Tại sao giữ nguyên Test Set:** Để đảm bảo tính công bằng của thí nghiệm đối chứng; chỉ có chất lượng dữ liệu thay đổi, thước đo luôn cố định.
5. **Đánh giá Repair thành công:** Chỉ số Hit Rate từ 60% vọt trở lại 100%, F1 từ 0.5741 trở lại 1.0000 và Quality Gate báo `PASSED`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| :--- | ---: | ---: | ---: | :--- |
| `retrieval_hit_rate` | **100.0%** | **60.0%** | **100.0%** | Bị mất 4/10 câu do 4 bài báo mới nhất bị loại khỏi kho vector |
| `mean_token_f1` | **1.0000** | **0.5741** | **1.0000** | Vector bị lệch do nhiễu và thiếu summary làm câu trả lời bị sai |
| `judge_accuracy` | **100.0%** | **60.0%** | **100.0%** | AI Judge phản ánh đúng sự sa sút chất lượng của hệ thống |
| `mean_judge_score` | **5.00 / 5.0** | **3.20 / 5.0** | **5.00 / 5.0** | Phục hồi hoàn hảo sau khi Re-index dữ liệu sạch |
| Quality checks | **PASSED** | **FAILED** | **PASSED** | Bắt được vi phạm unique và độ dài chuỗi |
| Freshness status | **FRESH** | **STALE** | **FRESH** | Phát hiện ngày tháng bị lùi về quá khứ |

### Kết luận từ số liệu
1. **Dữ liệu bị drop & inject noise:** Không gian vector bị khuyết thiếu các điểm dữ liệu quan trọng, khiến khoảng cách cosine bị lệch, dẫn đến việc top-4 kết quả trả về sai tài liệu mục tiêu (Hit Rate rớt từ 100% xuống 60%).
2. **Sau khi Idempotent Repair:** Kho vector `papers-repaired` được nạp lại đầy đủ 24 điểm dữ liệu sạch, khôi phục lại toàn bộ độ bao phủ tìm kiếm (Hit Rate đạt lại 100%).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Hiểm họa Ghost Vectors:** Nếu không xóa và quản lý sạch collection khi update, các vector mồ côi (orphaned vectors) sẽ làm sai lệch nghiêm trọng kết quả tìm kiếm.
2. **Exact vs Semantic Search:** Việc kết hợp Hybrid giữa tìm kiếm chính xác (metadata lookup) và tìm kiếm ngữ nghĩa (cosine vector) đem lại độ chính xác cao nhất cho RAG.
3. **Data Quality quyết định Vector Space:** Mô hình nhúng dù tốt đến đâu cũng sẽ sinh ra vector sai lệch nếu đầu vào văn bản bị chèn ký tự rác hoặc bị cắt cụt.

### Nếu có thêm thời gian
Triển khai thêm tầng Re-ranking (sử dụng Cross-Encoder như `bge-reranker-large`) sau bước tìm kiếm sơ cấp của ChromaDB để tối ưu hóa thứ hạng tài liệu được cung cấp cho Agent.

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phạm Quang Huy  
**Ngày xác nhận:** 2026-09-25  
