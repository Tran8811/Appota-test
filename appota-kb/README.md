# Tri thức nội bộ Appota: MVP "đúng người, đúng phạm vi, đúng phiên bản"

MVP cho **Bài test B, Mission 2**. Toàn bộ dữ liệu là **giả lập**, không dùng dữ liệu thật của Appota.

## Bài toán
Cùng một câu hỏi ("Quy định nghỉ phép của tôi?"), hai nhân sự thuộc hai đơn vị khác nhau phải nhận hai câu trả lời khác nhau, chỉ dựa trên tài liệu họ được phép xem và đang có hiệu lực, kèm nguồn kiểm chứng.

## Phần được chọn để chứng minh
**Lọc quyền, đơn vị và phiên bản bằng code trước khi đưa cho LLM.** Nếu phần này đúng thì hướng giải quyết khả thi: tìm kiếm văn bản đã có nhiều giải pháp, còn rò quyền hoặc lấy nhầm bản cũ thì sản phẩm vô nghĩa. Ở MVP, tài liệu ngoài quyền **không bao giờ xuất hiện trong prompt** gửi cho LLM (có test kiểm tra điều này).

## Kiến trúc

```
Câu hỏi + người dùng (đơn vị, cấp)
        │
        ▼
 [1] Lọc cứng bằng code (kb/access.py)
     sai đơn vị / vượt cấp / hết hiệu lực  →  loại
        │ tài liệu được phép
        ▼
 [2] Retrieval BM25 + ngưỡng (kb/retrieve.py)
     không đủ độ phủ từ khóa  →  TỪ CHỐI (không gọi LLM)
        │
        ▼
 [3] Chọn bản ưu tiên bằng quy tắc xác định
     team > phòng > công ty > tập đoàn; cùng cấp thì bản mới hơn;
     cùng cấp + cùng ngày + khác nội dung  →  CONFLICT
        │
        ▼
 [4] LLM (Gemini) diễn đạt, nêu khác biệt riêng/chung, trích [doc_id]
        │
        ▼
 [5] Kiểm tra đầu ra bằng code: nguồn bịa, tài liệu ngoài quyền, thiếu trích dẫn
```

## Cấu trúc thư mục
```
data/            11 tài liệu giả lập (.md + front-matter metadata)
users.json       4 người dùng giả lập (thay cho SSO/IAM)
kb/loader.py     đọc tài liệu, kiểm tra metadata (file lỗi bị bỏ qua và báo)
kb/access.py     lọc quyền + phiên bản
kb/retrieve.py   BM25, ngưỡng từ chối, ưu tiên, phát hiện mâu thuẫn
kb/answer.py     prompt, gọi Gemini, kiểm tra đầu ra
app.py           giao diện Streamlit (có chế độ debug)
tests/           unit test + bộ kiểm thử Mission 2 (run_tests.py)
results/         kết quả kiểm thử
docs/            trả lời 3 câu hỏi, kịch bản video, checklist nộp bài
```

## Dữ liệu giả lập
Mỗi tài liệu có metadata: `doc_id, title, topic, scope (group/company/dept/team), owner_unit, access_level, status (active/archived), effective_date, supersedes`.

| Tài liệu | Mục đích |
|---|---|
| Nghỉ phép Tập đoàn v1 (archived, 10 ngày) và v2 (12 ngày) | Xử lý phiên bản |
| Nghỉ phép Công ty B (14 ngày) | Quy định riêng đè quy định chung |
| OT Tập đoàn (40 giờ) và OT Marketing (30 giờ) | Quy định cấp phòng |
| Quy chế lương Ban Giám đốc (level 5) | Chặn theo cấp truy cập |
| Quy trình khiếu nại (Nhân sự, level 3) | Chặn theo đơn vị + cấp |
| Hai bản nội quy đi muộn Công ty B (50.000 và 100.000, cùng ngày) | Mâu thuẫn |
| Cấp laptop (Kỹ thuật), thử việc (Tập đoàn) | Tài liệu nhiễu |

## Chạy local
```bash
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
# mở .env và dán GEMINI_API_KEY (lấy miễn phí tại Google AI Studio)
python check_key.py           # kiểm tra key
streamlit run app.py
```
Thử nhanh bằng terminal: `python ask_cli.py an "Quy định nghỉ phép của tôi như thế nào?"`

## Kiểm thử
```bash
python -m unittest discover -s tests -t .      # 37 unit test (1 lỗi đã biết được đánh dấu expectedFailure)
python tests/run_tests.py                      # 12 tình huống Mission 2; tự dùng Gemini nếu có key
python tests/run_tests.py --offline            # chỉ phần xác định bằng code, không gọi Gemini
```
Kết quả: `results/test_results_offline.md` (phần xác định bằng code) và `results/test_results_live.md` (khi chạy với Gemini thật).

Kết quả chế độ offline (12 tình huống): **9 đạt, 3 chưa đạt**.

| # | Tình huống | Kết quả |
|---|---|---|
| T1 | Cùng câu hỏi nghỉ phép, An và Bình | Đạt |
| T2 | Level thấp hỏi lương Tổng Giám đốc | Đạt |
| T3 | Chủ đề không có dữ liệu | Đạt |
| T4 | Bản cũ (archived) không bị dùng | Đạt |
| T5 | Quy định Marketing đè quy định chung | Đạt |
| T6 | Prompt injection | Đạt |
| T7 | Hai bản mâu thuẫn cùng cấp | Đạt |
| T8 | Quyền theo đơn vị và cấp (khiếu nại) | Đạt |
| T9 | Câu hỏi mơ hồ "Phạt bao nhiêu?" | **Chưa đạt**: hệ thống tự đoán chủ đề |
| T10 | Hỏi "tăng ca", tài liệu ghi "OT" | **Chưa đạt**: BM25 không hiểu đồng nghĩa |
| T11 | Hỏi "OT được trả bao nhiêu tiền?" | **Chưa đạt**: mất tài liệu chung vì quy định riêng chỉ ghi đè một phần |

## Hạn chế đã biết
- **Đồng nghĩa**: "tăng ca" không khớp "OT" (T10). Hướng khắc phục: từ điển đồng nghĩa hoặc embedding đa ngữ.
- **Ghi đè một phần**: hệ thống coi quy định riêng thay thế quy định chung, trong khi thực tế thường chỉ ghi đè một điều khoản (T11).
- **Câu hỏi mơ hồ**: không có cơ chế hỏi lại (T9).
- **Kết quả phụ thuộc cách diễn đạt**: một số câu hỏi đạt do trùng từ ngẫu nhiên (ví dụ "Mức phạt là bao nhiêu?" bị từ chối vì chữ "mức" không có trong tài liệu, không phải vì hệ thống nhận ra sự mơ hồ).
- **Metadata do con người gán**: nếu gán sai `status`, `scope` hoặc `owner_unit` thì lọc sẽ sai. MVP chỉ kiểm tra thiếu/sai định dạng, chưa kiểm tra đúng/sai nội dung.
- **Chưa thử indirect injection** (chỉ dẫn nằm trong nội dung tài liệu).
- Mỗi tài liệu là một chunk; dữ liệu rất nhỏ (11 tài liệu); không có Vector DB, SSO/IAM thật, upload tài liệu, hay phản hồi người dùng.
- Danh sách tài liệu bị loại ở chế độ debug chỉ dành cho demo; sản phẩm thật không được hiển thị cho người dùng thường.

## Bảo mật
Repo không chứa API key (`.env` nằm trong `.gitignore`). Khi deploy, key đặt trong Streamlit Secrets. Mỗi phiên demo giới hạn 30 câu hỏi để bảo vệ quota.
