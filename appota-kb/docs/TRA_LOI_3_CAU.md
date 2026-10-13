# Trả lời 3 câu hỏi bắt buộc (bản nháp, hãy đọc lại và chỉnh theo trải nghiệm của bạn)

## 1. Phần quan trọng nhất được hiện thực hóa và vì sao
Mình chọn **lọc quyền, đơn vị và phiên bản bằng code trước khi tài liệu tới LLM**, rồi mới retrieval và trả lời có nguồn.

Lý do: ở Mission 1 mình xác định tìm kiếm văn bản không còn là điểm khó, vì có nhiều giải pháp có sẵn. Điểm khó là mỗi người chỉ nhận tri thức đúng phạm vi và đang có hiệu lực. Nếu tài liệu ngoài quyền hoặc bản cũ lọt vào prompt thì dù LLM giỏi đến đâu cũng không cứu được, còn nếu lọc đúng trước thì LLM chỉ còn việc diễn đạt.

Bằng chứng giải pháp khả thi: với cùng câu hỏi nghỉ phép, An (Công ty B) nhận quy định 14 ngày kèm đối chiếu mức chung, Bình (Công ty C) nhận quy định chung 12 ngày và prompt của Bình không chứa chữ nào của Công ty B (test T1, và unit test kiểm tra nội dung prompt). Nội dung lương Ban Giám đốc không bao giờ xuất hiện trong prompt của người không đủ quyền (T2, T6).

## 2. Thay đổi so với Mission 1 và lý do
- **Bỏ "LLM rerank độ ưu tiên", thay bằng quy tắc xác định** (cấp cụ thể hơn thắng, cùng cấp thì bản mới hơn, cùng cấp cùng ngày khác nội dung thì báo mâu thuẫn). Lý do: quyết định ưu tiên cần giải thích và kiểm thử lặp lại được; để LLM xếp hạng thì khó kiểm chứng. LLM chỉ còn diễn đạt và nêu khác biệt.
- **Thay Vector DB bằng BM25 trong bộ nhớ.** Lý do: dữ liệu chỉ 11 tài liệu, và MVP cần chứng minh lọc quyền chứ không phải khả năng mở rộng. Cái giá là T10: "tăng ca" không khớp "OT".
- **Giả lập hồ sơ người dùng thay cho SSO/IAM**, chọn trong dropdown, vì ngoài phạm vi MVP.
- **Thêm ngữ cảnh người hỏi vào prompt.** Ở bản đầu, prompt chỉ có tài liệu nên khi An hỏi về OT, câu trả lời mở đầu bằng "Nếu bạn thuộc phòng Marketing...", nghe như đang đoán dù hệ thống đã biết An thuộc Marketing. Mình phát hiện khi xem câu trả lời thật trên giao diện, sau đó thêm khối thông tin người hỏi vào prompt và thêm test.
- **Thêm kiểm tra đầu ra bằng code** (nguồn bịa, nhắc tới tài liệu ngoài quyền, thiếu trích dẫn) và **từ chối trước khi gọi LLM** khi không có tài liệu phù hợp. Mission 1 mới chỉ dựa vào prompt để chống bịa; mình thấy cần chốt chặn bằng code.
- **Siết ngưỡng khớp từ khóa từ 50% lên 60%.** Khi chạy thử, hỏi lương Tổng Giám đốc khiến Bình nhận nhầm tài liệu laptop (chỉ trùng chữ "Giám đốc"), và câu "Mức phạt" kéo cả tài liệu nghỉ phép/OT vì trùng chữ "mức".

## 3. Trường hợp dễ trả lời sai nhất và cách phát hiện, kiểm soát
Trường hợp rủi ro nhất mình thấy trong lúc làm:

1. **Quy định riêng chỉ ghi đè một phần quy định chung (T11).** Hỏi "OT được trả bao nhiêu tiền?", An chỉ nhận tài liệu Marketing và mất toàn bộ tỷ lệ 150/200/300% của Tập đoàn. Hệ thống coi "riêng thay thế chung" trong khi thực tế thường chỉ ghi đè một điều khoản. Mình phát hiện bằng cách thử nhiều cách diễn đạt của cùng một ý và thấy kết quả đổi theo cách hỏi (có cách hỏi lấy đủ hai tài liệu chỉ vì trùng chữ "tính chất"). Đã ghi lại thành test chưa đạt; hướng sửa là luôn đưa kèm mọi tài liệu cùng chủ đề trong phạm vi quyền.
2. **Câu hỏi mơ hồ (T9) và đồng nghĩa (T10).** Hệ thống tự đoán chủ đề khi hỏi "Phạt bao nhiêu?", và không hiểu "tăng ca" là "OT". Cả hai được giữ nguyên làm test chưa đạt thay vì sửa cho đẹp.
3. **Metadata sai do con người** (gán nhầm `status`, `owner_unit`...). Mình kiểm soát một phần bằng cách validate khi nạp (thiếu trường, sai giá trị thì không nạp và báo lỗi) và có test cho loader. Chưa kiểm tra được metadata "hợp lệ nhưng sai".
4. **Prompt injection.** Rủi ro bị giảm vì dữ liệu ngoài quyền không có trong prompt (T6). Chưa thử trường hợp chỉ dẫn độc hại nằm trong nội dung tài liệu.

Cách phát hiện chung: chế độ debug hiển thị tài liệu bị loại kèm lý do, điểm BM25 và prompt thật; bộ test tự động chạy lại mỗi khi sửa.

> Sau khi chạy `python tests/run_tests.py --live` với Gemini thật, hãy bổ sung ở đây những gì bạn thấy ở lời văn câu trả lời (Gemini có nêu đủ cả hai mức 50.000/100.000 ở T7 không, có lần nào trích nguồn sai không...).
