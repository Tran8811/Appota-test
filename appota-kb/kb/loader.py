"""Đọc tài liệu .md có front-matter và kiểm tra metadata.

File thiếu/sai metadata sẽ KHÔNG được nạp, và lỗi được trả về để báo cáo.
Đây là cách kiểm soát rủi ro "metadata sai dẫn tới trả lời sai".
"""
import glob
import os
import re
from datetime import date

import yaml

REQUIRED = ["doc_id", "title", "topic", "scope", "owner_unit",
            "access_level", "status"]
VALID_SCOPES = ("group", "company", "dept", "team")
VALID_STATUS = ("active", "archived")


def _normalize_doc(meta, path, text):
    if not isinstance(meta, dict):
        raise ValueError("front-matter rỗng hoặc sai định dạng")

    # Chấp nhận lược đồ tài liệu mới và vẫn giữ tên trường cũ cho mã đang dùng.
    if not meta.get("scope") and meta.get("org_level"):
        meta["scope"] = {1: "group", 2: "company", 3: "dept", 4: "team"}.get(meta["org_level"])
    meta.setdefault("title", meta.get("document_title"))
    meta.setdefault("document_title", meta.get("title"))
    meta.setdefault("document_id", meta.get("doc_id"))
    if "version" not in meta:
        meta["version"] = meta.get("document_version")
    if "supersedes" not in meta:
        meta["supersedes"] = meta.get("supersedes_document_id")

    missing = [k for k in REQUIRED if k not in meta or meta[k] in (None, "")]
    if missing:
        raise ValueError("thiếu trường: " + ", ".join(missing))
    if meta["scope"] not in VALID_SCOPES:
        raise ValueError(f"scope không hợp lệ: {meta['scope']!r}")
    expected_level = {"group": 1, "company": 2, "dept": 3, "team": 4}[meta["scope"]]
    if meta.get("org_level") is not None and meta["org_level"] != expected_level:
        raise ValueError(f"org_level không khớp scope: {meta['org_level']!r}")
    if meta["status"] not in VALID_STATUS:
        raise ValueError(f"status không hợp lệ: {meta['status']!r}")
    if not isinstance(meta["access_level"], int) or isinstance(meta["access_level"], bool):
        raise ValueError("access_level phải là số nguyên")
    positions = meta.get("allowed_positions")
    if positions is not None and (not isinstance(positions, list) or not all(isinstance(p, str) for p in positions)):
        raise ValueError("allowed_positions phải là danh sách chức vụ hoặc null")
    # YAML tự đổi 2026-01-01 thành kiểu date; chuẩn hóa về chuỗi ISO để so sánh được
    for field in ("effective_date", "expiry_date"):
        value = meta.get(field)
        if value in (None, ""):
            meta[field] = None
            continue
        if isinstance(value, date):
            meta[field] = value.isoformat()
        else:
            try:
                meta[field] = date.fromisoformat(str(value)).isoformat()
            except ValueError:
                meta[field] = None  # giữ tài liệu, nhưng kiểm soát hiệu lực sẽ từ chối an toàn
                meta["_invalid_" + field] = True

    meta.setdefault("document_id", meta["doc_id"])
    meta.setdefault("document_title", meta["title"])
    meta.setdefault("document_version", meta.get("version"))
    meta.setdefault("org_level", meta["scope"])
    meta.setdefault("corporation", meta.get("corporation"))
    meta.setdefault("company", meta.get("company", meta["owner_unit"] if meta["scope"] == "company" else None))
    meta.setdefault("department", meta.get("department", meta["owner_unit"] if meta["scope"] == "dept" else None))
    meta.setdefault("team", meta.get("team", meta["owner_unit"] if meta["scope"] == "team" else None))
    meta.setdefault("allowed_positions", meta.get("allowed_positions"))
    meta.setdefault("access_scope", meta.get("access_scope", meta["scope"]))
    meta.setdefault("supersedes_document_id", meta.get("supersedes"))
    meta.setdefault("source_file", os.path.abspath(path))
    meta.setdefault("page_number", meta.get("page"))
    meta.setdefault("section_title", meta.get("section"))

    # Tiêu đề là mốc trích dẫn, không phải nội dung trả lời. Bỏ ký hiệu
    # tiêu đề Markdown để đoạn trích hiển thị như văn bản thông thường.
    meta["text"] = text.strip()
    if not meta["text"]:
        raise ValueError("nội dung tài liệu rỗng")
    meta["path"] = path
    return meta


def parse_file(path):
    """Đọc phần metadata đầu tệp Markdown và trả về metadata đã chuẩn hóa."""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    parts = raw.split("---", 2)
    if len(parts) < 3 or parts[0].strip():
        raise ValueError("thiếu khối front-matter ở đầu file")
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        raise ValueError(f"front-matter không đọc được: {e}")
    # Tiêu đề là mốc trích dẫn, không phải đoạn nội dung. Giữ văn bản thường
    # để phục vụ tìm kiếm và giao diện.
    body = re.sub(r"(?m)^\s{0,3}#{1,6}\s+.*(?:\r?\n|$)", "", parts[2].strip()).strip()
    return _normalize_doc(meta, path, body)


def parse_pdf(path):
    """Đọc PDF kèm tệp metadata YAML và giữ nguyên số trang của PDF."""
    sidecar = path + ".yaml"
    if not os.path.isfile(sidecar):
        raise ValueError("PDF thiếu sidecar metadata (.pdf.yaml)")
    try:
        with open(sidecar, encoding="utf-8") as f:
            meta = yaml.safe_load(f)
        from pypdf import PdfReader
        reader = PdfReader(path)
    except Exception as e:
        raise ValueError(f"không đọc được PDF hoặc metadata: {e}")
    if len(reader.pages) != 1:
        raise ValueError("PDF demo hiện yêu cầu một trang để giữ citation trang chính xác")
    text = (reader.pages[0].extract_text() or "").replace("\u00a0", " ").replace("\u00ad", "-")
    meta = dict(meta or {})
    meta["page_number"] = 1
    return _normalize_doc(meta, path, text)


def load_docs(data_dir="data"):
    """Trả về (docs, errors). errors là list (tên_file, lý_do)."""
    docs, errors, seen = [], [], set()
    paths = glob.glob(os.path.join(data_dir, "*.md")) + glob.glob(os.path.join(data_dir, "*.pdf"))
    for path in sorted(paths):
        name = os.path.basename(path)
        try:
            d = parse_pdf(path) if path.lower().endswith(".pdf") else parse_file(path)
            if d["doc_id"] in seen:
                raise ValueError(f"trùng doc_id: {d['doc_id']}")
            seen.add(d["doc_id"])
            docs.append(d)
        except ValueError as e:
            errors.append((name, str(e)))
    return docs, errors
