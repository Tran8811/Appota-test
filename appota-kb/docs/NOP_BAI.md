# Checklist nộp bài và hướng dẫn deploy

Hạn nộp: **18:22 ngày 15/10**. Hãy xong trước 15h để còn thời gian xử lý sự cố.

## A. Trước khi push GitHub
- [ ] `git status` không có `.env` hay `.streamlit/secrets.toml`
- [ ] Tìm trong repo: `grep -r "AIza" .` không ra kết quả nào (không lộ key)
- [ ] `python -m unittest discover -s tests -t .` đạt
- [ ] Chạy `python tests/run_tests.py --live`, đọc kỹ `results/test_results_live.md`, sửa cột "Điều học được" nếu thấy khác thực tế, rồi cập nhật bảng kết quả trong README
- [ ] Đọc lại `docs/TRA_LOI_3_CAU.md`, sửa theo trải nghiệm thật của bạn

## B. GitHub
```bash
git init
git add .
git commit -m "Mission 2: MVP tri thức nội bộ Appota"
# tạo repo PUBLIC trên github.com rồi:
git remote add origin https://github.com/<ten-ban>/appota-kb.git
git branch -M main
git push -u origin main
```

## C. Deploy Streamlit Community Cloud (miễn phí)
1. Vào share.streamlit.io, đăng nhập bằng GitHub.
2. New app → chọn repo, nhánh `main`, file `app.py`.
3. Advanced settings → Secrets → dán:
   ```
   GEMINI_API_KEY = "key_của_bạn"
   ```
4. Deploy, chờ vài phút, mở link và chạy thử cả 6 câu hỏi mẫu.
5. Dán link vào đầu README.

Lưu ý bảo vệ key: link public có thể bị người lạ dùng hết quota. App đã giới hạn 30 câu hỏi mỗi phiên. Bạn nên đặt giới hạn chi tiêu/quota trong Google AI Studio, và xóa hoặc đổi key sau khi chấm xong.

Nếu không deploy được: ghi rõ lý do trong README (ví dụ không muốn public API key) và để hướng dẫn chạy local (đã có sẵn).

## D. Video
Làm theo `docs/VIDEO_SCRIPT.md`, tối đa 5 phút, upload YouTube (chế độ không công khai/unlisted) hoặc Google Drive bật chia sẻ, kiểm tra link mở được khi đăng xuất tài khoản.

## E. Bài nộp gửi HR/Appota
- [ ] Link GitHub (public, có README)
- [ ] Link bản chạy thử (hoặc lý do không deploy)
- [ ] Link video
- [ ] Bộ kiểm thử: `results/test_results_live.md` (và offline), nằm trong repo
- [ ] Trả lời 3 câu hỏi bắt buộc (`docs/TRA_LOI_3_CAU.md`, dán vào chỗ nộp theo yêu cầu)
