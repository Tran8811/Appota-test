"""Chạy python check_key.py để kiểm tra API theo cấu hình hiện tại."""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from kb.llm_client import call_groq, get_llm_config

provider, key, model = get_llm_config()
if not key:
    variable = "GROQ_API_KEY" if provider == "groq" else "GEMINI_API_KEY"
    sys.exit(f"Chưa có {variable}. Hãy thêm key vào file .env.")

try:
    if provider == "groq":
        result = call_groq(
            "Bạn là chương trình kiểm tra kết nối. Chỉ trả lời đúng một từ: OK.",
            "Kết nối thành công chưa?",
            key,
            model,
        )
    else:
        from google.genai import types
        from kb.gemini_client import create_gemini_client

        client = create_gemini_client(key)
        response = client.models.generate_content(
            model=model,
            contents="Trả lời đúng một từ: OK",
            config=types.GenerateContentConfig(
                system_instruction="Bạn là chương trình kiểm tra kết nối."
            ),
        )
        result = (response.text or "").strip()
    print(f"Kết nối {provider.capitalize()} thành công. Model {model} trả lời: {result}")
except Exception as exc:
    message = str(exc)
    if provider == "groq" and ("401" in message or "invalid_api_key" in message.lower()):
        hint = "Key Groq không hợp lệ; hãy kiểm tra GROQ_API_KEY trong .env."
    elif provider == "groq" and "1010" in message:
        hint = "Groq/API gateway từ chối request ở lớp truy cập (403/1010); chưa đủ căn cứ để kết luận key sai. Kiểm tra VPN/proxy/firewall hoặc thử lại từ mạng khác."
    elif provider == "groq" and "403" in message:
        hint = "Groq từ chối quyền truy cập (403); kiểm tra trạng thái/quyền của project và key trong Groq Cloud."
    elif provider == "groq" and ("model_not_found" in message.lower() or " 404" in message):
        hint = "Model không khả dụng cho key/tài khoản Groq này; kiểm tra GROQ_MODEL."
    elif "CERTIFICATE_VERIFY_FAILED" in message:
        hint = "Lỗi chứng chỉ TLS; kiểm tra mạng/máy tính, không tắt xác minh SSL."
    elif "429" in message or "RESOURCE_EXHAUSTED" in message:
        hint = f"Đã gọi được API {provider}, nhưng quota/giới hạn tốc độ hiện không đủ."
    else:
        hint = f"Kiểm tra cấu hình {provider.upper()}_API_KEY và tên model {model}."
    sys.exit(f"Lỗi khi gọi {provider} ({model}): {message}\n{hint}")
