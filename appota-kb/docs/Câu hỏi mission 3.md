# Trả lời 3 câu hỏi Mission 3

## 1. Sau khi nhận yêu cầu mới, bạn đã ưu tiên thay đổi điều gì và chủ động chưa làm điều gì? Vì sao?

Em ưu tiên sửa các quy tắc có thể làm hệ thống trả lời sai hoặc lộ nhầm phạm vi. Cụ thể, em cập nhật lọc tổ chức để so khớp đường dẫn tập đoàn → công ty → phòng ban → nhóm, đồng thời giữ tương thích với hồ sơ cũ chỉ có danh sách `units`. Hệ thống vẫn kiểm tra `access_level` và `allowed_positions` trước khi retrieval, tài liệu khác tập đoàn không được cấp quyền chỉ vì tên công ty trùng.

Với thời điểm áp dụng, tài liệu chỉ được dùng nếu `effective_date` đã đến và `expiry_date` chưa qua tại ngày được hỏi. Em thêm tài liệu giả lập nghỉ phép `LEAVE-GROUP-v3-2027`, hiệu lực từ 01/01/2027 và thay thế v2: khi hỏi theo ngày hiện tại, v3 không vào nguồn trả lời nhưng hệ thống báo tài liệu này sắp có hiệu lực, khi hỏi về năm 2027, hệ thống có thể chọn v3. Khi nhiều tài liệu cùng cấp, hệ thống ưu tiên ngày hiệu lực mới hơn, nếu ngày này bằng nhau thì xét ngày hết hạn xa hơn. Nếu metadata vẫn không phân định được thì giữ trạng thái mâu thuẫn để nêu các nguồn, không tự đoán.

Em cũng làm rõ yêu cầu trích dẫn: prompt yêu cầu câu trả lời mở đầu theo dạng “Theo tài liệu…”, nêu mã/tên tài liệu, phiên bản, mục và trang nếu có. Giao diện hiển thị file, mục và đoạn trích, PDF dùng số trang trích xuất, còn Markdown ghi trang không áp dụng thay vì tạo số trang giả. Câu hỏi thiếu chủ đề như “Phạt bao nhiêu?” vẫn được yêu cầu làm rõ trước khi gọi LLM.

Em chưa triển khai SSO/IAM vì MVP hiện dùng người dùng và tài liệu giả lập. Em cũng chưa thay BM25 bằng vector search, phần synonym hiện có đã giúp truy vấn “tăng ca” tìm được tài liệu OT và được kiểm tra bằng test. Đây là lựa chọn để giới hạn phạm vi thay đổi, giữ hành vi tìm kiếm hiện tại và tập trung xử lý quyền, hiệu lực, phiên bản, mâu thuẫn và nguồn kiểm chứng trước.

## 2. Thay đổi nào tạo ra khác biệt lớn nhất giữa sản phẩm Mission 2 và Mission 3? Bạn dùng bằng chứng nào để kết luận phiên bản mới tốt hơn?

Khác biệt lớn nhất là câu trả lời có căn cứ rõ hơn theo thời điểm và toàn bộ nguồn liên quan trong phạm vi quyền. Mission 2 có thể bỏ tài liệu Tập đoàn khi câu hỏi về tiền OT khớp tài liệu Marketing hơn, cải tiến ở Mission 3 xác định chủ đề từ kết quả tìm kiếm rồi đưa cả tài liệu liên quan tới OT Marketing và OT Tập đoàn vào prompt, nhưng vẫn lọc quyền trước. Bản có ngày hiệu lực trong tương lai bị loại, bản mới nhất ở cùng cấp được chọn thay cho bản cũ. Câu hỏi mơ hồ được yêu cầu làm rõ trước khi gọi LLM.

Bằng chứng hiện có:

- T11 của bộ Mission 2: prompt phải có cả `OT-MKT-v1` và `OT-GROUP-v1`, bao gồm nội dung 150% và nghỉ bù.
- Test Mission 3 kiểm tra tài liệu tương lai không được phép, trường hợp câu hỏi mơ hồ không gọi LLM, nội dung nguồn kiểm chứng được, bản cũ cùng cấp không thành nguồn, và hồi quy quyền nghỉ phép của An/Bình.
- Bộ kiểm thử Mission 2 chạy lại ở chế độ offline để kiểm tra các hành vi xác định, gồm quyền, từ chối, phiên bản, mâu thuẫn và prompt.


## 3. Nếu sản phẩm này được đưa cho người dùng thật vào ngày mai, rủi ro hoặc giới hạn lớn nhất còn lại là gì? Bạn sẽ ưu tiên xử lý nó như thế nào?

Rủi ro lớn nhất là hệ thống dựa vào metadata do con người gán và mô hình quy tắc ưu tiên theo toàn tài liệu. Metadata hợp lệ về cú pháp vẫn có thể sai thực tế, quy định riêng có thể chỉ thay một vài điều khoản, trong khi hệ thống chưa hiểu điều khoản nào của quy định chung còn áp dụng. Do sử dụng thuật toán BM25 tìm tài liệu tương đồng nên cũng chưa bao quát được những từ đồng nghĩa.

Em sẽ ưu tiên xây dựng quy trình quản trị tài liệu có chủ sở hữu phê duyệt: lưu lịch sử phiên bản và ngày bắt đầu/kết thúc hiệu lực; kiểm tra chéo metadata và quyền trước khi phát hành; đồng thời chia tài liệu theo điều khoản và ghi rõ điều khoản nào bị thay thế. Sau đó, em sẽ cải thiện retrieval bằng embedding để tìm được các câu hỏi và tài liệu diễn đạt khác nhau nhưng cùng nghĩa, chẳng hạn “tăng ca” và “OT”. Em ưu tiên mô hình hybrid: kết hợp điểm BM25 với điểm tương đồng vector, rồi áp dụng bộ lọc quyền và ngày hiệu lực trước khi đưa kết quả vào LLM. Em sẽ đánh giá bằng các cặp câu hỏi đồng nghĩa và các câu hỏi không liên quan để đo recall lẫn kết quả sai; embedding chỉ giúp tìm ứng viên, không xác nhận tài liệu đúng, còn hiệu lực hay được phép xem. Cuối cùng, em sẽ tích hợp IAM thật và kiểm thử trên dữ liệu đã được phân loại trước khi triển khai rộng.

## Before → After

| Bước | Mission 2 → Mission 3 |
|---|---|
| M2 — Trước cải tiến | Có lọc đơn vị/cấp, trạng thái active/archived, retrieval BM25 và nguồn trích dẫn; ngày hiệu lực tương lai chưa bị loại, T11 có thể bỏ sót quy định chung, câu hỏi “Phạt bao nhiêu?” bị đoán thành chủ đề đi muộn. |
| Vấn đề/yêu cầu mới | Ngày có hiệu lực phải được tôn trọng; người dùng phải kiểm soát truy cập và mâu thuẫn; thiếu căn cứ cần từ chối/làm rõ; nguồn phải kiểm chứng được. |
| Quyết định thay đổi gì / không thay đổi gì | Lọc ngày hiệu lực trước retrieval; chọn bản mới nhất trong từng cấp và chỉ cảnh báo xung đột ở cấp ưu tiên; lấy các tài liệu cùng topic đã qua lọc quyền; làm rõ câu hỏi chỉ gồm từ khái quát; hiển thị nội dung nguồn. Giữ nguyên BM25 và hồ sơ user giả lập; chưa chọn Change Request khi chưa có yêu cầu được duyệt. |
| M3 — Sau cải tiến | Ngày tương lai không vào retrieval; phiên bản cũ cùng cấp không còn là nguồn; tài liệu chung và riêng cùng chủ đề được cung cấp; câu hỏi mơ hồ không gọi LLM; người dùng mở xem nội dung nguồn. |
| Bằng chứng cho thấy tốt hơn | Test mới trong `tests/test_mission3.py`, cùng bộ test offline Mission 2 đã cập nhật kỳ vọng cho hỏi làm rõ và trường hợp T11. |
| Giới hạn còn lại | Change Request và test tương ứng đang chờ chỉ định; kết quả live chưa chạy lại; đồng nghĩa “tăng ca” vẫn chưa được BM25 xử lý; chưa có IAM, phê duyệt metadata hay phân tích xung đột theo điều khoản. |

## Video và bản chạy thử

- Link Mission 3: chưa được deploy trong phiên làm việc này.
- Video cải tiến ≤5 phút: chưa được tạo; kịch bản đề xuất: (1) nêu yêu cầu/nguyên nhân, (2) so sánh T11 và ngày hiệu lực trước/sau, (3) mở nguồn để kiểm chứng, (4) minh họa câu hỏi mơ hồ được làm rõ, (5) nêu Change Request đang chờ và giới hạn còn lại.
