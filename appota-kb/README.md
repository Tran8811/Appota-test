# Tri thức nội bộ Appota: Mission 3

Phiên bản cập nhật Mission 3 của MVP **Bài test B**. Toàn bộ dữ liệu là **giả lập**, không dùng dữ liệu thật của Appota.

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
     sai đơn vị / vượt cấp / archived / chưa tới ngày hiệu lực  →  loại
        │ tài liệu được phép
        ▼
 [2] Retrieval BM25 + ngưỡng (kb/retrieve.py)
     câu hỏi mơ hồ  →  LÀM RÕ; không đủ căn cứ  →  TỪ CHỐI
        │
        ▼
 [3] Chọn bản ưu tiên bằng quy tắc xác định
     team > phòng > công ty > tập đoàn; mỗi cấp chỉ lấy bản mới nhất;
     đồng hạng ở cấp ưu tiên  →  CONFLICT
        │
        ▼
 [4] LLM (Gemini) diễn đạt, nêu khác biệt riêng/chung, trích [doc_id]
        │
        ▼
 [5] Hiển thị metadata + nội dung nguồn để người dùng kiểm chứng
     kiểm tra đầu ra bằng code: nguồn bịa, tài liệu ngoài quyền, thiếu trích dẫn
```

## Cấu trúc thư mục
```
data/            12 tài liệu Markdown và 1 PDF giả lập (PDF có sidecar .pdf.yaml)
users.json       4 người dùng giả lập (thay cho SSO/IAM)
kb/loader.py     đọc tài liệu, kiểm tra metadata (file lỗi bị bỏ qua và báo)
kb/access.py     lọc quyền + phiên bản + ngày hiệu lực
kb/retrieve.py   BM25, làm rõ câu hỏi mơ hồ, ưu tiên, phát hiện mâu thuẫn
kb/answer.py     prompt, gọi Gemini, kiểm tra đầu ra
app.py           giao diện Streamlit (có chế độ debug)
tests/           unit test + bộ kiểm thử Mission 2 và Mission 3
results/         kết quả kiểm thử
docs/            Before/After, trả lời 3 câu hỏi và kịch bản video
```

## Trích dẫn nguồn

Markdown chứa nội dung văn bản và heading, tiện sửa nhưng không có phân trang ổn định; citation dùng tên mục và trích đoạn. PDF giữ bố cục và số trang cố định; loader đọc PDF cùng sidecar `.pdf.yaml` để giữ metadata và trích số trang thực. Repo có `chi_phi_cong_tac_demo.pdf` một trang để thử citation trang 1. PDF nhiều trang hiện chưa được hỗ trợ trong demo.

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
python -m unittest discover -s tests -t .
python tests/run_tests.py --offline            # chạy lại 12 tình huống Mission 2, không gọi Gemini
```
Test Mission 3: `python -m unittest tests.test_mission3`. Bộ test Mission 3 bổ sung kiểm tra ngày hiệu lực, nguồn cùng chủ đề khi có ghi đè một phần, câu hỏi mơ hồ, khả năng kiểm chứng nguồn và regression quyền theo user.

Kết quả offline Mission 2: `python tests/run_tests.py --offline` (12/12 đạt sau khi bổ sung alias đồng nghĩa OT). Lần chạy live gần nhất không gọi được Gemini do `CERTIFICATE_VERIFY_FAILED`; các ca cần LLM chưa được đánh giá trong kết quả đó.

Test Mission 3 có ba ca được gắn loại rõ ràng: CR-M3-01 ánh xạ trực tiếp yêu cầu ban đầu rằng thiếu/sai ngày hiệu lực phải fail-closed; edge case ngày hết hạn được tính bao gồm hết ngày lịch; regression bảo đảm người dùng Công ty C không thấy quy định Công ty B. Đây là CR theo yêu cầu trong phiên làm việc này, không phải Change Request bên ngoài đã được reviewer phê duyệt.

## Hạn chế đã biết
- **Đồng nghĩa**: "tăng ca" không khớp "OT" (T10). Hướng khắc phục: từ điển đồng nghĩa hoặc embedding đa ngữ.
- **Ghi đè một phần**: Mission 3 giữ cả tài liệu cùng topic trong phạm vi quyền để giảm bỏ sót, nhưng chưa xác định điều khoản nào của quy định chung còn áp dụng.
- **Câu hỏi mơ hồ**: đã làm rõ một số truy vấn chỉ có từ khái quát như “Phạt bao nhiêu?”; đây là heuristic, không phải phân loại ngôn ngữ tổng quát.
- **Metadata do con người gán**: nếu gán sai `status`, `scope` hoặc `owner_unit` thì lọc sẽ sai. MVP chỉ kiểm tra thiếu/sai định dạng, chưa kiểm tra đúng/sai nội dung.
- **Chưa thử indirect injection** (chỉ dẫn nằm trong nội dung tài liệu).
- Mỗi tài liệu là một chunk; dữ liệu rất nhỏ (13 tài liệu); không có Vector DB, SSO/IAM thật, upload tài liệu, hay phản hồi người dùng.
- Danh sách tài liệu bị loại ở chế độ debug chỉ dành cho demo; sản phẩm thật không được hiển thị cho người dùng thường.

## Trạng thái bài nộp
- Repository: phiên bản Mission 3 đang được cập nhật trên cùng repository.
- Link bản chạy thử mới: chưa deploy.
- Video cải tiến ≤5 phút: chưa tạo; nội dung Before/After và kịch bản demo nằm ở `docs/TRA_LOI_3_CAU.md`.
- Ba câu hỏi bắt buộc và giới hạn còn lại: `docs/TRA_LOI_3_CAU.md`.

## Bảo mật
Repo không chứa API key (`.env` nằm trong `.gitignore`). Khi deploy, key đặt trong Streamlit Secrets. Mỗi phiên demo giới hạn 30 câu hỏi để bảo vệ quota.
