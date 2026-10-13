"""Thử nhanh với Gemini thật. Ví dụ:
python ask_cli.py an "Quy định nghỉ phép của tôi như thế nào?"
"""
import json
import sys

from kb.answer import ask
from kb.loader import load_docs

uid, q = sys.argv[1], sys.argv[2]
users = {u["id"]: u for u in json.load(open("users.json", encoding="utf-8"))}
docs, _ = load_docs("data")
res = ask(q, users[uid], docs)
print(res["answer"])
print("\nNguồn:", [s["doc_id"] for s in res["sources"]])
print("Gọi LLM:", res["llm_called"], "| Cảnh báo:", res["warnings"])
