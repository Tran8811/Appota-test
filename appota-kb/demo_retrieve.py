"""In kết quả retrieval cho từng người dùng. Chạy: python demo_retrieve.py "câu hỏi" """
import json
import sys

from kb.access import split_allowed
from kb.loader import load_docs
from kb.retrieve import retrieve

q = sys.argv[1] if len(sys.argv) > 1 else "Quy định nghỉ phép của tôi như thế nào?"
docs, _ = load_docs("data")
print("CÂU HỎI:", q)
for u in json.load(open("users.json", encoding="utf-8")):
    allowed, _ = split_allowed(docs, u)
    r = retrieve(q, allowed)
    print(f"\n[{u['id']}] status={r['status']} {r['reason']}")
    for t in r["topics"]:
        print("   topic:", t["topic"],
              "| DÙNG:", [d["doc_id"] for d in t["primary"]],
              "| CHUNG HƠN:", [d["doc_id"] for d in t["lower_priority"]],
              "| conflict" if t["conflict"] else "")
