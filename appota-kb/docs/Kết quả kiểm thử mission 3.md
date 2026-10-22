# Báo cáo kiểm thử Mission 3

## Kết luận

- Đã chạy bộ hồi quy quan trọng của Mission 2: **12/12 tình huống đạt** ở chế độ offline.
- Có hơn 3 test cho phần cải tiến. Bộ `test_mission3.py` có 9 test và `test_hardening.py` có 17 test; tổng **26 test đạt**.
- Có test edge case và regression chức năng cũ. Ngoài ra có test CR-M3-01 và test citation PDF.

## Lệnh đã chạy và kết quả

Thư mục làm việc: `appota-kb`.

```powershell
$env:PYTHONUTF8 = "1"
..\.venv\Scripts\python.exe -m unittest tests.test_mission3 tests.test_hardening
```

Kết quả thực tế: `Ran 26 tests ... OK`.

```powershell
..\.venv\Scripts\python.exe tests\run_tests.py --offline
```

Kết quả thực tế: **12 tình huống, 12 đạt, 0 chưa đạt**. Báo cáo chi tiết do runner tạo tại `results/test_results_offline.md` và `results/test_results_offline.json`.

## Các test cải tiến tiêu biểu

| Loại | Test | Input và tài liệu | Kỳ vọng / điều kiện PASS | Kết quả |
| --- | --- | --- | --- | --- |
| Change Request CR-M3-01 | `test_change_request_cr01_unknown_effective_date_fails_closed` | User An; tài liệu OT Marketing có `effective_date=None`; hỏi tại ngày 2026-10-22 | Tài liệu bị loại với trạng thái ngày hiệu lực chưa xác định, không được dùng làm căn cứ | PASS |
| Edge case | `test_edge_expiry_date_is_valid_through_end_of_calendar_day` | User An; tài liệu hết hạn 2026-10-22; kiểm tra ngày 22 và 23 | Ngày hết hạn vẫn được tính hiệu lực trong ngày 22; bị loại từ ngày 23 | PASS |
| Hết hạn giả lập | `test_mock_active_policy_with_past_expiry_is_rejected` | User An hỏi tài liệu demo active hết hạn 2026-06-30 tại ngày 2026-10-22 | Tài liệu bị từ chối dù `status` còn active | PASS |
| Regression Mission 2 | `test_regression_mission2_user_scope_still_hides_company_b_policy` | Bình thuộc Công ty C hỏi quy định nghỉ phép; nguồn gồm chính sách Tập đoàn và Công ty B | Có thể nhận nguồn Tập đoàn; không được truy xuất nguồn Công ty B | PASS |
| Citation PDF | `test_pdf_citation_uses_extracted_page_number` | User An hỏi thời hạn thanh toán chi phí công tác; PDF giả lập và sidecar metadata | Citation trỏ `chi_phi_cong_tac_demo.pdf`, trang 1, mục đúng và trích đoạn có “7 ngày làm việc” | PASS |
| Schema metadata | `test_all_mock_documents_expose_the_complete_metadata_schema` | Toàn bộ 12 Markdown và 1 PDF giả lập | Mỗi tài liệu có đủ khóa định danh, version, quyền, hiệu lực, tổ chức và citation; `expiry_date` được khai báo | PASS |

CR-M3-01 ánh xạ tiêu chí trong yêu cầu của người dùng rằng thiếu ngày hiệu lực phải được coi là chưa xác định và không suy đoán. Đây không phải Change Request bên ngoài được reviewer phê duyệt.

## Phạm vi và giới hạn

- Các test trên chạy offline; phần trả lời dùng fake LLM hoặc kiểm tra điều kiện bằng code. Không đánh giá chất lượng sinh câu trả lời của Gemini.
- Ngày hết hạn trong dữ liệu demo được đặt giả lập: chính sách thông thường hết hạn 2027-12-31, bản lưu trữ hết hạn 2024-12-31, và `EXPIRED-DEMO-v1` hết hạn 2026-06-30. Các ngày này chỉ phục vụ kiểm thử.
- PDF demo hiện là PDF một trang. Test xác nhận số trang được trích là trang 1; chưa kiểm thử PDF nhiều trang.
- pypdf có in cảnh báo CMap của font nhúng trong PDF demo, nhưng vẫn trích xuất đúng văn bản tiếng Việt và số trang; test citation PDF đã đạt.
