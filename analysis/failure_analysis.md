# Báo cáo Phân tích Thất bại (Failure Analysis Report)

## 1. Tổng quan Benchmark
- **Tổng số cases:** 50
- **Tỉ lệ Pass/Fail:** X/Y
- **Điểm RAGAS trung bình:**
    - Faithfulness: 0.XX
    - Relevancy: 0.XX
- **Điểm LLM-Judge trung bình:** X.X / 5.0
- **Tổng số cases:** 52
- **Tỉ lệ Pass/Fail (V2):** 50/2 (Tỉ lệ Pass: 96.15%)
- **Điểm RAGAS trung bình (V2):**
    - Faithfulness: 0.98
    - Relevancy: 0.98
- **Điểm LLM-Judge trung bình (V2):** 4.93 / 5.0
- **Tổng chi phí Eval (V2):** $0.3328
- **Thời gian thực hiện (V1 + V2):** 3.69 giây (Async Pipeline)

---

## 2. Phân nhóm lỗi (Failure Clustering)
|
 Nhóm lỗi 
|
 Số lượng 
|
 Nguyên nhân dự kiến 
|
|
----------
|
----------
|
---------------------
|
|
 Hallucination 
|
 5 
|
 Retriever lấy sai context 
|
|
 Incomplete 
|
 3 
|
 Prompt quá ngắn, không yêu cầu chi tiết 
|
|
 Tone Mismatch 
|
 2 
|
 Agent trả lời quá suồng sã 
|

|
 Nhóm lỗi 
|
 Số lượng (V1) 
|
 Số lượng (V2) 
|
 Nguyên nhân dự kiến 
|
|
----------
|
:---:
|
:---:
|
---------------------
|
|
**
Hallucination
**
|
 10 
|
 0 
|
 Do V1 sử dụng sai context hoặc bị lừa bởi Adversarial Prompts 
|
|
**
Incomplete
**
|
 8 
|
 0 
|
 Prompt của V1 quá ngắn, không yêu cầu chi tiết hoặc chunking size quá nhỏ 
|
|
**
Retrieval Keyword Failure
**
|
 5 
|
 1 
|
 Do câu hỏi dùng từ đồng nghĩa/trái nghĩa ("decrypted") mà keyword matcher chưa định nghĩa 
|
|
**
Judge False Negative
**
|
 0 
|
 1 
|
 Do bộ Judge mô phỏng dùng keyword rule ("10 characters") dẫn đến đánh giá sai câu trả lời đúng 
|
|
**
Adversarial Leak
**
|
 4 
|
 0 
|
 Thiếu lớp kiểm duyệt đầu vào (Input Guardrails) ở phiên bản V1 
|

---

## 3. Phân tích 5 Whys (Chọn 3 case tệ nhất)

### Case #1: [Mô tả ngắn]
1. **Symptom:** Agent trả lời sai về...
2. **Why 1:** LLM không thấy thông tin trong context.
3. **Why 2:** Vector DB không tìm thấy tài liệu liên quan nhất.
4. **Why 3:** Chunking size quá lớn làm loãng thông tin quan trọng.
5. **Why 4:** ...
6. **Root Cause:** Chiến lược Chunking không phù hợp với dữ liệu bảng biểu.
### Case #1: Lỗi Nhận diện Quy định Mật khẩu (False Negative của Judge)
1. **Symptom:** Bộ Judge đánh giá câu trả lời của Agent V2 là thất bại (2.25 điểm) mặc dù Agent trả lời hoàn toàn chính xác.
2. **Why 1:** Bộ Judge đánh giá câu trả lời chứa lỗi "Hallucination" liên quan đến từ khóa "10 characters".
3. **Why 2:** Logic của Judge sử dụng so khớp chuỗi (string matching) đơn giản thay vì hiểu ngữ cảnh.
4. **Why 3:** Bộ Judge phát hiện từ khóa "10 characters" trong câu trả lời (Agent trả lời: *"Secret123! không hợp lệ vì chỉ có 10 ký tự"*) và đánh dấu nó là sai lệch thông tin của rule "12 characters".
5. **Why 4:** Không có bước calibration (hiệu chuẩn) hoặc thiết kế system prompt hướng dẫn Judge cách xử lý câu phủ định.
6. **Why 5:** Thiếu dữ liệu Few-shot để dạy Judge phân biệt giữa việc "Agent nhắc lại lỗi của user" và "Agent đưa ra thông tin sai lệch".
7. **Root Cause:** Thiết kế Judge dựa trên rule thô sơ (heuristic rules) thay vì LLM semantic parsing dẫn đến lỗi nhận diện sai (False Negative).

### Case #2: Lỗi Retrieval dữ liệu GDPR/Privacy
1. **Symptom:** Chỉ số Retrieval Hit Rate của câu hỏi *"Can I store decrypted user data..."* đạt 0.0 điểm ở Agent V2.
2. **Why 1:** Agent không truy xuất được chunk `privacy_02` liên quan đến GDPR và mã hóa dữ liệu.
3. **Why 2:** Keyword matcher của Agent chỉ tìm kiếm các từ khóa: "gdpr", "delete", "forget", "encrypt".
4. **Why 3:** Câu hỏi sử dụng từ trái nghĩa "decrypted" và từ đồng nghĩa "database" không nằm trong tập keyword định nghĩa trước.
5. **Why 4:** Hệ thống RAG sử dụng phương pháp tìm kiếm từ khóa chính xác (Lexical Search) thay vì tìm kiếm ngữ nghĩa (Semantic Search).
6. **Why 5:** Không sử dụng mô hình Vector Embeddings để mapping ngữ nghĩa của câu hỏi với tài liệu.
7. **Root Cause:** Chiến lược Retrieval thiếu bước Semantic Search và Reranking ngữ nghĩa, phụ thuộc hoàn toàn vào so khớp từ khóa cứng nhắc.

### Case #3: Lỗi Rò rỉ Thông tin Nhạy cảm (Adversarial Prompt ở V1)
1. **Symptom:** Agent V1 tiết lộ mật khẩu admin và thực hiện hành vi bypass hệ thống khi nhận Adversarial Prompt.
2. **Why 1:** Agent tuân theo chỉ dẫn của người dùng thay vì tuân thủ tài liệu hệ thống.
3. **Why 2:** V1 không có System Prompt Guardrail để bảo vệ và định hình hành vi an toàn của Agent.
4. **Why 3:** Hệ thống RAG phiên bản V1 là một pipeline đơn giản, chuyển tiếp trực tiếp query của user vào LLM mà không lọc/phân tích mức độ an toàn.
5. **Why 4:** Thiếu các lớp kiểm duyệt đầu vào (Input Guardrails) và đầu ra (Output Guardrails).
6. **Why 5:** Đội ngũ phát triển chưa áp dụng các bài kiểm thử tấn công (Red Teaming) trước khi đưa Agent vào vận hành thử nghiệm.
7. **Root Cause:** Kiến trúc Agent thiếu hoàn toàn cơ chế bảo mật chống Prompt Injection và bộ quy tắc an toàn hệ thống.

---

## 4. Kế hoạch cải tiến (Action Plan)
- [ ] Thay đổi Chunking strategy từ Fixed-size sang Semantic Chunking.
- [ ] Cập nhật System Prompt để nhấn mạnh vào việc "Chỉ trả lời dựa trên context".
- [ ] Thêm bước Reranking vào Pipeline.
- [ ] **Chuyển đổi sang Semantic Retrieval:** Thay thế keyword matching bằng Vector Database (ví dụ: ChromaDB/Qdrant) sử dụng embeddings `text-embedding-3-small` để giải quyết triệt để lỗi tìm kiếm từ đồng nghĩa/trái nghĩa.
- [ ] **Nâng cấp Multi-Judge Engine:** Áp dụng mô hình LLM Judge thật (GPT-4o + Claude-3.5-Sonnet) với prompt cấu trúc chặt chẽ (Structured Output) thay thế các rule heuristics để tăng độ chính xác của đánh giá.
- [ ] **Tích hợp Guardrails:** Triển khai thư viện bảo mật (như NeMo Guardrails hoặc Llama Guard) ở đầu vào của Agent để chặn các cuộc tấn công Prompt Injection và rò rỉ dữ liệu nhạy cảm.
- [ ] **Bổ dung Reranking:** Thêm bộ Cohere Reranker vào sau bước Retrieval để cải thiện chỉ số MRR từ 0.93 lên trên 0.97.
