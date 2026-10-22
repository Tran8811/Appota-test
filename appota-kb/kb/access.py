"""Kiểm tra quyền và thời điểm áp dụng trước khi tìm kiếm tài liệu."""
from datetime import date


def _date(value):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)) if value else None
    except (TypeError, ValueError):
        return None


def _org_allowed(doc, user):
    """Kiểm tra toàn bộ đường dẫn tổ chức và hỗ trợ hồ sơ cũ chỉ có danh sách đơn vị."""
    scope = doc.get("scope", doc.get("org_level"))
    owner = doc.get("owner_unit")
    units = set(user.get("units", []))
    field = {"group": "corporation", "company": "company", "dept": "department", "team": "team"}.get(scope)
    target = doc.get(field) if field else None
    structured = any(doc.get(k) for k in ("corporation", "company", "department", "team"))
    if not structured:
        return not owner or owner in units

    # Chính sách áp dụng cho các đơn vị con chỉ khi metadata cho phép;
    # các cấp tổ chức cha vẫn phải khớp.
    for key in ("corporation", "company", "department", "team"):
        expected = doc.get(key)
        actual = user.get(key)
        if expected and actual and actual != expected:
            return False
    if target:
        # Hồ sơ người dùng cũ có thể chỉ lưu danh sách đơn vị theo thứ tự,
        # chưa có các trường tổ chức chuẩn hóa. Chỉ chấp nhận đúng đơn vị đó.
        return user.get(field) == target or target in units or owner in units
    # Metadata cũ có thể thiếu trường của cấp được khai báo; dùng owner_unit
    # làm phương án dự phòng nghiêm ngặt, tránh cấp quyền từ đường dẫn thiếu.
    if owner and owner not in units:
        return False
    applies = doc.get("applies_to_descendants", doc.get("access_scope") in ("organization", "descendants"))
    if scope in ("group", "company", "dept") and not applies:
        child_key = {"group": "company", "company": "department", "dept": "team"}.get(scope)
        if child_key and user.get(child_key) and not owner:
            return False
    return True


def check_doc(doc, user, as_of=None):
    """Trả về None nếu được phép và tài liệu còn hiệu lực; nếu không, trả lý do nội bộ."""
    if not isinstance(user, dict) or not user.get("user_id", user.get("id")):
        return "thiếu user context đáng tin cậy"
    if not _org_allowed(doc, user):
        return "sai đơn vị"
    access_level = doc.get("access_level")
    if not isinstance(access_level, int) or isinstance(access_level, bool):
        return "thiếu metadata quyền truy cập"
    level = user.get("level")
    if not isinstance(level, int) or access_level > level:
        return "vượt cấp truy cập"
    positions = doc.get("allowed_positions")
    if positions is not None and (not isinstance(positions, list) or user.get("position") not in positions):
        return "chức vụ không được phép"
    if doc.get("status") != "active":
        return "đã hết hiệu lực"
    query_date = _date(as_of) or date.today()
    effective = _date(doc.get("effective_date"))
    if doc.get("_invalid_effective_date") or effective is None:
        return "chưa xác định ngày hiệu lực"
    if effective > query_date:
        return f"chưa đến ngày hiệu lực ({effective.isoformat()})"
    expiry = _date(doc.get("expiry_date"))
    if doc.get("_invalid_expiry_date"):
        return "chưa xác định ngày hết hạn"
    if expiry and expiry < query_date:
        return "đã hết hiệu lực"
    return None


def split_allowed(docs, user, as_of=None):
    allowed, rejected = [], []
    for doc in docs:
        reason = check_doc(doc, user, as_of)
        (allowed if reason is None else rejected).append(doc if reason is None else (doc, reason))
    return allowed, rejected
