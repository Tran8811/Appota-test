"""Lọc quyền + phiên bản bằng code thuần (KHÔNG dùng AI).

Mọi tài liệu bị loại ở đây sẽ không bao giờ tới retriever hay LLM.
"""


def check_doc(doc, user):
    """Trả về None nếu được phép dùng, ngược lại trả về lý do bị loại."""
    if doc["owner_unit"] not in user["units"]:
        return "sai đơn vị"
    if doc["access_level"] > user["level"]:
        return "vượt cấp truy cập"
    if doc["status"] != "active":
        return "đã hết hiệu lực"
    return None


def split_allowed(docs, user):
    """Tách tài liệu thành (allowed, rejected).

    rejected là list (doc, lý_do) chỉ dùng cho chế độ debug/test.
    KHÔNG hiển thị rejected cho người dùng thường: lý do hoặc tiêu đề tài liệu
    có thể làm lộ việc tài liệu đó tồn tại.
    """
    allowed, rejected = [], []
    for d in docs:
        reason = check_doc(d, user)
        if reason is None:
            allowed.append(d)
        else:
            rejected.append((d, reason))
    return allowed, rejected
