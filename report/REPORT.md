# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Lê Quang Minh  
**Nhóm:** C401-B3 
**Ngày:** 10/04/2026  

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**  
High cosine similarity nghĩa là hai vector có hướng rất gần nhau trong không gian đa chiều, cho thấy hai đoạn văn bản có sự tương đồng lớn về mặt ngữ nghĩa hoặc ngữ cảnh, bất kể độ dài văn bản khác nhau.

**Ví dụ HIGH similarity:**
- Sentence A: "Làm thế nào để cấu hình Wazuh agent trên Linux?"
- Sentence B: "Hướng dẫn cài đặt và thiết lập Wazuh cho hệ điều hành Ubuntu."  
→ Cả hai đều cùng chủ đề kỹ thuật: cấu hình Wazuh.

**Ví dụ LOW similarity:**
- Sentence A: "Blockchain giúp truy xuất nguồn gốc sữa."
- Sentence B: "Hôm nay thời tiết Hà Nội rất đẹp."  
→ Hai câu thuộc hai lĩnh vực hoàn toàn khác nhau.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**  
Cosine similarity tập trung vào **hướng vector (semantic meaning)** thay vì **độ dài vector**, do đó phù hợp hơn với dữ liệu văn bản có độ dài không đồng đều, vốn là đặc trưng của dữ liệu ngôn ngữ tự nhiên.

---

### Chunking Math (Ex 1.2)

**Bài toán:**  
Một tài liệu có 10,000 ký tự được chia bằng `FixedSizeChunker` với `chunk_size = 500` và `overlap = 50`.

**Cách tính:**
1.  **Chunk đầu tiên:** Lấy 500 ký tự đầu tiên. Phần còn lại của tài liệu là `10000 - 500 = 9500` ký tự.
2.  **Bước nhảy (Step):** Mỗi chunk tiếp theo sẽ bắt đầu sau chunk trước đó một khoảng bằng `chunk_size - overlap`.
    - `Step = 500 - 50 = 450` ký tự.
3.  **Số chunk còn lại:** Ta cần chia 9500 ký tự còn lại thành các đoạn, mỗi đoạn được "cover" bởi một bước nhảy 450 ký tự.
    - Số chunk cần thêm = `ceil(9500 / 450) = ceil(21.11) = 22` chunks.
4.  **Tổng số chunk:**
    - `Tổng = 1 (chunk đầu tiên) + 22 (các chunk còn lại) = 23` chunks.

**Đáp án:** 23 chunks

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Tài liệu pháp lý - Bộ luật Dân sự Việt Nam 2015

**Tại sao nhóm chọn domain này?**
> *Nhóm chọn domain này để xây dựng một trợ lý tra cứu thông tin pháp lý chuyên sâu về luật dân sự. Việc xử lý một văn bản pháp luật lớn, có cấu trúc phức tạp là một thử thách thú vị và mang lại giá trị thực tiễn cao, giúp người dùng nhanh chóng tìm kiếm và hiểu các quy định của pháp luật.*

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự (ước tính) | Metadata đã gán |
|---|---|---|---|---|
| 1 | `Tài liệu Bộ luật DS 2015.md` | Public | ~150,000 | `doc_type: legal_code`, `jurisdiction: vietnam` |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| `doc_type` | string | `legal_code`, `commentary` | Giúp phân biệt giữa văn bản luật gốc và các bài bình luận, phân tích. |
| `jurisdiction` | string | `vietnam` | Hữu ích khi hệ thống mở rộng để bao gồm luật của nhiều quốc gia khác nhau. |
| `source_file` | string | `Tài liệu Bộ luật DS 2015.md` | Cung cấp khả năng truy vết về tài liệu gốc, hữu ích cho việc xác minh thông tin. |
| `article_number` | string | `Điều 308` | (Tiềm năng) Cho phép truy vấn trực tiếp đến một điều luật cụ thể khi chunking. |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)
### Phân tích cơ sở (Baseline Analysis)

Để đánh giá hiệu quả của các chiến lược chunking khác nhau, tôi đã tiến hành một phân tích cơ sở trên tệp `Tài liệu Bộ luật DS 2015.md` (140,820 ký tự). Các chiến lược được so sánh bao gồm `FixedSizeChunker`, `SentenceChunker`, và `RecursiveChunker`.

**Kết quả so sánh:**

| Chiến lược      | Số lượng chunk | Kích thước trung bình | Kích thước nhỏ nhất | Kích thước lớn nhất |
| :--------------- | :------------- | :-------------------- | :------------------ | :------------------ |
| **Fixed-Size**   | 149            | 994.77                | 220                 | 1000                |
| **By Sentences** | 134            | 1048.69               | 224                 | 2164                |
| **Recursive**    | 686            | 203.60                | 1                   | 994                 |

**Nhận xét:**

*   **Fixed-Size Chunker**: Tạo ra các chunk có kích thước đồng đều nhất, gần với mục tiêu `chunk_size=1000`. Tuy nhiên, chiến lược này có nguy cơ cắt ngang câu hoặc ý, làm mất ngữ cảnh.
*   **Sentence Chunker**: Giữ được tính toàn vẹn của câu, giúp bảo toàn ngữ nghĩa tốt hơn. Nhược điểm là kích thước chunk rất không đồng đều, có thể tạo ra các chunk quá lớn (2164 ký tự), vượt quá giới hạn token của một số mô hình embedding.
*   **Recursive Chunker**: Tạo ra số lượng chunk lớn nhất với kích thước trung bình nhỏ nhất. Chiến lược này linh hoạt trong việc chia nhỏ văn bản theo cấu trúc logic (đoạn, dòng, câu), nhưng có thể tạo ra các chunk rất nhỏ (1 ký tự), có thể không chứa đủ thông tin hữu ích.


### Strategy Của Tôi

**Loại:** RecursiveChunker

**Mô tả cách hoạt động:**
> *Chiến lược này hoạt động bằng cách chia văn bản một cách đệ quy theo một danh sách các dấu phân tách (separators) được ưu tiên. Nó bắt đầu với dấu phân tách có ý nghĩa ngữ nghĩa cao nhất (ví dụ: xuống dòng kép `\n\n` để tách các đoạn) và tiếp tục với các dấu phân tách nhỏ hơn (như `\n`, `. `) cho đến khi mỗi chunk đạt được kích thước mong muốn. Cách tiếp cận này cố gắng giữ các khối văn bản có liên quan về mặt ngữ nghĩa lại với nhau.*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Tài liệu pháp lý như Bộ luật Dân sự có cấu trúc rất rõ ràng với các Phần, Chương, Mục, và Điều luật, thường được ngăn cách bởi các tiêu đề và xuống dòng. `RecursiveChunker` là lựa chọn lý tưởng vì nó có thể tận dụng cấu trúc này bằng cách ưu tiên chia cắt tại các dấu xuống dòng kép (`\n\n`), giúp giữ trọn vẹn các điều luật hoặc các đoạn giải thích trong cùng một chunk, từ đó bảo toàn ngữ cảnh pháp lý quan trọng.*

**Code snippet:**
```python
class RecursiveChunker:
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        
        if not remaining_separators:
            return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        sep = remaining_separators[0]
        new_remaining = remaining_separators[1:]

        if sep == "" or sep not in current_text:
            return self._split(current_text, new_remaining)

        final_chunks = []
        parts = current_text.split(sep)
        
        for part in parts:
            if not part:
                continue
            
            if len(part) <= self.chunk_size:
                final_chunks.append(part)
            else:
                final_chunks.extend(self._split(part, new_remaining))
                
        return final_chunks

### So Sánh: Strategy của tôi vs Baseline

Dựa trên phân tích cơ sở, tôi chọn `FixedSizeChunker` làm chiến lược baseline tốt nhất vì sự đơn giản và kích thước chunk đồng đều của nó. Đối với "chiến lược của tôi", tôi sẽ sử dụng `RecursiveChunker` như đã được triển khai trong `main.py`. Đây là một chiến lược nâng cao hơn, hứa hẹn sẽ cải thiện chất lượng retrieval.

| Tài liệu                      | Strategy                       | Số lượng chunk | Kích thước trung bình | Chất lượng Retrieval (Dự kiến) |
| :---------------------------- | :----------------------------- | :------------- | :-------------------- | :------------------------------ |
| Tài liệu Bộ luật DS 2015.md | **Best Baseline** (Fixed-Size) | 149            | 994.77                | Khá                             |
| Tài liệu Bộ luật DS 2015.md | **Của tôi** (Recursive)        | 686            | 203.60                | Tốt hơn                        |

**Phân tích:**

Chiến lược baseline (`FixedSizeChunker`) tạo ra các chunk lớn và đồng đều. Điều này đảm bảo mỗi chunk chứa nhiều thông tin, nhưng cũng có nguy cơ cao bị cắt ngang ngữ cảnh (ví dụ: cắt giữa một điều luật), làm cho nội dung của chunk trở nên khó hiểu và nhiễu.

Ngược lại, "chiến lược của tôi" (`RecursiveChunker`) thông minh hơn. Nó cố gắng chia văn bản dựa trên các dấu hiệu ngữ nghĩa tự nhiên như xuống dòng, dấu chấm câu. Kết quả là tạo ra nhiều chunk nhỏ hơn (trung bình 203 ký tự) nhưng mỗi chunk lại tập trung vào một ý hoặc một đoạn văn cụ thể.

**Giả thuyết của tôi là:** các chunk nhỏ và tập trung này sẽ cải thiện đáng kể chất lượng retrieval. Khi người dùng truy vấn, hệ thống sẽ dễ dàng tìm thấy một chunk nhỏ chứa chính xác câu trả lời với điểm tương đồng cao, thay vì một chunk lớn chứa cả câu trả lời và rất nhiều thông tin không liên quan làm loãng tín hiệu. Việc kiểm chứng giả thuyết này sẽ được trình bày trong phần "Kết quả".

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Bình Minh | `LegalChunker` | 8/10 | Regex bám rất sát cấu trúc luận điểm pháp lý, giữ được các cụm “Thứ nhất”, “Tình huống”, heading La Mã | Chunk khá lớn (`1500` ký tự) nên có lúc giảm độ chính xác ở câu hỏi cần đúng điều khoản nhỏ |
| Trần Quốc Việt | `LegalDocumentChunker` (structure-aware + hybrid fallback) | 0/10 | Thiết kế hợp domain, có fallback fixed-size + overlap và mô tả giải pháp khá rõ | Benchmark thực tế trong file cho `4/5` query relevant top-3, retrieval lệch nhiều so với gold answer |
| Nguyễn Việt Hoàng | `LegalArticleChunker` / `VietnameseLegalChunker` định hướng article-aware | 9/10 | Kết quả định lượng tốt nhất trong nhóm, `5/5` top-3 relevant, giữ tốt ranh giới Điều/Khoản | Vẫn có query mà top-1 chưa phải chunk tối ưu nhất, đặc biệt với Điều 295 |
| Lê Quang Minh | Chunk nhỏ + real embeddings `text-embedding-3-small` | Không ghi rõ trong file | Dùng embedding thật, nạp `739` chunks nên semantic matching tốt hơn mock embedding | File chỉ có log truy vấn và chưa có bảng benchmark tổng kết, nên khó so sánh định lượng trực tiếp |
| Ngô Quang Phúc | `LegalDocumentChunker` | 8/10 | Chunk trực tiếp theo Điều/Chương, metadata filter hiệu quả, benchmark đạt `4/5` query thành công | Không dùng real embeddings, query khó không có filter còn yếu; chỉ có `5` chunk nên độ phủ chi tiết hạn chế |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> Nếu xét theo số liệu rõ ràng trong file nhóm, strategy của Nguyễn Việt Hoàng cho kết quả tốt nhất vì đạt `5/5` câu có chunk relevant trong top-3 và tổng điểm retrieval `9/10`, đồng thời vẫn giữ được ngữ cảnh pháp lý trọn vẹn. Tuy vậy, nhóm cũng rút ra rằng không chỉ chunking quyết định kết quả: metadata filtering của Ngô Quang Phúc và embedding thật của Lê Quang Minh đều cho thấy hiệu quả rất rõ khi truy vấn các câu hỏi pháp lý cụ thể. Vì thế, hướng tốt nhất cho domain này là kết hợp structure-aware chunking với metadata và một embedding backend tốt.

---
```

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Tôi sử dụng biểu thức chính quy (regex) `(?<=[.!?])(?:\s+|\n)` để tách văn bản thành các câu. Regex này tìm kiếm các dấu chấm câu `.`, `!`, `?` theo sau là một hoặc nhiều khoảng trắng hoặc dấu xuống dòng. Cách này giúp xử lý tốt các trường hợp câu kết thúc ở cuối đoạn văn.*

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Thuật toán hoạt động bằng cách thử chia văn bản với một danh sách các dấu phân tách theo thứ tự ưu tiên. Nếu một đoạn văn bản sau khi chia vẫn lớn hơn `chunk_size`, hàm sẽ gọi lại chính nó (`_split`) trên đoạn văn bản đó với các dấu phân tách còn lại. Điểm dừng (base case) của đệ quy là khi đoạn văn bản nhỏ hơn `chunk_size` hoặc khi không còn dấu phân tách nào để thử.*

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Các tài liệu được lưu trữ trong một danh sách (list) các dictionary trong bộ nhớ. Mỗi khi một tài liệu được thêm vào, hàm `_embedding_fn` sẽ được gọi để tạo vector và lưu cùng với nội dung và metadata. Hàm `search` tính toán cosine similarity (thông qua tích vô hướng `_dot`) giữa vector của câu truy vấn và tất cả các vector trong store, sau đó sắp xếp và trả về top-k kết quả có điểm cao nhất.*

**`search_with_filter` + `delete_document`** — approach:
> *`search_with_filter` hoạt động bằng cách lọc trước danh sách tài liệu dựa trên `metadata_filter` để tạo ra một danh sách ứng viên. Sau đó, quá trình tìm kiếm tương tự như `search` được thực hiện trên danh sách ứng viên này. `delete_document` tìm và loại bỏ các tài liệu có `doc_id` khớp với giá trị được cung cấp trong metadata.*

### KnowledgeBaseAgent

**`answer`** — approach:
> *Cấu trúc của prompt rất đơn giản: nó bao gồm một phần "Context:" và một phần "Question:". Để đưa context vào, tôi lấy `top_k` chunk liên quan nhất từ `EmbeddingStore`, nối chúng lại với nhau bằng dấu xuống dòng, và đặt vào phần "Context:". Sau đó, prompt hoàn chỉnh được gửi đến hàm `_llm_fn` để tạo câu trả lời.*

### Test Results
============================ test session starts 
============================== ... collected 42 items

tests/test_solution.py .......................................... [100%]

============================== 42 passed in 12.66s ==============================

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|---|---|---|---|---|---|
| 1 | "Thế chấp tài sản là gì?" | "Quy định về việc dùng tài sản để bảo đảm thực hiện nghĩa vụ." | high | 0.85 | ✔️ |
| 2 | "Hiệu lực đối kháng với người thứ ba." | "Quyền truy đòi tài sản bảo đảm của bên nhận bảo đảm." | high | 0.79 | ✔️ |
| 3 | "Bồi thường thiệt hại ngoài hợp đồng." | "Trách nhiệm do vi phạm hợp đồng." | medium | 0.65 | ✔️ |
| 4 | "Thời hiệu khởi kiện về hợp đồng." | "Thủ tục đăng ký kết hôn." | low | 0.11 | ✔️ |
| 5 | "Quy định về lãi suất trong hợp đồng vay." | "Cách tính thuế thu nhập cá nhân." | low | 0.08 | ✔️ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Kết quả cặp 3 khá thú vị. Mặc dù cả hai câu đều nói về "trách nhiệm" và "thiệt hại", mô hình embedding vẫn có thể phân biệt được sự khác biệt ngữ cảnh quan trọng giữa "ngoài hợp đồng" và "vi phạm hợp đồng", cho ra điểm số ở mức trung bình thay vì cao. Điều này cho thấy khả năng biểu diễn ngữ nghĩa tinh vi của embedding.*

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`.

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Thứ tự ưu tiên thanh toán giữa các bên cùng nhận bảo đảm được xác định như thế nào theo Điều 308 BLDS 2015? | Thứ tự được xác định theo thứ tự xác lập hiệu lực đối kháng. |
| 2 | BLDS 2015 quy định bao nhiêu biện pháp bảo đảm thực hiện nghĩa vụ? | 9 biện pháp: cầm cố, thế chấp, đặt cọc, ký cược, ký quỹ, bảo lưu quyền sở hữu, bảo lãnh, tín chấp, cầm giữ tài sản. |
| 3 | Hiệu lực đối kháng với người thứ ba của biện pháp bảo đảm phát sinh khi nào? | Từ khi đăng ký biện pháp bảo đảm hoặc bên nhận bảo đảm nắm giữ/chiếm giữ tài sản bảo đảm. |
| 4 | Cầm giữ tài sản là gì? | Là việc bên có quyền đang nắm giữ hợp pháp tài sản là đối tượng của hợp đồng song vụ được chiếm giữ tài sản khi bên có nghĩa vụ không thực hiện đúng nghĩa vụ. |
| 5 | Việc định giá tài sản bảo đảm được quy định như thế nào? | Do các bên thỏa thuận hoặc thông qua tổ chức định giá, phải đảm bảo khách quan, phù hợp giá thị trường. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thứ tự ưu tiên thanh toán giữa các bên cùng nhận bảo đảm được xác định như thế nào theo Điều 308 BLDS 2015? | "...trường hợp các biện pháp bảo đảm đều phát sinh hiệu lực đối kháng với người thứ ba thì thứ tự thanh toán được xác định theo thứ tự xác lập hiệu lực đối kháng..." | 0.731 | ✔️ | Agent trích dẫn đúng nội dung của Điều 308, giải thích rằng thứ tự ưu tiên dựa trên thứ tự xác lập hiệu lực đối kháng. |
| 2 | BLDS 2015 quy định bao nhiêu biện pháp bảo đảm thực hiện nghĩa vụ? | "Điều 292 BLDS 2015 quy định các biện pháp bảo đảm thực hiện nghĩa vụ bao gồm: cầm cố tài sản; thế chấp tài sản; đặt cọc; ký cược; ký quỹ; bảo lưu quyền sở hữu; bảo lãnh; tín chấp và cầm giữ tài sản." | 0.815 | ✔️ | Agent liệt kê chính xác 9 biện pháp bảo đảm được quy định tại Điều 292. |
| 3 | Hiệu lực đối kháng với người thứ ba của biện pháp bảo đảm phát sinh khi nào? | "Biện pháp bảo đảm phát sinh hiệu lực đối kháng với người thứ ba từ khi đăng ký biện pháp bảo đảm hoặc bên nhận bảo đảm nắm giữ hoặc chiếm giữ tài sản bảo đảm." | 0.789 | ✔️ | Agent trả lời đúng, trích dẫn từ Điều 297 về hai căn cứ phát sinh hiệu lực đối kháng. |
| 4 | Cầm giữ tài sản là gì? | "...cầm giữ tài sản là việc bên có quyền( sau đây gọi là bên cầm giữ) đang nắm giữ hợp pháp tài sản là dối tượng của hợp đồng song vụ được chiếm giữ tài sản trong trường hợp bên có nghĩa vụ không thực hiện hoặc thực hiện không đúng nghĩa vụ." | 0.852 | ✔️ | Agent định nghĩa chính xác về "cầm giữ tài sản" dựa trên nội dung của Điều 346. |
| 5 | Việc định giá tài sản bảo đảm được quy định như thế nào? | "Bên bảo đảm và bên nhận bảo đảm có quyền thỏa thuận về giá tài sản bảo đảm hoặc định giá thông qua tổ chức định giá tài sản khi xử lý tài sản bảo đảm..." | 0.755 | ✔️ | Agent giải thích rõ ràng về quyền thỏa thuận hoặc định giá qua tổ chức thứ ba theo Điều 306. |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 5 / 5

**Ghi chú quan trọng:** *Sau khi chuyển từ `mock embeddings` sang `text-embedding-3-small` của OpenAI và áp dụng `RecursiveChunker`, chất lượng truy xuất đã tăng lên đáng kể. Các điểm số similarity cao và các chunk được trả về đều rất liên quan, cho thấy tầm quan trọng của việc chọn mô hình embedding và chiến lược chunking phù hợp với domain.*

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ quá trình này:**
> *Tôi đã học được rằng chất lượng của một hệ thống RAG không chỉ phụ thuộc vào LLM mà phụ thuộc rất lớn vào giai đoạn "Retrieval". Việc lựa chọn mô hình embedding phù hợp và một chiến lược chunking thông minh để giữ lại ngữ cảnh là hai yếu tố quyết định để hệ thống có thể tìm thấy đúng thông tin và đưa ra câu trả lời chính xác.*

**Thử thách lớn nhất gặp phải:**
> *Thử thách lớn nhất là xử lý lỗi "maximum context length" của OpenAI khi làm việc với một tài liệu lớn như Bộ luật Dân sự. Điều này buộc tôi phải tìm hiểu sâu và áp dụng `RecursiveChunker` một cách hiệu quả để chia nhỏ tài liệu mà không làm mất đi tính toàn vẹn của các điều luật.*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Nếu làm lại, tôi sẽ thử nghiệm kỹ hơn với các tham số của `RecursiveChunker` (ví dụ: `chunk_size` và `separators`) để tối ưu hóa việc giữ ngữ cảnh cho các điều luật phức tạp. Ngoài ra, tôi cũng sẽ nghiên cứu cách thêm metadata ở cấp độ chunk (ví dụ: tự động gán số hiệu điều luật cho mỗi chunk) để hỗ trợ việc lọc và truy vấn chính xác hơn nữa.*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5 / 5 |
| Document selection | Nhóm | 8/ 10 |
| Chunking strategy | Nhóm | 12 / 15 |
| My approach | Cá nhân | 8 / 10 |
| Similarity predictions | Cá nhân | 4 / 5 |
| Results | Cá nhân | 9 / 10 |
| Core implementation (tests) | Cá nhân | 30 / 30 |
| Demo | Nhóm | 4 / 5 |
| **Tổng** | | **80 / 90  |