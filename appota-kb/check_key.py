"""Chạy: python check_key.py  -> kiểm tra API key Gemini có hoạt động không."""
import os
import sys

from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY", "").strip()
model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not key:
    sys.exit("Chưa có GEMINI_API_KEY. Hãy copy .env.example thành .env rồi dán key vào.")

from google import genai

try:
    client = genai.Client(api_key=key)
    r = client.models.generate_content(model=model, contents="Trả lời đúng một từ: OK")
    print(f"Key hoạt động. Model {model} trả lời:", r.text.strip())
except Exception as e:
    sys.exit(f"Lỗi khi gọi {model}: {e}\n"
             "Nếu lỗi 404/model not found: đổi GEMINI_MODEL trong .env sang model có trong Google AI Studio.")
