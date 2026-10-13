"""Đọc tài liệu .md có front-matter và kiểm tra metadata.

File thiếu/sai metadata sẽ KHÔNG được nạp, và lỗi được trả về để báo cáo.
Đây là cách kiểm soát rủi ro "metadata sai dẫn tới trả lời sai".
"""
import glob
import os
from datetime import date

import yaml

REQUIRED = ["doc_id", "title", "topic", "scope", "owner_unit",
            "access_level", "status", "effective_date"]
VALID_SCOPES = ("group", "company", "dept", "team")
VALID_STATUS = ("active", "archived")


def parse_file(path):
    """Trả về dict gồm metadata + 'text' + 'path'. Ném ValueError nếu sai."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    parts = raw.split("---", 2)
    if len(parts) < 3 or parts[0].strip():
        raise ValueError("thiếu khối front-matter ở đầu file")
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        raise ValueError(f"front-matter không đọc được: {e}")
    if not isinstance(meta, dict):
        raise ValueError("front-matter rỗng hoặc sai định dạng")

    missing = [k for k in REQUIRED if k not in meta or meta[k] in (None, "")]
    if missing:
        raise ValueError("thiếu trường: " + ", ".join(missing))
    if meta["scope"] not in VALID_SCOPES:
        raise ValueError(f"scope không hợp lệ: {meta['scope']!r}")
    if meta["status"] not in VALID_STATUS:
        raise ValueError(f"status không hợp lệ: {meta['status']!r}")
    if not isinstance(meta["access_level"], int) or isinstance(meta["access_level"], bool):
        raise ValueError("access_level phải là số nguyên")
    # YAML tự đổi 2026-01-01 thành kiểu date; chuẩn hóa về chuỗi ISO để so sánh được
    eff = meta["effective_date"]
    if isinstance(eff, date):
        meta["effective_date"] = eff.isoformat()
    else:
        try:
            date.fromisoformat(str(eff))
        except ValueError:
            raise ValueError(f"effective_date không hợp lệ: {eff!r}")
        meta["effective_date"] = str(eff)

    meta["text"] = parts[2].strip()
    if not meta["text"]:
        raise ValueError("nội dung tài liệu rỗng")
    meta["path"] = path
    return meta


def load_docs(data_dir="data"):
    """Trả về (docs, errors). errors là list (tên_file, lý_do)."""
    docs, errors, seen = [], [], set()
    for path in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        name = os.path.basename(path)
        try:
            d = parse_file(path)
            if d["doc_id"] in seen:
                raise ValueError(f"trùng doc_id: {d['doc_id']}")
            seen.add(d["doc_id"])
            docs.append(d)
        except ValueError as e:
            errors.append((name, str(e)))
    return docs, errors
