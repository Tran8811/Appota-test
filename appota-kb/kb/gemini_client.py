"""Tạo Gemini client với chứng chỉ gốc đáng tin cậy từ hệ điều hành."""
import ssl

import truststore
from google import genai
from google.genai import types


def create_gemini_client(api_key):
    """Giữ xác minh TLS và dùng trust store của Windows/macOS/Linux."""
    ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    http_options = types.HttpOptions(client_args={"verify": ssl_context}, timeout=30_000)
    return genai.Client(api_key=api_key, http_options=http_options)
