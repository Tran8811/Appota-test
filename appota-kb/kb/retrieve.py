"""Retrieval trên tập tài liệu ĐÃ LỌC QUYỀN + chọn bản ưu tiên + phát hiện mâu thuẫn.

Không dùng AI. Quy tắc ưu tiên xác định: cấp cụ thể hơn thắng
(team > dept > company > group); cùng cấp thì bản có effective_date mới hơn thắng;
cùng cấp và cùng ngày mà là hai tài liệu khác nhau -> CONFLICT (không tự chọn).
"""
import math
import re
from collections import Counter, defaultdict

SCOPE_RANK = {"group": 0, "company": 1, "dept": 2, "team": 3}


def _version_key(doc):
    value = str(doc.get("document_version") or "")
    if not value:
        match = re.search(r"(?:^|[-_])v(\d+(?:\.\d+)*)$", str(doc.get("doc_id", "")), re.I)
        value = match.group(1) if match else ""
    try:
        return tuple(int(part) for part in value.lstrip("vV").split("."))
    except ValueError:
        return ()

# Từ hỏi/từ nối quá phổ biến, không mang nghĩa tìm kiếm
STOPWORDS = {
    "của", "tôi", "mình", "em", "anh", "chị", "như", "thế", "nào", "là", "gì", "có",
    "không", "được", "bao", "nhiêu", "thì", "và", "cho", "với", "các", "những", "một",
    "quy", "định", "quy_định", "cần", "phải", "hãy", "xin", "ở", "về", "khi", "nếu",
    "mấy", "sao", "làm", "thế_nào",
}

MIN_COVERAGE = 0.6   # tài liệu phải chứa >= 60% từ khóa của câu hỏi (0.5 từng cho kết quả nhiễu)
MIN_SCORE = 0.5      # điểm BM25 tối thiểu
TOPIC_SCORE_RATIO = 0.5  # chỉ giữ chủ đề có điểm >= 50% điểm cao nhất
VAGUE_TERMS = {"mức", "phạt", "quy định", "chính sách"}


def tokenize(text):
    toks = re.findall(r"\w+", text.lower())
    return toks


def query_terms(question):
    # Bảng đồng nghĩa Việt/Anh nhỏ, khai báo tường minh cho thuật ngữ trong kho tri thức.
    normalized = question.lower()
    for phrase in ("tăng ca", "làm thêm giờ", "làm ngoài giờ", "overtime"):
        normalized = re.sub(rf"\b{re.escape(phrase)}\b", " ot ", normalized)
    return [t for t in tokenize(normalized) if t not in STOPWORDS]


def _doc_tokens(doc):
    return tokenize(doc["title"] + " " + doc["text"])


def bm25_scores(terms, docs, k1=1.5, b=0.75):
    """BM25 tự cài (idf luôn dương, ổn định với tập rất nhỏ)."""
    tokenized = [_doc_tokens(d) for d in docs]
    n = len(docs)
    if n == 0:
        return []
    avgdl = sum(len(t) for t in tokenized) / n
    df = Counter()
    for toks in tokenized:
        for term in set(toks):
            df[term] += 1
    scores = []
    for toks in tokenized:
        tf = Counter(toks)
        dl = len(toks)
        s = 0.0
        for term in terms:
            if tf[term] == 0:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            s += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * dl / avgdl))
        scores.append(s)
    return scores


def _coverage(terms, doc):
    if not terms:
        return 0.0
    toks = set(_doc_tokens(doc))
    return sum(1 for t in set(terms) if t in toks) / len(set(terms))


def resolve_topic(docs):
    """Ưu tiên phạm vi cụ thể, rồi đến quy định có hiệu lực mới hơn; giữ lại trường hợp hòa."""
    by_scope = defaultdict(list)
    for doc in docs:
        by_scope[doc["scope"]].append(doc)

    latest_by_scope = {}
    for scope, scoped_docs in by_scope.items():
        superseded = {d.get("supersedes_document_id", d.get("supersedes")) for d in scoped_docs}
        current = [d for d in scoped_docs if d.get("doc_id") not in superseded]
        # Ngày hiệu lực mới nhất là căn cứ thời gian mạnh nhất. Nếu cùng ngày,
        # ngày hết hạn xa hơn có thể xác định bản có thời hạn dài hơn. Nếu vẫn
        # hòa, chỉ chọn phiên bản cao nhất khi duy nhất; nếu không thì báo mơ hồ.
        dated = [d for d in current if d.get("effective_date")]
        if dated:
            newest_date = max(str(d["effective_date"]) for d in dated)
            selected = [d for d in dated if str(d["effective_date"]) == newest_date]
            if len(selected) > 1:
                expiry_key = lambda d: str(d.get("expiry_date") or "9999-12-31")
                farthest_expiry = max(expiry_key(d) for d in selected)
                expiry_selected = [d for d in selected if expiry_key(d) == farthest_expiry]
                if len(expiry_selected) == 1:
                    selected = expiry_selected
                else:
                    selected = expiry_selected
                    versions = [(_version_key(d), d) for d in selected]
                    highest = max((key for key, _ in versions), default=())
                    if highest and sum(key == highest for key, _ in versions) == 1:
                        selected = [d for key, d in versions if key == highest]
        else:
            versions = [(_version_key(d), d) for d in current]
            highest = max((key for key, _ in versions), default=())
            if highest and sum(key == highest for key, _ in versions) == 1:
                selected = [d for key, d in versions if key == highest]
            else:
                selected = current
        latest_by_scope[scope] = selected

    primary_scope = max(latest_by_scope, key=SCOPE_RANK.get)
    primary = latest_by_scope[primary_scope]
    lower_priority = [
        doc
        for scope, scoped_docs in latest_by_scope.items()
        if SCOPE_RANK[scope] < SCOPE_RANK[primary_scope]
        for doc in scoped_docs
    ]
    return primary, lower_priority, len(primary) > 1


def retrieve(question, allowed_docs):
    """Trả về dict:
    status: 'ok' | 'conflict' | 'no_answer' | 'clarify'
    topics: list {topic, primary, lower_priority, conflict}
    scores: {doc_id: điểm}
    reason: lý do khi no_answer/clarify
    """
    terms = query_terms(question)
    if not terms:
        return {"status": "no_answer", "topics": [], "scores": {},
                "reason": "câu hỏi quá chung chung, không có từ khóa để tìm"}
    if not set(terms) - VAGUE_TERMS:
        return {"status": "clarify", "topics": [], "scores": {},
                "reason": "câu hỏi chưa nêu rõ chủ đề cần tra cứu"}

    scores = bm25_scores(terms, allowed_docs)
    hits = []
    for d, s in zip(allowed_docs, scores):
        if s >= MIN_SCORE and _coverage(terms, d) >= MIN_COVERAGE:
            hits.append((d, s))
    score_map = {d["doc_id"]: round(s, 3) for d, s in zip(allowed_docs, scores)}
    if not hits:
        return {"status": "no_answer", "topics": [], "scores": score_map,
                "reason": "không có tài liệu phù hợp trong phạm vi được phép truy cập"}

    by_topic = defaultdict(list)
    for d, s in hits:
        by_topic[d["topic"]].append((d, s))
    topic_best = {t: max(s for _, s in items) for t, items in by_topic.items()}
    cutoff = max(topic_best.values()) * TOPIC_SCORE_RATIO

    topics, any_conflict = [], False
    for t, items in by_topic.items():
        if topic_best[t] < cutoff:
            continue
        topic_docs = [doc for doc in allowed_docs if doc["topic"] == t]
        primary, rest, conflict = resolve_topic(topic_docs)
        any_conflict = any_conflict or conflict
        topics.append({"topic": t, "primary": primary,
                       "lower_priority": rest, "conflict": conflict})
    return {"status": "conflict" if any_conflict else "ok",
            "topics": topics, "scores": score_map, "reason": ""}
