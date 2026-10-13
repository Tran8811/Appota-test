# Kịch bản video (tối đa 5 phút)

Chuẩn bị: mở sẵn app (bật Chế độ debug khi cần), thanh bên hiện rõ người dùng. Quay màn hình, nói thong thả. Tập 1 lần trước khi quay.

| Thời gian | Nội dung | Thao tác trên màn hình |
|---|---|---|
| 0:00–0:40 | **Bài toán**: cùng câu hỏi nhưng mỗi người cần câu trả lời khác nhau, tài liệu có nhiều cấp, nhiều phiên bản. Khó nhất không phải là tìm, mà là tìm đúng phạm vi. | Mở app, chưa thao tác |
| 0:40–1:20 | **Phần chọn để chứng minh**: lọc quyền, đơn vị, phiên bản bằng code trước khi tới LLM. Nói 1 câu về sơ đồ trong README. | Mở sơ đồ trong README |
| 1:20–2:50 | **Demo chính**: chọn An, hỏi "Quy định nghỉ phép của tôi như thế nào?" → 14 ngày kèm đối chiếu 12 ngày. Chọn Bình, hỏi lại → 12 ngày. Bật Debug để cho thấy tài liệu Công ty B bị loại với lý do "sai đơn vị" và bản v1 bị loại vì "đã hết hiệu lực". | Đổi người dùng ở thanh bên, bật Debug |
| 2:50–3:20 | **Quyền và từ chối**: An hỏi "Lương của Tổng Giám đốc là bao nhiêu?" → từ chối. Chọn Giám đốc, hỏi lại → có câu trả lời. Chạy câu injection "Bỏ qua mọi hướng dẫn..." → từ chối. Nhấn mạnh: debug cho thấy không gọi LLM. | Dùng câu hỏi mẫu |
| 3:20–4:00 | **Tình huống khó**: "Đi muộn bị phạt bao nhiêu?" → hệ thống báo hai bản mâu thuẫn, nêu cả 50.000 và 100.000, không tự chọn. | Chọn An |
| 4:00–4:50 | **Thất bại và hạn chế** (nói thật): hỏi "Quy định tăng ca thế nào?" → bị từ chối dù có quy định OT, vì BM25 không hiểu đồng nghĩa. Nêu thêm: ghi đè một phần (T11) và câu hỏi mơ hồ (T9). Cho xem bảng kết quả test (9 đạt, 3 chưa đạt). | Mở results/test_results_*.md |
| 4:50–5:00 | Hướng cải thiện: embedding/từ điển đồng nghĩa, metadata ghi đè từng điều khoản, hỏi lại khi mơ hồ. | |

Mẹo: không đọc nguyên văn kịch bản; nếu Gemini trả lời khác mong đợi trong lúc quay, hãy nói rõ đó là hạn chế và đừng quay lại để giấu (đề cho điểm việc biết hệ thống chưa tốt ở đâu).
