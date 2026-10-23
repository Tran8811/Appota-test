"""Cấu hình và gọi các nhà cung cấp mô hình ngôn ngữ."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def get_llm_config():
    """Trả về (provider, key, model); nhận diện key Groq bị dán nhầm vào ô Gemini."""
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if provider not in {"groq", "gemini"}:
        if groq_key or gemini_key.startswith("gsk_"):
            provider = "groq"
        else:
            provider = "gemini"

    key = groq_key if provider == "groq" else gemini_key
    # Tương thích khi key Groq hiện vẫn đang nằm trong GEMINI_API_KEY của .env.
    if provider == "groq" and not key and gemini_key.startswith("gsk_"):
        key = gemini_key

    default_model = "llama-3.3-70b-versatile" if provider == "groq" else "gemini-3.8-flash"
    model = os.getenv("GROQ_MODEL" if provider == "groq" else "GEMINI_MODEL", default_model).strip()
    return provider, key, model


def call_groq(system, prompt, api_key, model):
    """Gọi Groq qua API chat completions tương thích OpenAI."""
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }).encode("utf-8")
    request = Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Groq API trả HTTP {exc.code}: {details}") from exc
    except URLError as exc:
        raise RuntimeError(f"Không kết nối được Groq API: {exc.reason}") from exc

    try:
        return result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Groq API trả về phản hồi không đúng định dạng.") from exc
