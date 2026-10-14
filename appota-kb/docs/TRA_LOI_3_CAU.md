# Trả lời 3 câu hỏi

## 1. Phần quan trọng nhất được hiện thực hóa và vì sao
Em chọn **lọc quyền, đơn vị và phiên bản bằng code trước khi tài liệu tới LLM**, rồi mới retrieval và trả lời có nguồn.

Lý do: ở Mission 1 đã xác định tìm kiếm văn bản không còn là điểm khó, vì có nhiều giải pháp có sẵn. Điểm khó là mỗi người chỉ nhận tri thức đúng phạm vi và đang có hiệu lực. Nếu tài liệu ngoài quyền hoặc bản cũ lọt vào prompt thì dù LLM có tốt đến đâu cũng không sửa được, còn nếu lọc đúng trước thì LLM chỉ còn việc diễn đạt.

Bằng chứng giải pháp khả thi: với cùng câu hỏi nghỉ phép, An (Công ty B) nhận quy định 14 ngày kèm đối chiếu mức chung, Bình (Công ty C) nhận quy định chung 12 ngày và prompt của Bình không chứa thông tin nào của Công ty B. Nội dung lương Ban Giám đốc không bao giờ xuất hiện trong prompt của người không đủ quyền (T2, T6).

## 2. Thay đổi so với Mission 1 và lý do
- **Bỏ "LLM rerank độ ưu tiên", thay bằng quy tắc xác định** (cấp cụ thể hơn thì chọn, cùng cấp thì bản mới hơn, cùng cấp cùng ngày khác nội dung thì báo mâu thuẫn). Lý do: quyết định ưu tiên cần giải thích và kiểm thử lặp lại được, để LLM xếp hạng thì khó kiểm chứng. LLM chỉ có nhiệm vụ diễn đạt và nêu khác biệt.
- **Thay Vector DB bằng BM25 trong bộ nhớ.** Lý do: dữ liệu chỉ 11 tài liệu, và MVP cần chứng minh lọc quyền chứ không phải khả năng mở rộng. Hạn chế: "tăng ca" không khớp "OT".
- **Giả lập hồ sơ người dùng thay cho SSO/IAM**, chọn trong dropdown, vì ngoài phạm vi MVP.
- **Thêm ngữ cảnh người hỏi vào prompt.** Ở bản đầu, prompt chỉ có tài liệu nên khi An hỏi về OT, câu trả lời mở đầu bằng "Nếu bạn thuộc phòng Marketing...", dù hệ thống đã biết An thuộc Marketing. Phát hiện khi xem câu trả lời thật trên giao diện, sau đó thêm khối thông tin người hỏi vào prompt và thêm test.
- **Thêm kiểm tra đầu ra bằng code** (nguồn bịa, nhắc tới tài liệu ngoài quyền, thiếu trích dẫn) và **từ chối trước khi gọi LLM** khi không có tài liệu phù hợp. Mission 1 mới chỉ dựa vào prompt để chống bịa cần chốt chặn bằng code.
- **Tăng khớp từ khóa từ 50% lên 60%.** Khi chạy thử, người dùng hỏi lương Tổng Giám đốc khiến Bình nhận nhầm tài liệu, và câu "Mức phạt" kéo cả tài liệu nghỉ phép/OT vì trùng chữ "mức".

## 3. Trường hợp dễ trả lời sai nhất và cách phát hiện, kiểm soát
Trường hợp rủi ro nhất mình thấy trong lúc làm:

1. **Quy định riêng chỉ thay đổi một số nội dung của quy định chung (T11).** Ví dụ, quy định Marketing giới hạn OT tối đa 30 giờ và yêu cầu duyệt trước, còn quy định Tập đoàn nêu mức trả OT ngày thường, cuối tuần và ngày lễ. Hệ thống xếp hạng cả tài liệu, không phân biệt rõ điều khoản nào được thay đổi. Vì vậy, tùy cách đặt câu hỏi, hệ thống có thể chỉ lấy quy định Marketing và bỏ sót mức trả OT chung, hoặc lấy cả hai tài liệu. Đã ghi trường hợp này thành test chưa đạt. Hướng xử lý là luôn đưa các tài liệu cùng chủ đề mà người hỏi được phép xem vào kết quả, rồi làm rõ nội dung nào của quy định chung vẫn áp dụng.
2. **Câu hỏi mơ hồ (T9) và đồng nghĩa (T10).** Hệ thống tự đoán chủ đề khi hỏi "Phạt bao nhiêu?", và không hiểu "tăng ca" là "OT". Cả hai được giữ nguyên làm test chưa đạt thay vì sửa cho đẹp.
3. **Metadata sai do con người** (gán nhầm `status`, `owner_unit`...). Kiểm soát một phần bằng cách validate khi nạp (thiếu trường, sai giá trị thì không nạp và báo lỗi) và có test cho loader. Chưa kiểm tra được metadata "hợp lệ nhưng sai".
4. **Prompt injection.** Rủi ro bị giảm vì dữ liệu ngoài quyền không có trong prompt (T6). 

Cách phát hiện chung: chế độ debug hiển thị tài liệu bị loại kèm lý do, điểm BM25 và prompt thật, bộ test tự động chạy lại mỗi khi sửa.
